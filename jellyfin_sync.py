import os
import re
import requests
from dotenv import load_dotenv
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

load_dotenv()

# =============
# CONFIGURATION
# =============
JELLYFIN_URL = os.getenv("JELLYFIN_URL", "")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY", "")
USER_ID = os.getenv("JELLYFIN_USER_ID", "")

DATA_YML_PATH = "data.yml"

# ======================
# INITIALIZE RUAMEL.YAML
# ======================
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.map_indent = 2
yaml.sequence_indent = 4
yaml.sequence_dash_offset = 2


# ================
# HELPER FUNCTIONS
# ================
def get_category_from_path(path):
    if not path: return "tv"
    path_lower = path.lower()
    if "anime" in path_lower:
        return "anime"
    elif "movies" in path_lower:
        return "movies"
    elif "tv shows" in path_lower or "tv" in path_lower:
        return "tv"
    return "tv"

def get_sortable_title(title):
    t = title.lower().strip()
    for article in ["the ", "a ", "an "]:
        if t.startswith(article):
            return t[len(article):]
    return t

# ======================
# JELLYFIN API FUNCTIONS
# ======================
def get_jellyfin_items():
    headers = {"X-Emby-Token": JELLYFIN_API_KEY, "Accept": "application/json"}
    url = f"{JELLYFIN_URL}/Users/{USER_ID}/Items"
    params = {
        "IncludeItemTypes": "Movie,Series", "Recursive": "true",
        "Fields": "ImageTags,Path,PremiereDate", "SortBy": "SortName", "SortOrder": "Ascending"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("Items", [])


# ==================
# DATA.YML FUNCTIONS
# ==================
def load_data_yml():
    if not os.path.exists(DATA_YML_PATH):
        return {"movies": [], "tv": [], "anime": []}

    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.load(f)

    if not data: data = {}
    for key in ["movies", "tv", "anime"]:
        if key not in data: data[key] = []
    return data


def save_data_yml(data):
    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)

    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

        # Adds blank lines between entries
        content = re.sub(r'(?<!\n)\n {2}- title:', '\n\n  - title:', content)

        # Ruamel is stupid and adheres strictly to YAML specification,
        # so this re-adds indentation in reviews/block scalars
        # purely for my own sanity with git diffs
        content = re.sub(r'^\n(?=(\n*)( {4,}))', r'\2\n', content, flags=re.MULTILINE)

    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f:
        f.write(content)


# ===========
# MAIN SCRIPT
# ===========
def main():
    if not all([JELLYFIN_URL, JELLYFIN_API_KEY, USER_ID]):
        print("Error: Missing Jellyfin credentials in .env file!")
        return

    print("Loading existing data.yml...")
    data = load_data_yml()

    existing_titles = {
        "movies": set(),
        "tv": set(),
        "anime": set()
    }

    for category in ["movies", "tv", "anime"]:
        for item in data[category]:
            existing_titles[category].add(item.get("title", "").lower().strip())

    print("Fetching items from Jellyfin...")
    items = get_jellyfin_items()

    title_counts = {"movies": {}, "tv": {}, "anime": {}}
    for item in items:
        cat = get_category_from_path(item.get("Path", ""))
        name = item.get("Name", "").lower().strip()
        title_counts[cat][name] = title_counts[cat].get(name, 0) + 1

    added_count = 0

    for item in items:
        jellyfin_title = item.get("Name")
        if not jellyfin_title:
            continue

        category = get_category_from_path(item.get("Path", ""))

        title_check = jellyfin_title.lower().strip()

        if title_counts[category].get(title_check, 0) > 1:
            premiere_date = item.get("PremiereDate")
            if premiere_date:
                year = premiere_date[:4]
                jellyfin_title = f"{jellyfin_title} ({year})"
                title_check = jellyfin_title.lower().strip()

        if title_check in existing_titles[category]:
            continue

        poster_url = "assets/images/no-poster.svg"

        new_entry = {
            "title": jellyfin_title,
            "rating": "☆☆☆☆☆ (0/10)",
            "review": LiteralScalarString("TBA\n"),
            "poster": poster_url,
            "tier": "unranked",
            "watched": ""
        }

        new_sortable = get_sortable_title(jellyfin_title)
        insert_index = len(data[category])

        for i, existing_item in enumerate(data[category]):
            existing_sortable = get_sortable_title(existing_item.get("title", ""))
            if existing_sortable > new_sortable:
                insert_index = i
                break

        data[category].insert(insert_index, new_entry)

        existing_titles[category].add(title_check)

        added_count += 1
        print(f"Added: {jellyfin_title} to {category}")

    print(f"\nSaving updated data.yml... Added {added_count} new items.")
    save_data_yml(data)


if __name__ == "__main__":
    main()