"""Meaningful offline coverage of generation, API failures, persistence and resume."""
import csv
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock
import requests
from src.generator import GeneratorConfig as Config, generate, VALID_NAME
from src.checker import NameChecker, Result
from src.storage import Store


class Generators(unittest.TestCase):
    def test_short_presets_and_case_insensitive_uniqueness(self):
        for mode, charset in (("letters", "abcdefghijklmnopqrstuvwxyz"), ("characters", "abcdefghijklmnopqrstuvwxyz0123456789_"), ("numbers", "0123456789")):
            result = generate(Config(mode=mode, count=1000, seed="test"))
            self.assertEqual(len(result.names), 1000)
            self.assertEqual(len({n.lower() for n in result.names}), 1000)
            self.assertTrue(all(len(n) == 4 and set(n) <= set(charset) for n in result.names))

    def test_seed_and_huge_search_space(self):
        c = Config(mode="characters", min_length=16, max_length=16, seed="huge")
        self.assertEqual(generate(c).names, generate(c).names)
        self.assertEqual(generate(c).space, 37 ** 16)

    def test_pagination_covers_all_3_digit_names(self):
        c = Config(mode="numbers", min_length=3, max_length=3, count=500, order="sequential")
        first, second = generate(c), generate(replace(c, offset=500))
        self.assertEqual(first.names[0], "000")
        self.assertEqual(second.names[-1], "999")
        self.assertFalse(set(first.names) & set(second.names))

    def test_exhaustion_terminates(self):
        r = generate(Config(mode="custom", charset="a", count=20000))
        self.assertEqual(r.names, ["aaaa"])
        self.assertEqual(r.examined, 1)

    def test_dictionary_languages_and_categories(self):
        de = generate(Config(mode="words", language="de", categories=["tiere"], max_length=16, count=2000)).names
        self.assertIn("adler", de)
        self.assertNotIn("raven", de)
        en = generate(Config(mode="words", language="en", categories=["animals"], max_length=16, count=2000)).names
        self.assertIn("raven", en)
        self.assertNotIn("adler", en)

    def test_mask_and_invalid_tokens(self):
        r = generate(Config(mode="mask", mask="Zen{n}{n}", min_length=5, max_length=5, case="original", count=200))
        self.assertEqual(len(r.names), 100)
        self.assertTrue(all(n.startswith("Zen") and n[3:].isdigit() for n in r.names))
        for mask in ("{q}", "abc!", "", "{l"):
            with self.assertRaises(ValueError):
                generate(Config(mode="mask", mask=mask))

    def test_filters_apply_to_final_name(self):
        c = Config(mode="characters", min_length=6, max_length=6, prefix="Z", suffix="x", excludes="_9", max_repeat=1, no_ambiguous=True)
        r = generate(c)
        self.assertEqual(len(r.names), 250)
        self.assertTrue(all(n.startswith("Z") and n.endswith("x") and VALID_NAME.fullmatch(n) for n in r.names))
        self.assertTrue(all(not set("_901ilo").intersection(n.lower()) for n in r.names))
        self.assertTrue(all(not any(a == b for a, b in zip(n.lower(), n.lower()[1:])) for n in r.names))

    def test_list_normalization_leet_and_dedup(self):
        c = Config(mode="list", min_length=3, max_length=16, count=100, case="original", order="sequential")
        self.assertEqual(generate(c, ["Wolf", "wolf", "Bär", "not-valid!", "hi", "  Frost "]).names, ["Wolf", "Baer", "Frost"])
        self.assertEqual(generate(replace(c, leet=True), ["Blade"]).names, ["8l4d3"])

    def test_palindromes_and_repeat_with_normalized_prefix(self):
        r = generate(Config(mode="palindrome", min_length=3, max_length=6, count=1000))
        self.assertTrue(all(n == n[::-1] for n in r.names))
        r = generate(Config(mode="repeat", min_length=3, max_length=6, prefix="Ä", count=2000))
        self.assertTrue(all(n.startswith("Ae") and 3 <= len(n) <= 6 and len(set(n[2:])) == 1 for n in r.names))

    def test_invalid_config(self):
        for c in (Config(min_length=2), Config(count=20001), Config(offset=-1), Config(max_length=17), Config(mode="custom", charset="!"), Config(count="5")):
            with self.assertRaises(ValueError):
                generate(c)


def response(code, payload=None, headers=None):
    r = Mock(status_code=code, headers=headers or {})
    r.json.return_value = payload
    return r


class Api(unittest.TestCase):
    def client(self, *responses, token=""):
        session = Mock(headers={})
        session.get.side_effect = responses
        client = NameChecker(session=session, token=token)
        client.wait = Mock(return_value=True)
        return client, session

    def test_profile_and_unclaimed_are_separate_from_available(self):
        client, _ = self.client(response(200, {"name": "Notch", "id": "a" * 32}), response(404), response(204))
        self.assertEqual(client.check_one("Notch").status, "taken")
        self.assertEqual(client.check_one("TestingOne").status, "unclaimed")
        self.assertEqual(client.check_one("TestingTwo").status, "unclaimed")

    def test_malformed_200_and_wrong_name_are_errors(self):
        for payload in ({}, {"id": "a" * 32, "name": "Other"}, {"id": 4, "name": "Notch"}, [], None):
            client, _ = self.client(response(200, payload))
            self.assertEqual(client.check_one("Notch").status, "error")

    def test_auth_statuses_and_token_destination(self):
        for value, expected in (("AVAILABLE", "available"), ("DUPLICATE", "taken"), ("NOT_ALLOWED", "blocked"), ("WHAT", "error")):
            client, session = self.client(response(200, {"status": value}), token="secret")
            self.assertEqual(client.check_one("Testing").status, expected)
            self.assertTrue(session.get.call_args.args[0].startswith("https://api.minecraftservices.com/"))
            self.assertEqual(session.get.call_args.kwargs["headers"]["Authorization"], "Bearer secret")
            self.assertFalse(session.get.call_args.kwargs["allow_redirects"])

    def test_token_auth_failure_stops_batch(self):
        client, session = self.client(response(401), token="expired")
        results = []
        client.run(["One", "Two"], results.append)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "error")
        self.assertEqual(session.get.call_count, 1)

    def test_retry_after_and_each_name_gets_own_retry_budget(self):
        client, session = self.client(response(429, headers={"Retry-After": "45"}), response(503), response(404), response(503), response(404))
        self.assertEqual(client.check_one("FirstName").status, "unclaimed")
        self.assertEqual(client.check_one("SecondName").status, "unclaimed")
        self.assertIn(((45.0,),), [(c.args,) for c in client.wait.call_args_list])
        self.assertEqual(session.get.call_count, 5)

    def test_network_failures_are_never_discoveries(self):
        client, session = self.client(*[requests.Timeout()] * 4)
        self.assertEqual(client.check_one("Testing").status, "error")
        self.assertEqual(session.get.call_count, 4)

    def test_invalid_name_never_hits_network(self):
        client, session = self.client()
        self.assertEqual(client.check_one("ab").status, "invalid")
        session.get.assert_not_called()

    def test_stop_unblocks_paused_worker(self):
        client = NameChecker()
        client.pause()
        thread = threading.Thread(target=client.run, args=(["Testing"], lambda _: None))
        thread.start()
        client.stop()
        thread.join(1)
        self.assertFalse(thread.is_alive())


class Persistence(unittest.TestCase):
    def test_incremental_export_resume_and_reopen(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(temp)
            scan = store.create_scan(Config(), ["NameA", "NameB", "NameC", "NameD"])
            store.record(scan, Result("NameA", "unclaimed", "Public lookup", "now"))
            store.record(scan, Result("NameB", "available", "Token check", "now"))
            store.record(scan, Result("NameC", "error", "Timeout", "now"))
            self.assertIn("https://namemc.com/profile/NameA", (store.folder(scan) / "unbelegt.txt").read_text())
            self.assertEqual(store.pending(scan), ["NameC", "NameD"])
            store.toggle_favorite("NameA")
            store.close()
            store = Store(temp)
            self.assertEqual(store.favorites(), ["NameA"])
            store.toggle_favorite("namea")
            self.assertFalse(store.favorites())
            folder = store.export(scan)
            self.assertIn("NameB", (folder / "verfuegbar.txt").read_text())
            self.assertNotIn("NameA", (folder / "verfuegbar.txt").read_text())
            self.assertIn('href="https://namemc.com/profile/NameA"', (folder / "NameMC-Links.html").read_text())
            self.assertEqual(len(json.loads((folder / "ergebnisse.json").read_text())), 3)
            with (folder / "ergebnisse.csv").open(encoding="utf-8-sig", newline="") as f:
                self.assertEqual(len(list(csv.reader(f))), 4)
            store.close()


if __name__ == "__main__":
    unittest.main()
