#!/usr/bin/env python3
"""
Script to automatically fix common linting issues.
"""

import re
from pathlib import Path


def fix_file(file_path):
    """Fix common linting issues in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix whitespace issues
        content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)  # Remove trailing whitespace
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)  # Remove extra blank lines

        # Fix comparison to None
        content = re.sub(r"if (\w+) == None:", r"if \1 is None:", content)
        content = re.sub(r"if (\w+) != None:", r"if \1 is not None:", content)

        # Fix boolean comparisons
        content = re.sub(r"if (\w+) == True:", r"if \1:", content)
        content = re.sub(r"if (\w+) == False:", r"if not \1:", content)

        # Add newline at end if missing
        if not content.endswith("\n"):
            content += "\n"

        # Only write if content changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix linting issues."""
    project_root = Path(".")
    python_files = []

    # Collect Python files, excluding venv
    for file_path in project_root.rglob("*.py"):
        if "venv" not in str(file_path):
            python_files.append(file_path)

    fixed_count = 0

    for file_path in python_files:
        if fix_file(file_path):
            print(f"Fixed: {file_path}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} files.")


if __name__ == "__main__":
    main()
