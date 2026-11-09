"""
⛏️ MC Rare Name Checker - Curated Word Lists
Sorgfältig kuratierte Wortlisten für seltene Minecraft-Usernames.
"""

WORDLISTS = {
    # ═══════════════════════════════════════════════════════════
    # ENGLISH WORDS - Categorized
    # ═══════════════════════════════════════════════════════════
    "en": {
        "animals": [
            # 3 letter
            "Bat", "Bee", "Cat", "Cod", "Cow", "Dog", "Eel", "Elk", "Emu",
            "Fox", "Hen", "Jay", "Koi", "Owl", "Ram", "Rat", "Yak",
            # 4 letter
            "Bear", "Buck", "Bull", "Colt", "Crab", "Crow", "Deer", "Dove",
            "Duck", "Fawn", "Frog", "Goat", "Hare", "Hawk", "Lion", "Lynx",
            "Mink", "Moth", "Mule", "Pike", "Puma", "Seal", "Slug", "Swan",
            "Toad", "Wasp", "Wolf", "Worm", "Wren",
            # 5 letter
            "Bison", "Cobra", "Crane", "Eagle", "Finch", "Gecko", "Goose",
            "Heron", "Horse", "Hyena", "Lemur", "Llama", "Moose", "Otter",
            "Panda", "Raven", "Shark", "Snail", "Snake", "Squid", "Stork",
            "Tiger", "Trout", "Viper", "Whale", "Zebra",
            # 6+ letter
            "Badger", "Condor", "Cougar", "Coyote", "Dragon", "Falcon",
            "Ferret", "Hornet", "Jaguar", "Kraken", "Lizard", "Mantis",
            "Marlin", "Osprey", "Parrot", "Python", "Raptor", "Salmon",
            "Scarab", "Spider", "Toucan", "Turtle", "Vulture", "Weasel",
            "Wolverine", "Panther", "Leopard", "Griffin", "Phoenix",
        ],

        "nature": [
            # 3 letter
            "Ash", "Bay", "Dew", "Elm", "Fir", "Fog", "Ice", "Ivy", "Oak",
            "Ore", "Sea", "Sky", "Sun",
            # 4 letter
            "Bark", "Cave", "Clay", "Coal", "Cove", "Dawn", "Dune", "Dusk",
            "Dust", "Fern", "Gale", "Hail", "Lake", "Lava", "Leaf", "Lime",
            "Mist", "Moon", "Moss", "Peak", "Pine", "Pond", "Rain", "Reef",
            "Root", "Rose", "Sand", "Seed", "Snow", "Star", "Stem", "Tide",
            "Twig", "Vale", "Vine", "Wave", "Wild", "Wind", "Wood",
            # 5 letter
            "Amber", "Bloom", "Briar", "Brook", "Cedar", "Cloud", "Coral",
            "Creek", "Ember", "Flame", "Flora", "Frost", "Grove", "Maple",
            "Marsh", "Petal", "River", "Shade", "Shore", "Smoke", "Solar",
            "Spark", "Steam", "Stone", "Storm", "Thorn", "Trail", "Vapor",
            # 6+ letter
            "Arctic", "Autumn", "Blizzard", "Breeze", "Canyon", "Crater",
            "Crystal", "Desert", "Forest", "Geyser", "Glacier", "Meadow",
            "Nebula", "Pebble", "Shadow", "Spring", "Summer", "Sunset",
            "Thunder", "Torrent", "Tundra", "Willow", "Winter",
        ],

        "weapons": [
            "Axe", "Bow",
            "Barb", "Bolt", "Claw", "Dart", "Edge", "Fang", "Grit", "Helm",
            "Hook", "Mace", "Pike", "Whip",
            "Arrow", "Blade", "Flail", "Knife", "Lance", "Sabre", "Shard",
            "Spear", "Staff", "Sting", "Sword",
            "Cannon", "Dagger", "Hammer", "Javelin", "Katana", "Musket",
            "Rapier", "Scythe", "Shield", "Sickle", "Stiletto", "Trident",
        ],

        "mythical": [
            "Imp", "Orc",
            "Bane", "Doom", "Fate", "Fury", "Myth", "Sage",
            "Angel", "Demon", "Drake", "Dwarf", "Fiend", "Ghost", "Ghoul",
            "Giant", "Gnome", "Golem", "Hydra", "Mummy", "Nymph", "Pixie",
            "Rogue", "Shade", "Siren", "Titan", "Troll", "Witch",
            "Banshee", "Djinn", "Goblin", "Kraken", "Lich", "Mimic",
            "Oracle", "Reaper", "Seraph", "Sphinx", "Spirit", "Undead",
            "Valkyrie", "Vampire", "Warden", "Wraith", "Wizard", "Zombie",
        ],

        "abstract": [
            # 3 letter
            "Ace", "Arc", "Art", "Awe", "Ego", "End", "Eon", "Era", "Hex",
            "Ion", "Joy", "Law", "Lie", "Nil", "Odd", "One", "Raw", "Sin",
            "Vex", "Vow", "War", "Wit", "Woe", "Zen", "Zap",
            # 4 letter
            "Aeon", "Apex", "Arch", "Aura", "Axis", "Calm", "Code", "Core",
            "Crux", "Cult", "Dare", "Echo", "Edge", "Envy", "Epic", "Fear",
            "Flux", "Glow", "Grim", "Haze", "Hope", "Hymn", "Icon", "Jinx",
            "Lore", "Luck", "Lust", "Maze", "Mind", "Muse", "Myth", "Neon",
            "Noir", "Nova", "Oath", "Omen", "Orb", "Pain", "Path", "Pact",
            "Pray", "Pulse", "Pure", "Rage", "Risk", "Ruin", "Rule", "Rune",
            "Rush", "Scar", "Sign", "Soul", "Tone", "True", "Vice", "Void",
            "Wake", "Will", "Wish", "Zeal", "Zero", "Zone",
            # 5+ letter
            "Abyss", "Alpha", "Bliss", "Chaos", "Chase", "Clash", "Crypt",
            "Curse", "Delta", "Dream", "Dread", "Faith", "Fable", "Flash",
            "Force", "Forge", "Frost", "Gamma", "Ghost", "Gloom", "Glory",
            "Grace", "Haven", "Honor", "Karma", "Logic", "Lunar", "Manor",
            "Mercy", "Nexus", "Night", "Noble", "Omega", "Order", "Peace",
            "Phase", "Power", "Pride", "Prime", "Prism", "Prowl", "Quest",
            "Reign", "Royal", "Sigma", "Skull", "Solar", "Synth", "Theta",
            "Tower", "Toxic", "Trace", "Ultra", "Unity", "Valor", "Vigor",
            "Wrath", "Zenith",
        ],

        "materials": [
            "Gem", "Tin",
            "Bone", "Gilt", "Gold", "Iron", "Jade", "Onyx", "Opal", "Ruby",
            "Rust", "Silk", "Wax",
            "Agate", "Alloy", "Brass", "Coral", "Ebony", "Flint", "Glass",
            "Ivory", "Pearl", "Quartz", "Steel", "Stone", "Topaz",
            "Cobalt", "Copper", "Chrome", "Crystal", "Diamond", "Marble",
            "Nickel", "Obsidian", "Pewter", "Platinum", "Silver", "Velvet",
            "Titanium",
        ],

        "colors": [
            "Ash", "Jet", "Red", "Tan",
            "Blue", "Cyan", "Gold", "Gray", "Grey", "Jade", "Lime", "Mint",
            "Navy", "Noir", "Pink", "Rose", "Rust", "Sage", "Teal", "Wine",
            "Amber", "Azure", "Black", "Blaze", "Blush", "Brown", "Coral",
            "Cream", "Ebony", "Green", "Ivory", "Lilac", "Mauve", "Mocha",
            "Olive", "Peach", "Pearl", "Plum", "Royal", "Sandy", "Slate",
            "Smoky", "Steel", "Taupe", "White",
            "Auburn", "Bronze", "Cherry", "Cobalt", "Copper", "Crimson",
            "Golden", "Indigo", "Maroon", "Orchid", "Pastel", "Rustic",
            "Scarlet", "Silver", "Sunset", "Violet",
        ],

        "adjectives": [
            "Big", "Dry", "Hot", "Icy", "Old", "Sly", "Shy",
            "Bold", "Calm", "Cold", "Cool", "Dark", "Dead", "Deep", "Evil",
            "Fair", "Fast", "Fell", "Grim", "Hard", "High", "Holy", "Iron",
            "Keen", "Kind", "Last", "Lone", "Long", "Lost", "Loud", "Mad",
            "Mean", "Mild", "Pale", "Poor", "Rare", "Real", "Rich", "Rude",
            "Safe", "Slim", "Slow", "Soft", "Tall", "Thin", "True", "Vast",
            "Warm", "Weak", "Wide", "Wild", "Wise",
            "Acute", "Agile", "Angry", "Blunt", "Brave", "Brief", "Brisk",
            "Cruel", "Dusty", "Elder", "Faint", "Fatal", "Feral", "Fiery",
            "Final", "First", "Fresh", "Grand", "Great", "Harsh", "Lethal",
            "Lucky", "Lunar", "Major", "Meek", "Mighty", "Minor", "Muted",
            "Noble", "Outer", "Proud", "Quick", "Quiet", "Rapid", "Rigid",
            "Rough", "Royal", "Rusty", "Sharp", "Sheer", "Sleek", "Stark",
            "Steep", "Stern", "Stiff", "Stone", "Swift", "Thick", "Tight",
            "Toxic", "Upper", "Vivid", "Young",
        ],

        "gaming": [
            "Bot", "Fps", "Gg", "Hp", "Kd", "Lol", "Mvp", "Npc", "Op",
            "Pvp", "Xp",
            "Buff", "Camp", "Flex", "Gank", "Loot", "Meta", "Nerf", "Noob",
            "Nuke", "Proc", "Push", "Rage", "Rank", "Rush", "Tank", "Wipe",
            "Carry", "Combo", "Craft", "Dodge", "Grind", "Guard", "Heist",
            "Level", "Mercy", "Pixel", "Purge", "Skill", "Smite", "Snipe",
            "Spawn", "Speed", "Squad", "Stash", "Stealth", "Swarm", "Swift",
        ],

        "og_elite": [
            # Ultra-short 2-3 letter OG names
            "Ax", "Bo", "Ed", "Go", "Hi", "If", "In", "It", "Jo", "No",
            "Ok", "On", "Op", "Or", "Ox", "So", "Up", "Us", "We",
            "Ace", "Age", "Aid", "Aim", "Air", "Ale", "All", "Amp", "Ant",
            "Ape", "Apt", "Arm", "Ask", "Ate", "Awe",
            "Bad", "Bag", "Ban", "Bar", "Bat", "Bay", "Bed", "Bet", "Big",
            "Bin", "Bit", "Bob", "Bog", "Box", "Boy", "Bud", "Bug", "Bun",
            "Bus", "Buy",
            "Cab", "Can", "Cap", "Car", "Cob", "Cog", "Cop", "Cow", "Cry",
            "Cub", "Cup", "Cut",
            "Dam", "Day", "Den", "Dew", "Did", "Dig", "Dim", "Dip", "Dog",
            "Dot", "Dry", "Dub", "Dud", "Due", "Dug", "Dye",
            "Ear", "Eat", "Egg", "Ego", "End", "Era", "Eve", "Eye",
            "Fan", "Far", "Fat", "Fax", "Fed", "Fee", "Few", "Fig", "Fin",
            "Fit", "Fix", "Fly", "Fog", "For", "Fox", "Fry", "Fun", "Fur",
            "Gap", "Gas", "Gem", "Get", "Gin", "God", "Got", "Gum", "Gun",
            "Gut", "Guy", "Gym",
            "Had", "Ham", "Has", "Hat", "Hay", "Her", "Hid", "Him", "Hip",
            "His", "Hit", "Hog", "Hop", "Hot", "How", "Hub", "Hue", "Hug",
            "Hum", "Hut",
            "Ice", "Ill", "Imp", "Ink", "Inn", "Ion", "Ire", "Ivy",
            "Jab", "Jag", "Jam", "Jar", "Jaw", "Jet", "Job", "Jog", "Joy",
            "Jug",
            "Keg", "Key", "Kid", "Kin", "Kit",
            "Lab", "Lad", "Lag", "Lap", "Law", "Lay", "Led", "Leg", "Lid",
            "Lie", "Lip", "Lit", "Log", "Lot", "Low",
            "Mad", "Man", "Map", "Mat", "Max", "May", "Men", "Met", "Mid",
            "Mix", "Mob", "Mod", "Mop", "Mud", "Mug",
            "Nab", "Nap", "Net", "New", "Nil", "Nip", "Nod", "Nor", "Not",
            "Now", "Nun", "Nut",
            "Oak", "Oar", "Oat", "Odd", "Ode", "Off", "Oil", "Old", "One",
            "Opt", "Orb", "Our", "Out", "Owe", "Own",
            "Pad", "Pal", "Pan", "Par", "Pat", "Paw", "Pay", "Pea", "Peg",
            "Pen", "Per", "Pet", "Pie", "Pig", "Pin", "Pit", "Pod", "Pop",
            "Pot", "Pro", "Pry", "Pub", "Pun", "Pup", "Put",
            "Rag", "Ram", "Ran", "Rap", "Rat", "Raw", "Ray", "Red", "Rib",
            "Rid", "Rig", "Rim", "Rip", "Rob", "Rod", "Rot", "Row", "Rub",
            "Rug", "Run", "Rut",
            "Sad", "Sag", "Sat", "Saw", "Say", "Set", "Sew", "She", "Shy",
            "Sin", "Sip", "Sir", "Sit", "Six", "Sky", "Sly", "Sob", "Sod",
            "Son", "Sop", "Sow", "Spy", "Sub", "Sum", "Sun",
            "Tab", "Tag", "Tan", "Tap", "Tar", "Tax", "Tea", "Ten", "The",
            "Thy", "Tie", "Tin", "Tip", "Toe", "Too", "Top", "Tow", "Toy",
            "Try", "Tub", "Tug", "Two",
            "Urn", "Use",
            "Van", "Vat", "Vet", "Via", "Vie", "Vim", "Vow",
            "Wag", "War", "Was", "Wax", "Way", "Web", "Wed", "Wet", "Who",
            "Why", "Wig", "Win", "Wit", "Woe", "Wok", "Won", "Woo", "Wow",
            "Yak", "Yam", "Yap", "Yaw", "Yes", "Yet", "Yew", "You",
            "Zap", "Zed", "Zen", "Zig", "Zip", "Zoo",
        ],
    },

    # ═══════════════════════════════════════════════════════════
    # GERMAN WORDS - Categorized (ASCII-safe, no umlauts)
    # ═══════════════════════════════════════════════════════════
    "de": {
        "tiere": [
            "Aal", "Bar", "Uhu",
            "Ente", "Fink", "Hase", "Igel", "Kalb", "Kitz", "Luchs",
            "Maus", "Rabe", "Rind", "Wels",
            "Adler", "Amsel", "Dachs", "Falke", "Fuchs", "Greif", "Hecht",
            "Keiler", "Krebs", "Marder", "Molch", "Otter", "Sperber",
            "Stier", "Taube", "Unke", "Wespe", "Wiesel", "Zeisig",
            "Biber", "Elster", "Forelle", "Habicht", "Hamster", "Kranich",
            "Panther", "Schlange", "Sperling",
        ],

        "natur": [
            "Eis", "See", "Tal",
            "Bach", "Baum", "Berg", "Fels", "Flut", "Glut", "Hang", "Keim",
            "Kies", "Klee", "Laub", "Moor", "Moos", "Quell", "Riff",
            "Sand", "Sumpf", "Tang", "Torf", "Wald", "Woge",
            "Birke", "Buche", "Eiche", "Erle", "Fichte", "Heide", "Kiefer",
            "Linde", "Steppe", "Weide", "Wiese",
            "Blitz", "Donner", "Fluss", "Frost", "Nebel", "Regen",
            "Schnee", "Sturm", "Welle", "Wolke",
        ],

        "waffen": [
            "Axt", "Beil",
            "Armbrust", "Dolch", "Haken", "Keule", "Klinge", "Lanze",
            "Morgenstern", "Pfeil", "Schild", "Schwert", "Sense", "Speer",
            "Spitze", "Stab", "Streitaxt",
        ],

        "mythisch": [
            "Elf", "Fee",
            "Albe", "Drache", "Geist", "Gnom", "Hexe", "Kobold", "Lich",
            "Nixe", "Ork", "Riese", "Sylphe", "Troll", "Vampir", "Wicht",
            "Zwerg", "Daemon", "Engel", "Golem", "Greif", "Hydra",
            "Phantom", "Schatten", "Sphinx", "Titan",
        ],

        "abstrakt": [
            "Eid", "Mut", "Rat", "Ruf", "Ruh", "Tod", "Zug",
            "Bann", "Ehre", "Elan", "Gier", "Gift", "Gnade", "Gram",
            "Hass", "Heil", "Huld", "Kern", "List", "Lohn", "Lust",
            "Macht", "Mark", "Neid", "Pein", "Pflicht", "Pracht", "Qual",
            "Rache", "Recht", "Ruhm", "Sieg", "Sinn", "Stolz", "Treue",
            "Trotz", "Tugend", "Wahn", "Wille", "Wucht", "Wut", "Ziel",
            "Zorn", "Zwist",
        ],

        "material": [
            "Erz", "Ton",
            "Blei", "Eisen", "Glas", "Gold", "Jade", "Kalk", "Kohle",
            "Lehm", "Rubin", "Saphir", "Silber", "Stahl", "Stein",
            "Diamant", "Granit", "Kristall", "Kupfer", "Marmor",
            "Obsidian", "Platin", "Titan", "Zinn",
        ],

        "krieg": [
            "Held", "Hort",
            "Feind", "Garde", "Jaeger", "Kaiser", "Kampf", "Knecht",
            "Konig", "Krieg", "Krieger", "Legion", "Orden", "Recke",
            "Ritter", "Soeldner", "Streiter", "Wachter", "Wappen",
        ],

        "farben": [
            "Rot", "Grau", "Blau", "Gold", "Gruen",
            "Braun", "Silber", "Weiss", "Schwarz", "Purpur",
            "Karmin", "Azur", "Ocker", "Umbra", "Indigo",
        ],

        "koerper": [
            "Arm", "Aug",
            "Bart", "Bein", "Blut", "Faust", "Haar", "Hand", "Haupt",
            "Herz", "Horn", "Kinn", "Klaue", "Knochen", "Kopf", "Narbe",
            "Pranke", "Stirn", "Tatze", "Zahn",
        ],
    },

    # ═══════════════════════════════════════════════════════════
    # SEMI-OG COMBO PARTS
    # ═══════════════════════════════════════════════════════════
    "semi_og_prefixes": [
        # English
        "Dark", "Dead", "Deep", "Cold", "Fire", "Ice", "Iron", "Last",
        "Lost", "Mad", "Neo", "Old", "Red", "Sky", "War", "Wild",
        "Black", "Blood", "Bone", "Doom", "Dread", "Dust", "Fell",
        "Ghost", "Grim", "Night", "Pale", "Shadow", "Silver", "Steel",
        "Stone", "Storm", "Swift", "True", "Void", "Wolf",
        # German
        "Alt", "Blut", "Dunkel", "Eis", "Feuer", "Grau", "Nacht",
        "Schwarz", "Stein", "Sturm", "Wild",
    ],

    "semi_og_suffixes": [
        # English
        "Axe", "Bane", "Bite", "Blade", "Born", "Burn", "Call", "Cast",
        "Claw", "Core", "Craft", "Crown", "Cry", "Edge", "Eye", "Fall",
        "Fang", "Fist", "Flame", "Forge", "Guard", "Hand", "Heart",
        "Hunt", "King", "Knight", "Lord", "Mage", "Moon", "Paw", "Rage",
        "Rune", "Shade", "Shard", "Skull", "Slayer", "Soul", "Star",
        "Storm", "Strike", "Sworn", "Thorn", "Watch", "Wing", "Wolf",
        # German
        "Beil", "Blitz", "Brand", "Faust", "Feuer", "Jaeger", "Klinge",
        "Kraft", "Krieg", "Macht", "Narbe", "Ritter", "Schwert", "Seele",
        "Sturm", "Wacht", "Zorn",
    ],

    # ═══════════════════════════════════════════════════════════
    # LEET SPEAK MAPPINGS
    # ═══════════════════════════════════════════════════════════
    "leet_map": {
        "a": "4", "e": "3", "i": "1", "o": "0",
        "s": "5", "t": "7", "b": "8", "g": "9",
    },

    # ═══════════════════════════════════════════════════════════
    # PATTERN NAMES - Special patterns that are rare/valuable
    # ═══════════════════════════════════════════════════════════
    "patterns": {
        "repeating": [
            # Double letters (2 chars)
            "aa", "bb", "cc", "dd", "ee", "ff", "gg", "hh", "ii", "jj",
            "kk", "ll", "mm", "nn", "oo", "pp", "qq", "rr", "ss", "tt",
            "uu", "vv", "ww", "xx", "yy", "zz",
            # Triple letters (3 chars)
            "aaa", "bbb", "ccc", "ddd", "eee", "fff", "ggg", "hhh",
            "iii", "jjj", "kkk", "lll", "mmm", "nnn", "ooo", "ppp",
            "qqq", "rrr", "sss", "ttt", "uuu", "vvv", "www", "xxx",
            "yyy", "zzz",
        ],
        "palindromes": [
            "aba", "aca", "ada", "afa", "aga", "aha", "aia", "aka", "ala",
            "ama", "ana", "apa", "ara", "asa", "ata", "ava", "awa", "axa",
            "aya", "aza",
            "bab", "bcb", "bdb", "beb", "bib", "bob", "bub",
            "cac", "cbc", "cdc", "cec", "cic", "coc", "cuc",
            "dad", "ded", "did", "dod", "dud",
            "eae", "ebe", "ece", "ede", "efe", "ege", "ehe", "eie", "eke",
            "ele", "eme", "ene", "epe", "ere", "ese", "ete", "eve", "ewe",
            "exe", "eye", "eze",
            "faf", "fef", "fif", "fof", "fuf",
            "gag", "gig", "gog", "gug",
            "kak", "kek", "kik", "kok", "kuk",
            "lal", "lel", "lil", "lol", "lul",
            "mam", "mem", "mim", "mom", "mum",
            "nan", "non", "nun",
            "pap", "pep", "pip", "pop", "pup",
            "rar", "rer", "ror",
            "sas", "ses", "sis", "sos", "sus",
            "tat", "tet", "tit", "tot", "tut",
            "vav", "vev", "viv", "vov",
            "waw", "wew", "wow",
            "xax", "xex", "xix", "xox", "xux",
            "yay", "yey",
            "zaz", "zez", "ziz", "zoz", "zuz",
        ],
        "sequential": [
            "abc", "bcd", "cde", "def", "efg", "fgh", "ghi", "hij",
            "ijk", "jkl", "klm", "lmn", "mno", "nop", "opq", "pqr",
            "qrs", "rst", "stu", "tuv", "uvw", "vwx", "wxy", "xyz",
        ],
    },
}
