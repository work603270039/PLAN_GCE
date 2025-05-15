#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPT PATCH + LOG ANALYZER (model o3)
=================================
• Wykrywa zmodyfikowane pliki *.py **oraz** pliki wskazane w logach
  (np. *.log w katalogu repo), w których pojawiają się tracebacki.
• Do modelu o3 wysyła:
    – pełną treść pliku,
    – streszczony fragment logu wywołujący błąd (ostatnie 30 linii),
  prosząc o poprawki.
• Po otrzymaniu odpowiedzi zastępuje plik, commit‑uje i push‑uje.
"""

import os, sys, subprocess, pathlib, time, re, textwrap
from typing import Dict, List
from dotenv import load_dotenv
import openai

# ────────────────────────────────── KONFIG ────────────────────────────────────
REPO_DIR      = pathlib.Path(__file__).resolve().parent
MAX_CODE_SIZE = 30_000      # bajty (pojedynczy plik kodu)
MAX_LOG_LINES = 200         # ile ostatnich linii logu analizować
MODEL         = "o3"
TEMPERATURE   = 0.2

SYSTEM_NOTE = (
    "You are a helpful linter assistant. "
    "You will receive the full content of a Python file, optionally followed by error excerpts from recent log files. "
    "Fix the root cause of the error, improve code quality and readability, but keep public interfaces unchanged. "
    "Return ONLY the full corrected file content, with no explanations."
)

# ──────────────────────────────── INIT ───────────────────────────────────────
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    sys.exit("Brak zmiennej OPENAI_API_KEY!")

# ─────────────────────────────── POMOCNICZE ──────────────────────────────────

def git(*args: str) -> str:
    "Execute git command and return stdout (str)."
    return subprocess.check_output(["git", *args], cwd=REPO_DIR, text=True).strip()


def modified_py_files() -> List[pathlib.Path]:
    "Files changed in working tree (status M/A) and < MAX_CODE_SIZE."
    out = git("status", "-s")
    files = []
    for line in out.splitlines():
        path = line[3:]
        if path.endswith(".py"):
            p = REPO_DIR / path
            if p.exists() and p.stat().st_size <= MAX_CODE_SIZE:
                files.append(p)
    return files


_LOG_FILE_RE = re.compile(r"File \"(.+?\.py)\", line (\d+)")

def error_sources_from_logs() -> Dict[pathlib.Path, str]:
    """Scan *.log files -> map of file path → joined error snippets."""
    result: Dict[pathlib.Path, List[str]] = {}
    for log_path in REPO_DIR.glob("*.log"):
        try:
            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-MAX_LOG_LINES:]
        except Exception:
            continue
        snippet = "\n".join(lines)
        for m in _LOG_FILE_RE.finditer(snippet):
            rel = m.group(1).replace("\\", "/")
            cand = (REPO_DIR / rel).resolve()
            if cand.exists() and cand.stat().st_size <= MAX_CODE_SIZE:
                result.setdefault(cand, []).append(f"{log_path.name}: …{m.group(0)}")
    # join list to single string per file
    return {p: "\n".join(snips[-3:]) for p, snips in result.items()}  # max 3 hits/file


def ask_gpt(content: str, filename: str, error_snippet: str | None) -> str:
    """Send code + optional error snippet to OpenAI o3. Retry on 429."""
    wait = 20
    user_msg = f"Oto zawartość pliku {filename}:\n\n```python\n{content}\n```"
    if error_snippet:
        user_msg += textwrap.dedent(f"""

        ---
        Fragment ostatnich logów wskazujący błąd:

        ```
        {error_snippet}
        ```
        """)
    while True:
        try:
            rsp = openai.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": SYSTEM_NOTE},
                    {"role": "user",   "content": user_msg},
                ],
            )
            return rsp.choices[0].message.content.strip()
        except openai.RateLimitError:
            print(f"⏳ Rate-limit – czekam {wait}s…")
            time.sleep(wait)
            wait = min(wait + 5, 60)
        except Exception as exc:
            print(f"❌ OpenAI error for {filename}: {exc}")
            return content   # zwróć oryginał


def apply_patch(path: pathlib.Path, error_snippet: str | None) -> bool:
    original = path.read_text(encoding="utf-8")
    fixed = ask_gpt(original, str(path.relative_to(REPO_DIR)), error_snippet)
    if fixed and fixed != original:
        path.write_text(fixed, encoding="utf-8")
        return True
    return False

# ─────────────────────────────── MAIN ────────────────────────────────────────

def main():
    try:
        git("fetch", "--quiet")
    except Exception:
        pass

    modified = set(modified_py_files())
    errors = error_sources_from_logs()            # {Path: snippet}
    targets = modified.union(errors.keys())

    if not targets:
        print("Brak nowych zmian i brak nowych błędów w logach.")
        return

    changed_any = False
    for p in sorted(targets):
        rel = p.relative_to(REPO_DIR)
        print(f"⚙️  GPT-fix {rel} …")
        snippet = errors.get(p)
        if apply_patch(p, snippet):
            changed_any = True
            print("   ✓ zmodyfikowano")
        else:
            print("   ↺ bez zmian lub błąd")

    if changed_any:
        git("add", "-A")
        git("commit", "-m", "Patch from GPT (o3, log‑aware)")
        current_branch = git("rev-parse", "--abbrev-ref", "HEAD")
        git("push", "origin", current_branch)
        print("🚀 Wypchnięto poprawki.")
    else:
        print("Nie było realnych zmian – pomijam commit.")


if __name__ == "__main__":
    main()
