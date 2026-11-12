"""Bounded, reproducible Minecraft Java name generation. No network or GUI."""
from dataclasses import dataclass, field
import math
import random
import re
import string
from .wordlists import WORDLISTS

VALID_NAME = re.compile(r"[A-Za-z0-9_]{3,16}\Z")
LETTERS = string.ascii_lowercase
DIGITS = string.digits
VOWELS = "aeiou"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"
CHARSETS = {"letters": LETTERS, "characters": LETTERS + DIGITS + "_",
            "numbers": DIGITS, "consonants": CONSONANTS, "custom": LETTERS}
TOKENS = {"l": LETTERS, "c": LETTERS + DIGITS + "_", "n": DIGITS,
          "v": VOWELS, "k": CONSONANTS}
MODES = {"letters": "Buchstaben · L", "characters": "Zeichen · C", "numbers": "Ziffern · N",
         "words": "Wörter · DE / EN", "compound": "Wortkombinationen", "pronounceable": "Aussprechbar",
         "mask": "Eigenes Muster", "palindrome": "Palindrome", "repeat": "Wiederholungen",
         "custom": "Eigener Zeichensatz", "list": "Eigene Namensliste"}


@dataclass
class GeneratorConfig:
    mode: str = "letters"
    min_length: int = 4
    max_length: int = 4
    count: int = 250
    language: str = "both"
    categories: list[str] = field(default_factory=list)
    charset: str = LETTERS + DIGITS
    mask: str = "{k}{v}{k}{v}"
    prefix: str = ""
    suffix: str = ""
    contains: str = ""
    excludes: str = ""
    blocked: str = ""
    case: str = "lower"
    leet: bool = False
    no_ambiguous: bool = False
    max_repeat: int = 0
    order: str = "random"
    offset: int = 0
    seed: str = ""


@dataclass
class Generation:
    names: list[str]
    space: int
    examined: int
    note: str


def normalize(text):
    for before, after in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"),
                          ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue")):
        text = text.replace(before, after)
    return text


def dictionary(language="both", categories=()):
    languages = ("en", "de") if language == "both" else (language,)
    return list(dict.fromkeys(normalize(w) for lang in languages
                             for cat, words in WORDLISTS[lang].items()
                             if not categories or cat in categories for w in words))


def decode(index, pools):
    out = []
    for pool in reversed(pools):
        index, position = divmod(index, len(pool))
        out.append(pool[position])
    return "".join(reversed(out))


def mask_pools(mask):
    pools = []
    pos = 0
    for token in re.finditer(r"\{([lcnvk])\}|([A-Za-z0-9_])", mask):
        if token.start() != pos:
            raise ValueError("Muster: Nur {l}, {c}, {n}, {v}, {k} und Minecraft-Zeichen verwenden.")
        pools.append(TOKENS[token[1]] if token[1] else token[2])
        pos = token.end()
    if pos != len(mask) or not pools or len(pools) > 16:
        raise ValueError("Das Muster muss 1–16 Positionen enthalten.")
    return pools


def generate(config: GeneratorConfig, custom_names=()):
    c = config
    for key in ("min_length", "max_length", "count", "offset", "max_repeat"):
        if type(getattr(c, key)) is not int:
            raise ValueError(f"{key} muss eine ganze Zahl sein.")
    for key in ("mode", "language", "charset", "mask", "prefix", "suffix", "contains", "excludes", "blocked", "case", "order", "seed"):
        if not isinstance(getattr(c, key), str):
            raise ValueError(f"{key} muss Text sein.")
    if not isinstance(c.categories, list) or not all(isinstance(cat, str) for cat in c.categories):
        raise ValueError("Kategorien müssen eine Liste aus Texten sein.")
    if c.mode not in MODES or c.language not in ("en", "de", "both"):
        raise ValueError("Unbekannter Generator oder Sprache.")
    if not 3 <= c.min_length <= c.max_length <= 16:
        raise ValueError("Die endgültige Namenslänge muss zwischen 3 und 16 liegen.")
    if not 1 <= c.count <= 20000 or c.offset < 0 or not 0 <= c.max_repeat <= 16:
        raise ValueError("Anzahl: 1–20.000, Startposition: ab 0, Wiederholung: 0–16.")
    if c.case not in ("lower", "title", "upper", "original") or c.order not in ("random", "sequential"):
        raise ValueError("Ungültige Schreibweise oder Reihenfolge.")
    rng = random.Random(c.seed or None)
    groups, lengths = [], []
    words = []
    if c.mode in ("words", "compound", "list"):
        if c.mode == "list":
            words = [normalize(w.strip()) for w in custom_names if w.strip()]
        elif c.mode == "words":
            words = dictionary(c.language, c.categories)
        else:
            base = dictionary(c.language, c.categories)
            # Two source dictionaries, lazy Cartesian indexing; never allocate millions of names.
            left = list(dict.fromkeys(WORDLISTS["semi_og_prefixes"] + base))
            right = list(dict.fromkeys(WORDLISTS["semi_og_suffixes"] + base))
            groups = [(left, right)]
        if not groups:
            words = list(dict.fromkeys(words))
            groups = [(words,)] if words else []
    elif c.mode == "mask":
        groups = [mask_pools(c.mask)]
    else:
        charset = c.charset if c.mode == "custom" else CHARSETS.get(c.mode, LETTERS)
        charset = "".join(dict.fromkeys(charset.lower()))
        if not charset or any(ch not in LETTERS + DIGITS + "_" for ch in charset):
            raise ValueError("Der Zeichensatz darf nur a–z, 0–9 und _ enthalten.")
        for total_length in range(c.min_length, c.max_length + 1):
            length = total_length - len(normalize(c.prefix)) - len(normalize(c.suffix))
            if length < 1:
                continue
            lengths.append(length)
            if c.mode == "pronounceable":
                groups.append([CONSONANTS if i % 2 == 0 else VOWELS for i in range(length)])
            elif c.mode == "palindrome":
                groups.append([LETTERS] * math.ceil(length / 2))
            elif c.mode == "repeat":
                groups.append([LETTERS + DIGITS])
            else:
                groups.append([charset] * length)
    sizes = [math.prod(len(pool) for pool in group) for group in groups]
    space = sum(sizes)
    if not space:
        return Generation([], 0, 0, "Keine Ausgangsnamen für diese Auswahl.")
    if c.order == "sequential":
        indexes = range(min(c.offset, space), min(space, c.offset + max(20000, c.count * 40)))
    else:
        # Modular permutation visits unique indices even for 37**16, without building a giant range.
        start = rng.randrange(space)
        step = rng.randrange(1, max(2, space))
        while math.gcd(step, space) != 1:
            step += 1
        indexes = ((start + i * step) % space for i in range(min(space, max(20000, c.count * 40))))
    names, seen, examined = [], set(), 0
    forbidden = set(c.excludes.lower())
    blocked = [w.strip().lower() for w in c.blocked.split(",") if w.strip()]
    for index in indexes:
        examined += 1
        group_index = 0
        while index >= sizes[group_index]:
            index -= sizes[group_index]
            group_index += 1
        name = decode(index, groups[group_index])
        if c.mode == "palindrome":
            length = lengths[group_index]
            name += name[-(2 if length % 2 else 1)::-1]
        elif c.mode == "repeat":
            name *= lengths[group_index]
        if c.leet:
            name = "".join(WORDLISTS["leet_map"].get(ch.lower(), ch) for ch in name)
        if c.case == "lower":
            name = name.lower()
        elif c.case == "upper":
            name = name.upper()
        elif c.case == "title":
            name = name[:1].upper() + name[1:].lower()
        name = normalize(c.prefix) + name + normalize(c.suffix)
        low = name.lower()
        if not VALID_NAME.fullmatch(name) or not c.min_length <= len(name) <= c.max_length:
            continue
        if low in seen or (c.contains and c.contains.lower() not in low):
            continue
        if forbidden.intersection(low) or any(w in low for w in blocked):
            continue
        if c.no_ambiguous and set("0o1il").intersection(low):
            continue
        if c.max_repeat and re.search(r"(.)\1{" + str(c.max_repeat) + r",}", low):
            continue
        seen.add(low)
        names.append(name)
        if len(names) == c.count:
            break
    note = "Ziel erreicht." if len(names) == c.count else "Weniger Treffer: Suchraum, Filter oder Suchbudget erreicht."
    return Generation(names, space, examined, note)


def describe(name):
    if name.isdigit():
        kind = f"{len(name)}N"
    elif name.isalpha() and name.isascii():
        kind = f"{len(name)}L"
    else:
        kind = f"{len(name)}C"
    tags = []
    if name.lower() == name.lower()[::-1]:
        tags.append("Palindrom")
    if len(set(name.lower())) == 1:
        tags.append("Repeat")
    return kind + (" · " + ", ".join(tags) if tags else "")
