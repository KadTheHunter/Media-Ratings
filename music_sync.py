import os
import re
from pathlib import Path
from dotenv import load_dotenv
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString, LiteralScalarString

# ==================
# CONFIGURATION
# ==================
load_dotenv()
MUSIC_DIR = Path("/d/Music")
DATA_YML_PATH = 'data.yml'

# ==================
# COLORS & PRINTING
# ==================
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def cprint(text, color=""): print(f"{color}{text}{Colors.RESET}")

# ==================
# HELPER FUNCTIONS
# ==================
def has_audio_files(folder_path):
    """Checks if a folder contains at least one valid audio file."""
    extensions = ['*.mp3', '*.flac', '*.m4a', '*.ogg', '*.wav']
    return any(folder_path.glob(ext) for ext in extensions)

def load_data_yml():
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.map_indent = 2
    yaml.sequence_indent = 4
    yaml.sequence_dash_offset = 2
    if not os.path.exists(DATA_YML_PATH): return {"music": []}
    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f: data = yaml.load(f)
    if not data or "music" not in data: data = {"music": []}
    return data

def save_data_yml(data):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.map_indent = 2
    yaml.sequence_indent = 4
    yaml.sequence_dash_offset = 2
    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f: yaml.dump(data, f)
    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f: content = f.read()
    content = re.sub(r'(?<!\n)\n {2}- title:', '\n\n  - title:', content)
    content = re.sub(r'^\n(?=(\n*)( {4,}))', r'\2\n', content, flags=re.MULTILINE)
    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f: f.write(content)

# ==================
# MAIN SCRIPT
# ==================
def main():
    if not MUSIC_DIR.exists():
        cprint(f"Error: Music directory '{MUSIC_DIR}' not found!", Colors.RED)
        return

    cprint("Scanning local music library structure...", Colors.CYAN)
    data = load_data_yml()

    existing_entries = set()
    for item in data.get("music", []):
        artist = item.get("artist", "")
        title = item.get("title", "")
        existing_entries.add(f"{artist} - {title}")

    added_count = 0
    albums_found = 0

    for artist_dir in MUSIC_DIR.iterdir():
        if not artist_dir.is_dir() or artist_dir.name.startswith('.'): continue

        artist_name = artist_dir.name

        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir() or album_dir.name.startswith('.'): continue

            if not has_audio_files(album_dir): continue

            albums_found += 1
            album_name = album_dir.name

            combo_key = f"{artist_name} - {album_name}"
            if combo_key in existing_entries: continue

            new_entry = {
                "title": album_name,
                "artist": artist_name,
                "rating": DoubleQuotedScalarString("0"),
                "review": LiteralScalarString("TBA\n"),
                "poster": "assets/images/no-poster.svg",
                "tier": "unranked"
            }

            data["music"].append(new_entry)
            existing_entries.add(combo_key)
            added_count += 1

            cprint(f"Added: {Colors.CYAN}{album_name} {Colors.GREEN}by {artist_name}", Colors.GREEN)

    cprint(f"\nScan complete. Found {Colors.BOLD}{albums_found}{Colors.RESET} valid album folders.", Colors.CYAN)

    if added_count > 0:
        cprint(f"✓ Added {Colors.BOLD}{added_count}{Colors.RESET} new entries to data.yml. Saving...", Colors.GREEN)
        save_data_yml(data)
        cprint("✓ Music sync complete!", Colors.GREEN)
    else:
        cprint("✓ No new albums to add. Library is up to date.", Colors.GREEN)

if __name__ == '__main__':
    main()