# ZenMcChecker

> **ZenMcChecker** is a fast, modern Minecraft rare username generator and availability checker with a clean, borderless dark UI.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-1.0.1-brightgreen.svg)](https://github.com/Z3ntrix603/ZenMcChecker/releases/tag/v1.0.1)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://github.com/Z3ntrix603/ZenMcChecker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

- **Curated Wordlists:** Over 1,500+ carefully selected dictionary words across high-demand categories (Animals, Nature, Weapons, Mythical, Colors, Materials, Gaming).
- **OG & Rare Name Modes:** Supports 2-3 letter ultra-short OG names, palindromes, repeating character patterns, and compound Semi-OG names (e.g. `DarkBlade`, `FrostKing`).
- **Live Mojang API Verification:** Real-time checking directly against the official Mojang API with automatic exponential backoff to handle rate limits seamlessly.
- **Borderless Dark Slate UI:** Clean, minimalist UI without bulky borders or cluttered panels, designed for optimal clarity.
- **Dual Live Output:** Side-by-side real-time stream separating Available (Unclaimed) from Taken (Claimed) usernames.
- **Direct NameMC Integration:** 1-click shortcut to inspect any discovered name on NameMC.
- **Folder & Export Management:** Automated save on check completion with custom output directory selection, TXT exports, and CSV exports containing direct profile URLs.

---

## Generation Modes

| Mode | Description | Example Output |
|---|---|---|
| **English Dictionary** | High-demand thematic English words | `Blade`, `Raven`, `Storm`, `Frost` |
| **German Dictionary** | Pure ASCII German dictionary words | `Adler`, `Falke`, `Blitz`, `Klinge` |
| **Combined Words** | Joint dictionary spanning EN & DE words | `Shadow`, `Drache`, `Wolf`, `Titan` |
| **OG Names (3-Letter)** | Ultra-rare 2 to 3 letter real English words | `Ace`, `Zen`, `Fox`, `Bat`, `Sky` |
| **Semi-OG Combos** | Two-word compound names with high aesthetic value | `DarkBlade`, `FrostKing`, `StormAxe` |
| **Leet Speak** | Clean, recognizable 1337-style conversions | `8l4d3`, `570rm`, `F1r3` |
| **Patterns & Palindromes** | Palindromic (`aba`), repeating (`aaa`), and sequential (`abc`) | `aba`, `xyx`, `lol`, `mom` |
| **Brute Force** | Exhaustive search across custom charsets & lengths | `a-z`, `A-Z`, `0-9` combinations |
| **Custom Text File** | Load and check your own wordlist files | Any external `.txt` file |

---

## Quick Start

### Option 1: Standalone Executable (No Python Required)
1. Download `ZenMcChecker.exe` from the [Latest Release](https://github.com/Z3ntrix603/ZenMcChecker/releases/tag/v1.0.1).
2. Double-click to run.

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/Z3ntrix603/ZenMcChecker.git
cd ZenMcChecker

# Install required dependencies
pip install -r requirements.txt

# Launch application
python run.py
```
Or simply double-click `start.bat`.

---

## Building the Executable

To compile the standalone Windows executable yourself using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "ZenMcChecker" --collect-all customtkinter run.py
```
The compiled executable will be placed in the `dist/` directory.

---

## License

This project is licensed under the [MIT License](LICENSE).
