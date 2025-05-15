```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gpt_patch.py – automatyczne poprawki kodu przy użyciu OpenAI
Czyta lokalny diff, wysyła pliki do modelu, zastępuje zawartość,
commit-uje i push-uje do „main”.
"""

import os
import subprocess
import pathlib
import sys
from dotenv import load_dotenv
import openai

# ----- KONFIG -----
REPO_DIR = pathlib.Path(__file__).resolve().parent
MAX_SIZE = 30_000  # bajtów; większe pliki pomija
MODEL = "gpt-4o-mini"  # możesz zmienić na inny
TEMPERATURE = 0.2
SYSTEM_NOTE = (
    "Jesteś pomocnym asystentem-lintem. "
    "Otrzymasz plik Pythona i masz go poprawić: napraw błędy, "
    "ułatw czytanie, dodaj docstringi, ale zachowaj funkcjonalność. "
    "Zwróć **tylko** kompletną, gotową zawartość pliku."
)

# ----- INIT -----
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    sys.exit("Brak zmiennej OPENAI_API_KEY!")

def git(*args):
    """Wywołuje git i zwraca stdout jako str."""
    return subprocess.check_output(["git", *args], cwd=REPO_DIR, text=True).strip()

def changed_python_files():
    """Zwraca listę zmienionych/nowych plików .py wg git status."""
    out = git("status", "-s")
    files = []
    for line in out.splitlines():
        status, path = line[:2], line[3:]
        if path.endswith(".py") and os.path.getsize(path) <= MAX_SIZE:
            files.append(pathlib.Path(path))
    return files

def ask_gpt(content, filename):
    """Zwraca poprawioną treść pliku."""
    prompt = f"Oto zawartość pliku {filename}:\n\n```python\n{content}\n```"
    response = openai.ChatCompletion.create(
        model=MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": SYSTEM_NOTE},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()

def apply_patch(path):
    """Zastosowuje poprawki do pliku."""
    text = path.read_text(encoding="utf-8")
    fixed = ask_gpt(text, path.name)
    if text != fixed:
        path.write_text(fixed, encoding="utf-8")
        return True
    return False

def main():
    """Główna funkcja skryptu."""
    modified = changed_python_files()
    if not modified:
        print("Brak nowych zmian — nic do poprawy.")
        return

    changed_any = False
    for p in modified:
        print(f"⚙️  GPT-fix {p} …")
        try:
            if apply_patch(p):
                changed_any = True
                print("   ✓ zmodyfikowano")
            else:
                print("   ↺ bez zmian")
        except Exception as e:
            print(f"   ✗ błąd: {e}")

    if changed_any:
        git("add", "-A")
        git("commit", "-m", "Patch from GPT")
        git("push", "origin", "main")
        print("🚀 Push gotowy.")
    else:
        print("Nie było różnicy w treści — pomijam commit.")

if __name__ == "__main__":
    main()
```