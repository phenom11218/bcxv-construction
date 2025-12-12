"""
Fix Unicode Characters in Python Scripts
=========================================
Replaces Unicode characters (✓, ✗, ⊘) with ASCII equivalents
to prevent encoding errors when running scripts in batch files.
"""

import os
from pathlib import Path

# Files to fix
FILES_TO_FIX = [
    "update_active_postings.py",
    "database_migrations.py",
    "analyze_award_timing.py",
]

# Character replacements
REPLACEMENTS = {
    "✓": "[OK]",
    "✗": "[ERROR]",
    "⊘": "[SKIP]",
}

def fix_file(filepath: Path):
    """Replace Unicode characters in a file."""
    print(f"\nProcessing: {filepath.name}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = 0

    for unicode_char, ascii_replacement in REPLACEMENTS.items():
        count = content.count(unicode_char)
        if count > 0:
            content = content.replace(unicode_char, ascii_replacement)
            changes += count
            print(f"  Replaced {count} instances of '{unicode_char}' with '{ascii_replacement}'")

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Saved {changes} changes")
    else:
        print("  No changes needed")

    return changes

def main():
    """Main execution."""
    print("="*70)
    print("UNICODE CHARACTER REPLACEMENT")
    print("="*70)
    print("\nReplacing Unicode symbols with ASCII equivalents for batch compatibility")
    print()

    script_dir = Path(__file__).parent
    total_changes = 0

    for filename in FILES_TO_FIX:
        filepath = script_dir / filename
        if filepath.exists():
            changes = fix_file(filepath)
            total_changes += changes
        else:
            print(f"\n[WARNING] File not found: {filename}")

    print()
    print("="*70)
    print(f"Total changes: {total_changes}")
    print("="*70)

    if total_changes > 0:
        print("\n[SUCCESS] Files updated successfully!")
        print("\nYou can now run the weekly_scraping.bat without encoding errors.")
    else:
        print("\n[INFO] No changes were needed.")

if __name__ == "__main__":
    main()
