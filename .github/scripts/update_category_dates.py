#!/usr/bin/env python3
import subprocess
import re
from datetime import datetime

DATA_YML_PATH = 'data.yml'

def get_changed_categories():
    """Use git diff to find which categories have changes"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', DATA_YML_PATH],
            capture_output=True,
            text=True,
            check=True
        )

        diff_output = result.stdout
        categories = ['movies', 'tv', 'anime', 'music', 'videogames', 'books']
        changed_categories = []

        current_category = None

        for line in diff_output.split('\n'):
            hunk_match = re.match(r'^@@ .+ @@ (\w+):', line)
            if hunk_match:
                context = hunk_match.group(1)
                if context in categories:
                    current_category = context

            if (line.startswith('+') or line.startswith('-')) and not line.startswith('+++') and not line.startswith('---'):
                if current_category and current_category not in changed_categories:
                    changed_categories.append(current_category)

        return changed_categories

    except subprocess.CalledProcessError:
        return []

def update_date_in_file(content, category, date_str):
    """Update or add the date for a category in category_dates section"""
    if 'category_dates:' not in content:
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('#') or line.strip() == '':
                insert_pos = i + 1
            else:
                break
        lines.insert(insert_pos, 'category_dates:')
        lines.insert(insert_pos + 1, f'  {category}: "{date_str}"')
        return '\n'.join(lines)

    pattern = rf'(category_dates:.*?\n)(.*?)(\n\S|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        dates_section = match.group(2)
        cat_pattern = rf'^  {category}:\s*".*?"'
        if re.search(cat_pattern, dates_section, re.MULTILINE):
            new_dates = re.sub(cat_pattern, f'  {category}: "{date_str}"', dates_section, flags=re.MULTILINE)
            return content[:match.start(2)] + new_dates + content[match.end(2):]
        else:
            new_dates = dates_section + f'\n  {category}: "{date_str}"'
            return content[:match.start(2)] + new_dates + content[match.end(2):]

    return content

def main():
    with open(DATA_YML_PATH, 'r', encoding='utf-8') as f:
        current_content = f.read()

    changed_categories = get_changed_categories()

    if not changed_categories:
        return

    today = datetime.now().strftime('%Y-%m-%d')
    updated_content = current_content

    for category in changed_categories:
        updated_content = update_date_in_file(updated_content, category, today)

    if updated_content != current_content:
        with open(DATA_YML_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)

if __name__ == '__main__':
    main()