import os
import re
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# ==================
# CONFIGURATION
# ==================
load_dotenv()
JELLYFIN_URL = os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
USER_ID = os.getenv("JELLYFIN_USER_ID")

POSTERS_DIR = 'assets/posters'

# ==================
# COLORS & PRINTING
# ==================
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ORANGE = '\033[38;5;208m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def cprint(text, color=""):
    print(f"{color}{text}{Colors.RESET}")

# ==================
# HELPER FUNCTIONS
# ==================
def sanitize_filename(title):
    """Converts a title into a safe filename."""
    safe = re.sub(r'[^\w\s-]', '', title).strip()
    safe = re.sub(r'\s+', '_', safe)
    return safe

def get_jellyfin_poster(title):
    """Searches Jellyfin for the title and returns the Primary Image URL."""
    headers = {
        'Authorization': f'MediaBrowser Token="{JELLYFIN_API_KEY}"',
        'Accept': 'application/json'
    }
    search_url = f"{JELLYFIN_URL}/Users/{USER_ID}/Items"
    params = {
        'SearchTerm': title,
        'IncludeItemTypes': 'Movie,Series,Book,MusicAlbum,Game',
        'Recursive': 'true',
        'Limit': 10
    }

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        items = response.json().get('Items', [])

        for item in items:
            if item['Name'].lower() == title.lower():
                item_id = item['Id']
                return f"{JELLYFIN_URL}/Items/{item_id}/Images/Primary?api_key={JELLYFIN_API_KEY}"
        return None
    except Exception as e:
        cprint(f"  [!] Error searching Jellyfin for '{title}': {e}", Colors.RED)
        return None

def download_image(url, filepath):
    """Downloads an image from a URL to a local filepath."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    except Exception as e:
        cprint(f"  [!] Failed to download image: {e}", Colors.RED)
        return False

# ==================
# MAIN SCRIPT
# ==================
def main():
    if not all([JELLYFIN_URL, JELLYFIN_API_KEY, USER_ID]):
        cprint("Error: Missing Jellyfin credentials in .env file!", Colors.RED)
        return

    cprint("Scanning data.yml for ranked items missing posters...", Colors.CYAN)

    from ruamel.yaml import YAML
    yaml = YAML()
    yaml.preserve_quotes = True

    try:
        with open('data.yml', 'r', encoding='utf-8') as f:
            data = yaml.load(f)
    except FileNotFoundError:
        cprint("Error: data.yml not found!", Colors.RED)
        return

    categories = ['movies', 'tv', 'anime', 'music', 'videogames', 'books']
    items_to_process = []

    for category in categories:
        if category not in data:
            continue

        for item in data[category]:
            tier = item.get('tier', 'unranked')
            poster = item.get('poster', '')

            if tier != 'unranked' and ('no-poster' in poster or not poster):
                items_to_process.append((category, item.get('title')))

    if not items_to_process:
        cprint("\n✓ All ranked items already have posters. Nothing to do.", Colors.GREEN)
        return

    cprint(f"\nFound {Colors.BOLD}{len(items_to_process)}{Colors.RESET} items to backfill.\n", Colors.YELLOW)

    downloaded_count = 0
    for category, title in items_to_process:
        cprint(f"Processing: {Colors.CYAN}{title} {Colors.GREEN}({category})", Colors.GREEN)

        img_url = get_jellyfin_poster(title)
        if not img_url:
            cprint(f"  [!] Not found in Jellyfin. Skipping.", Colors.YELLOW)
            continue

        safe_title = sanitize_filename(title)
        category_dir = Path(POSTERS_DIR) / category
        category_dir.mkdir(parents=True, exist_ok=True)

        raw_filepath = category_dir / f"{safe_title}.jpg"

        if download_image(img_url, raw_filepath):
            downloaded_count += 1
            cprint(f"  ✓ Downloaded raw image to {raw_filepath}", Colors.GREEN)
        else:
            cprint(f"  [!] Download failed. Skipping.", Colors.RED)

    if downloaded_count > 0:
        cprint(f"\n✓ Downloaded {Colors.BOLD}{downloaded_count}{Colors.RESET} raw posters.", Colors.GREEN)
        cprint("✓ Invoking process_posters.py to optimize images and update data.yml...", Colors.CYAN)

        subprocess.run(['python', 'process_posters.py'])

        cprint("✓ Poster backfill complete!", Colors.GREEN)
    else:
        cprint("\n✓ No new posters downloaded.", Colors.YELLOW)

if __name__ == '__main__':
    main()