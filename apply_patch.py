```python
# apply_patch.py – prosty patcher z logiem

import sys
import difflib
import pathlib
import shutil
import argparse
import textwrap
from itertools import zip_longest

def read_utf8(path: pathlib.Path) -> list[str]:
    """Odczytuje plik tekstowy w kodowaniu UTF-8 i zwraca jego linie jako listę."""
    return path.read_text(encoding="utf-8").splitlines(keepends=True)

def write_utf8(path: pathlib.Path, lines: list[str]) -> None:
    """Zapisuje listę linii do pliku w kodowaniu UTF-8."""
    path.write_text("".join(lines), encoding="utf-8")

def patch_file(original: pathlib.Path, hunks: list[list[str]]) -> tuple[int, int]:
    """Zwraca liczbę dodanych i usuniętych linii po zastosowaniu poprawek."""
    src = read_utf8(original)
    dst = []
    add = rem = 0
    idx = 0  # wskaźnik w src

    for hunk in hunks:
        # hunk[0] == "@@ -a,b +c,d @@"
        # następne linie: ' '|'-'|'+'...
        for line in hunk[1:]:
            if line.startswith(" "):
                dst.append(src[idx])
                idx += 1
            elif line.startswith("-"):
                rem += 1
                idx += 1
            elif line.startswith("+"):
                add += 1
                dst.append(line[1:])
    dst.extend(src[idx:])  # dodanie reszty pliku
    backup = original.with_suffix(".bak")
    shutil.copyfile(original, backup)
    write_utf8(original, dst)
    return add, rem

def parse_patch(lines: list[str]) -> dict[str, list[list[str]]]:
    """Parses the patch lines and returns a dictionary mapping filenames to their hunks."""
    files: dict[str, list[list[str]]] = {}
    current = None
    for ln in lines:
        if ln.startswith("diff --git"):
            current = ln.split()[-1][2:]  # "b/plik.py" → plik.py
            files.setdefault(current, [])
        elif ln.startswith("@@") and current:
            files[current].append([ln])
        elif current and files[current]:
            files[current][-1].append(ln)
    return files

def main(patch_path: str):
    """Główna funkcja, która przetwarza plik patcha."""
    patch_lines = read_utf8(pathlib.Path(patch_path))
    mapping = parse_patch(patch_lines)

    total_add = total_rem = 0
    for file, hunks in mapping.items():
        p = pathlib.Path(file)
        if not p.exists():
            print(f"[skip] {file} – brak pliku")
            continue
        add, rem = patch_file(p, hunks)
        total_add += add
        total_rem += rem
        print(f"[ok]   {file:25s}  +{add}  -{rem}")

    print(f"\nGotowe!  Plików: {len(mapping)}  Dodano: +{total_add}  Usunięto: -{total_rem}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("patch", help="plik .patch / .diff")
    args = ap.parse_args()
    main(args.patch)
```