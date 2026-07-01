import os
import re
from dotenv import load_dotenv
from ruamel.yaml import YAML

load_dotenv()

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

DATA_YML_PATH = "data.yml"

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.map_indent = 2
yaml.sequence_indent = 4
yaml.sequence_dash_offset = 2

def get_sortable_title(title):
    t = title.lower().strip()
    for article in ["the ", "a ", "an "]:
        if t.startswith(article):
            return t[len(article):]
    return t

def save_data_yml(data):
    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)

    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        content = re.sub(r'(?<!\n)\n {2}- title:', '\n\n  - title:', content)
        content = re.sub(r'^\n(?=(\n*)( {4,}))', r'\2\n', content, flags=re.MULTILINE)

    with open(DATA_YML_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    if not os.path.exists(DATA_YML_PATH):
        cprint("Error: data.yml not found!", Colors.RED)
        return

    cprint("Loading data.yml...", Colors.CYAN)
    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.load(f)

    categories_to_sort = ["music", "videogames"]
    sorted_count = 0

    for category in categories_to_sort:
        if category not in data or not data[category]:
            cprint(f"  ⚠️  No entries found in [{Colors.MAGENTA}{category}{Colors.GREEN}]", Colors.ORANGE)
            continue

        original_order = [item.get("title", "") for item in data[category]]

        data[category].sort(key=lambda x: get_sortable_title(x.get("title", "")))

        new_order = [item.get("title", "") for item in data[category]]

        if original_order != new_order:
            sorted_count += len(data[category])
            cprint(f"✓ Sorted {Colors.CYAN}{len(data[category])} {Colors.GREEN}entries in [{Colors.MAGENTA}{category}{Colors.GREEN}]", Colors.GREEN)
        else:
            cprint(f"  ✓ [{Colors.MAGENTA}{category}{Colors.GREEN}] is already sorted", Colors.GREEN)

    if sorted_count > 0:
        save_data_yml(data)
        cprint(f"\n✓ Sorted {Colors.CYAN}{sorted_count} {Colors.GREEN}total entries. data.yml updated.", Colors.GREEN)
    else:
        cprint("\n✓ No changes needed. All categories are already sorted.", Colors.GREEN)

if __name__ == "__main__":
    main()