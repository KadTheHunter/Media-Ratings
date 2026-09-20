import os
import re
import requests
import subprocess
import mutagen
from pathlib import Path
from dotenv import load_dotenv
from ruamel.yaml import YAML

# ==================
# CONFIGURATION
# ==================
load_dotenv()
JELLYFIN_URL = os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
USER_ID = os.getenv("JELLYFIN_USER_ID")
MUSIC_DIR = Path("/d/Music")
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
    clean = re.sub(r'[.<>:"/\\|?*\-\u2013\u2014]', '', title).strip()
    return re.sub(r'\s+', '_', clean)


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

def extract_local_music_covers(data):
    """Scans local music folders for ranked items missing posters and extracts embedded covers."""
    if not MUSIC_DIR.exists(): return 0
    cprint("Scanning local music for ranked items missing posters...", Colors.CYAN)

    music_titles = [item.get('title', '') for item in data.get('music', [])]

    downloaded_count = 0
    for item in data.get('music', []):
        if item.get('tier') != 'unranked' and 'no-poster' in item.get('poster', ''):
            artist = item.get('artist', '')
            title = item.get('title', '')

            album_dir = MUSIC_DIR / artist / title
            if not album_dir.exists():
                cprint(f"  [!] Folder not found for: {artist} - {title}", Colors.YELLOW)
                continue

            audio_path = None
            for ext in ['*.mp3', '*.flac', '*.m4a', '*.ogg']:
                audio_path = next(album_dir.glob(ext), None)
                if audio_path: break

            if not audio_path:
                cprint(f"  [!] No audio files found in folder for: {title}", Colors.YELLOW)
                continue

            try:
                audio = mutagen.File(audio_path)
                image_data = None

                if audio_path.suffix == '.mp3' and 'APIC:' in audio.tags:
                    image_data = audio.tags['APIC:'].data
                elif audio_path.suffix == '.flac' and audio.pictures:
                    image_data = audio.pictures[0].data
                elif audio_path.suffix in ['.m4a', '.mp4'] and audio.tags and 'covr' in audio.tags:
                    image_data = audio.tags['covr'][0]

                if image_data:
                    is_unique = music_titles.count(title) == 1
                    safe_name = sanitize_filename(title) if is_unique else sanitize_filename(f"{title} {artist}")

                    category_dir = Path(POSTERS_DIR) / 'music'
                    category_dir.mkdir(parents=True, exist_ok=True)

                    raw_filepath = category_dir / f"{safe_name}.jpg"
                    with open(raw_filepath, 'wb') as f:
                        f.write(image_data)

                    downloaded_count += 1
                    cprint(f"  ✓ Extracted cover for: {Colors.CYAN}{title}", Colors.GREEN)
                else:
                    cprint(f"  [!] No embedded cover found in audio files for: {title}", Colors.YELLOW)
            except Exception as e:
                cprint(f"  [!] Failed to extract {title}: {e}", Colors.RED)

    return downloaded_count


# ==================
# MAIN SCRIPT
# ==================
def main():
    if not all([JELLYFIN_URL, JELLYFIN_API_KEY, USER_ID]):
        cprint("Error: Missing Jellyfin credentials in .env file!", Colors.RED)
        return

    cprint("Scanning data.yml for ranked items missing posters...", Colors.CYAN)
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

    jellyfin_downloads = 0
    for category, title in items_to_process:
        if category == 'music': continue

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
            jellyfin_downloads += 1
            cprint(f"  ✓ Downloaded raw image to {raw_filepath}", Colors.GREEN)
        else:
            cprint(f"  [!] Download failed. Skipping.", Colors.RED)

    music_downloads = extract_local_music_covers(data)
    total_downloads = jellyfin_downloads + music_downloads

    if total_downloads > 0:
        cprint(f"\n✓ Processed {Colors.BOLD}{total_downloads}{Colors.RESET} raw posters.", Colors.GREEN)
        cprint("✓ Invoking process_posters.py to optimize images and update data.yml...", Colors.CYAN)

        subprocess.run(['python', 'process_posters.py'])

        cprint("✓ Poster backfill complete!", Colors.GREEN)
    else:
        cprint("\n✓ No new posters downloaded.", Colors.YELLOW)

if __name__ == '__main__':
    main()