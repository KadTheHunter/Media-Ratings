import os
import re
from pathlib import Path
from PIL import Image
from ruamel.yaml import YAML

class Colors:
    # Reset
    RESET = "\033[0m"

    # Text styles
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"
    STRIKETHROUGH = "\033[9m"

    # Bright foreground colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    ORANGE = "\033[38;5;208m"
    ORANGE_RED = "\033[38;5;202m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    BG_GRAY = "\033[100m"

    # Bright background colors
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"

def cprint(text, color=Colors.RESET):
    print(f"{color}{text}{Colors.RESET}")


# =============
# CONFIGURATION
# =============
POSTERS_DIR = Path("assets/posters")
DATA_YML_PATH = "data.yml"
PLACEHOLDER = "assets/images/no-poster.svg"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
CATEGORIES = ["movies", "tv", "anime", "music", "videogames"]


# ======================
# INITIALIZE RUAMEL.YAML
# ======================
yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.map_indent = 2
yaml.sequence_indent = 4
yaml.sequence_dash_offset = 2


# ==================
# DATA.YML FUNCTIONS
# ==================
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


# ================
# HELPER FUNCTIONS
# ================
def normalize_for_matching(text):
    # Removes: < > : " / \ | ? * and all dash variants (-, –, —)
    normalized = re.sub(r'[<>:"/\\|?*\-\u2013\u2014]', '', text)
    normalized = re.sub(r'[\s_]+', ' ', normalized)
    return normalized.strip().lower()


# ===========
# MAIN SCRIPT
# ===========
def main():
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)

    data = None
    if os.path.exists(DATA_YML_PATH):
        with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
            data = yaml.load(f)

    processed_count = 0
    linked_count = 0
    unmatched_files = []

    for category in CATEGORIES:
        category_dir = POSTERS_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        for file_path in category_dir.iterdir():
            if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue

            webp_path = file_path.with_suffix(".webp")

            try:
                img = Image.open(file_path)

                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                if category == 'music':
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                else:
                    if img.width > 400:
                        ratio = 400 / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((400, new_height), Image.Resampling.LANCZOS)

                img.save(webp_path, 'WEBP', quality=80, method=6)
                file_path.unlink()

                processed_count += 1
                cprint(f"✓ Converted: {Colors.MAGENTA}{file_path.name} {Colors.GREEN}-> {Colors.CYAN}{webp_path.name}", Colors.GREEN)

            except Exception as e:
                cprint(f"✗ Failed on {Colors.YELLOW}{file_path.name}{Colors.RED}: {Colors.ORANGE_RED}{e}", Colors.RED)

        if data:
            for file_path in category_dir.iterdir():
                if file_path.suffix.lower() != ".webp":
                    continue

                filename_normalized = normalize_for_matching(file_path.stem)
                webp_rel_path = str(file_path).replace("\\", "/")

                matched = False
                for entry in data.get(category, []):
                    entry_title = entry.get("title", "")
                    entry_normalized = normalize_for_matching(entry_title)

                    if entry_normalized == filename_normalized:
                        if entry.get("poster") != webp_rel_path:
                            entry["poster"] = webp_rel_path
                            linked_count += 1
                            cprint(f"  ↳ Linked to [{Colors.MAGENTA}{category}{Colors.GREEN}]: {Colors.CYAN}{Colors.BOLD}{entry_title}", Colors.GREEN)
                        matched = True
                        break

                if not matched:
                    unmatched_files.append((category, file_path.name))

    if data and linked_count > 0:
        save_data_yml(data)
        cprint(f"\nUpdated {Colors.CYAN}{linked_count} {Colors.GREEN}entries in data.yml.", Colors.GREEN)

    if unmatched_files:
        cprint(f"\n⚠️  Found {Colors.RED}{len(unmatched_files)} {Colors.YELLOW}poster(s) could not be linked to any entry:", Colors.YELLOW)
        for cat, filename in unmatched_files:
            cprint(f"   [{cat}] {Colors.ORANGE_RED}{Colors.BOLD}{filename}", Colors.RED)

    if processed_count == 0 and linked_count == 0 and not unmatched_files:
        cprint("No new images to process, no links to update.", Colors.YELLOW)
    else:
        if processed_count > 0:
            cprint(f"\nProcessed {Colors.CYAN}{processed_count} {Colors.GREEN}posters.", Colors.GREEN)
        if linked_count > 0:
            cprint(f"Linked {Colors.CYAN}{linked_count} {Colors.GREEN}posters.", Colors.GREEN)

if __name__ == "__main__":
    main()