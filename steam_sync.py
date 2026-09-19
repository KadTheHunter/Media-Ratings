import os
import re
import requests
from dotenv import load_dotenv
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString, LiteralScalarString

# ==================
# CONFIGURATION
# ==================
load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")
DATA_YML_PATH = 'data.yml'

# ==================
# COLORS & PRINTING
# ==================
class Colors:
    RED = '\033[91m';
    GREEN = '\033[92m';
    YELLOW = '\033[93m'
    CYAN = '\033[96m';
    BOLD = '\033[1m';
    RESET = '\033[0m'

def cprint(text, color=Colors.RESET):
    print(f"{color}{text}{Colors.RESET}")

# ==================
# DATA.YML FUNCTIONS
# ==================
def load_data_yml():
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.map_indent = 2
    yaml.sequence_indent = 4
    yaml.sequence_dash_offset = 2

    if not os.path.exists(DATA_YML_PATH):
        return {"videogames": []}

    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.load(f)

    if not data: data = {}

    if "videogames" not in data: data["videogames"] = []
    return data

def save_data_yml(data):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.map_indent = 2
    yaml.sequence_indent = 4
    yaml.sequence_dash_offset = 2

    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)

    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

        content = re.sub(r'(?<!\n)\n {2}- title:', '\n\n  - title:', content)

        content = re.sub(r'^\n(?=(\n*)( {4,}))', r'\2\n', content, flags=re.MULTILINE)

    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================
# MAIN SCRIPT
# ==================
def main():
    if not all([STEAM_API_KEY, STEAM_ID]):
        cprint("Error: Missing STEAM_API_KEY or STEAM_ID in .env file!", Colors.RED)
        return

    cprint("Fetching owned games from Steam...", Colors.CYAN)
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": STEAM_ID,
        "format": "json",
        "include_appinfo": True,
        "include_played_free_games": True
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        steam_games = response.json().get("response", {}).get("games", [])
    except Exception as e:
        cprint(f"Failed to fetch from Steam: {e}", Colors.RED)
        return

    cprint(f"Found {len(steam_games)} games in Steam library.", Colors.CYAN)

    cprint("Loading existing data.yml...", Colors.CYAN)
    data = load_data_yml()

    existing_titles = set()
    for item in data.get("videogames", []):
        t = item.get("title", "").lower().strip()
        existing_titles.add(t)

    added_count = 0

    for game in steam_games:
        title = game.get("name")
        if not title: continue

        # if game.get("playtime_forever", 0) == 0: continue

        skip_pattern = re.compile(r'\b(?:demo|soundtrack|editor|server|sdk|mod kit|beta|soundpad)\b', re.IGNORECASE)
        if skip_pattern.search(title):
            cprint(f"Skipping: {title}", Colors.YELLOW)
            continue

        clean_title = title.replace('™', '').replace('®', '').replace('©', '')
        title_check = clean_title.lower().strip()

        if title_check in existing_titles:
            continue

        new_entry = {
            "title": clean_title,
            "rating": DoubleQuotedScalarString("0"),
            "review": LiteralScalarString("TBA\n"),
            "poster": "assets/images/no-poster.svg",
            "tier": "unranked",
            "tags": []
        }

        data["videogames"].append(new_entry)
        existing_titles.add(title_check)
        added_count += 1
        cprint(f"Added: {Colors.CYAN}{title}", Colors.GREEN)

    if added_count > 0:
        cprint(f"\n✓ Added {Colors.BOLD}{added_count}{Colors.RESET} new games. Saving...", Colors.GREEN)
        save_data_yml(data)
    else:
        cprint("\n✓ No new games to add. Library is up to date.", Colors.GREEN)

if __name__ == '__main__':
    main()