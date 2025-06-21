#!/usr/bin/env python3
"""
Script to format conftest.py while preserving the imports section.
This is needed because we want to keep all model imports for database table creation,
but Black would remove unused imports.
"""

import re
import subprocess  # nosec
import sys
from pathlib import Path


def format_conftest_py():
    """Format conftest.py while preserving imports."""
    conftest_path = Path("tests/conftest.py")

    if not conftest_path.exists():
        print("tests/conftest.py not found")
        return 1

    # Read the current content
    with open(conftest_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split content into imports and non-imports
    lines = content.split("\n")

    # Find the imports section (everything before the first non-import line)
    import_lines = []
    other_lines = []
    in_imports = True

    for line in lines:
        if in_imports:
            if (
                line.strip().startswith("import ")
                or line.strip().startswith("from ")
                or line.strip() == ""
                or line.strip().startswith("#")
            ):
                import_lines.append(line)
            else:
                in_imports = False
                other_lines.append(line)
        else:
            other_lines.append(line)

    # Format the non-imports section with Black
    other_content = "\n".join(other_lines)

    # Create a temporary file with just the non-imports content
    temp_file = Path("temp_conftest_content.py")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(other_content)

        # Format the temporary file with Black
        result = subprocess.run(  # nosec
            [sys.executable, "-m", "black", "--quiet", str(temp_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"Black formatting failed: {result.stderr}")
            return 1

        # Read the formatted content
        with open(temp_file, "r", encoding="utf-8") as f:
            formatted_other_content = f.read()

        # Combine imports and formatted content
        final_content = "\n".join(import_lines) + "\n" + formatted_other_content

        # Write back to conftest.py
        with open(conftest_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        print("Successfully formatted conftest.py while preserving imports")
        return 0

    finally:
        # Clean up temporary file
        if temp_file.exists():
            temp_file.unlink()


if __name__ == "__main__":
    sys.exit(format_conftest_py())
