"""Application integration test: hidden Tk window, no OS input and no network."""
from dataclasses import asdict
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from src.checker import NameChecker
from src.generator import GeneratorConfig
from src.main import ZenMcCheckerApp


class Application(unittest.TestCase):
    def test_generate_scan_favorites_and_history(self):
        with tempfile.TemporaryDirectory() as temp:
            app = ZenMcCheckerApp(data_dir=temp)
            app.withdraw()
            def wait_for(condition):
                deadline = time.monotonic() + 8
                while not condition() and time.monotonic() < deadline:
                    app.update()
                    time.sleep(.01)
                self.assertTrue(condition(), "Application worker did not finish")
            try:
                wait_for(lambda: bool(app.names) and not app.generating)
                app.custom_names = ["Notch", "ZenName"]
                app._apply_config(asdict(GeneratorConfig(mode="list", max_length=16, order="sequential")))
                app._generate()
                wait_for(lambda: not app.generating)
                self.assertEqual(app.names, ["notch", "zenname"])
                app.config_vars["prefix"].set("ChangedAfterGeneration")
                responses = [Mock(status_code=200, headers={}), Mock(status_code=404, headers={})]
                responses[0].json.return_value = {"name": "Notch", "id": "a" * 32}
                session = Mock(headers={})
                session.get.side_effect = responses
                checker = NameChecker(session=session)
                checker.wait = Mock(return_value=True)
                with patch("src.main.NameChecker", return_value=checker):
                    app._start()
                    wait_for(lambda: not app.busy)
                self.assertEqual(app.results["notch"].status, "taken")
                self.assertEqual(app.results["zenname"].status, "unclaimed")
                folder = app.store.folder(app.scan_id)
                self.assertIn("zenname", (folder / "unbelegt.txt").read_text())
                self.assertEqual((folder / "verfuegbar.txt").read_text(), "")
                self.assertEqual(app.store.pending(app.scan_id), [])
                app.table.selection_set("zenname")
                app._name_action("favorite")
                app._show("favorites")
                self.assertEqual(len(app.favorites_table.get_children()), 1)
                app._show("history")
                app.history_table.selection_set(app.scan_id)
                app._history_action("load")
                self.assertEqual(app.config_vars["prefix"].get(), "")
                self.assertEqual(len(app.results), 2)
            finally:
                app._finish_close()


if __name__ == "__main__":
    unittest.main()
