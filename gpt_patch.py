#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPT Patch – log‑aware, indentation‑aware (model o3)
==================================================
• Skanuje zmodyfikowane pliki *.py **oraz** te wskazane w logach
  (ostatnie *.log w katalogu `logs/`).
• Jeśli w logu widzi `IndentationError` lub dowolny traceback,
  przekazuje wycinek do modelu **o3** i prosi o konkretną poprawkę.
• Plik zostaje nadpisany, commit‑owany i wypchnięty.
• Dodano opcjonalny DEBUG – gdy =True, wypisuje pełen prompt
  i odpowiedź modelu, co ułatwia diagnozę.
"""

import os, sys, subprocess, pathlib, time, re, textwrap, difflib
from typing import Dict, List
from dotenv import load_dotenv
import openai

# ───────────────────────────── KONFIG ──────────────────────────────
REPO_DIR       = pathlib.Path(__file__).resolve().parent
MAX_CODE_SIZE  = 30_000     # 30 kB
MAX_LOG_LINES  = 250        # z końca pliku
MODEL          = "o3"
TEMPERATURE    = 0.15
DEBUG          = False      # True → pokaże prompt + odpowiedź

SYSTEM_NOTE = (
    "You are a helpful linter assistant. You will receive the full content of a Python file, "
    "optionally followed by excerpts from recent log files that show errors. "
    "If the log shows an IndentationError, ALWAYS fix indentation at the indicated line(s). "
    "For any traceback, locate the root cause in the code and fix it while preserving public "
    "interfaces and functionality. Improve readability (PEP 8), but do NOT introduce breaking "
    "changes. Return ONLY the full corrected file, no explanations, no markdown fences."
)

# ────────────────────────── INIT API KEY ───────────────────────────
load_dotenv()
key = os.getenv("OPENAI_API_KEY")
if not key:
    sys.exit("Brak zmiennej OPENAI_API_KEY!")
openai.api_key = key

# ───────────────────────── GIT helpers ─────────────────────────────

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_DIR, text=True).strip()

# ─────────────────── znajdź pliki kodu do poprawy ──────────────────

def modified_py_files() -> List[pathlib.Path]:
    out = git("status", "-s")
    res: List[pathlib.Path] = []
    for line in out.splitlines():
        if line and line[0] in {"M", "A", "?"}:  # M‑odified, A‑dded, ?‑untracked
            path = line[3:]
            if path.endswith(".py"):
                p = REPO_DIR / path
                if p.exists() and p.stat().st_size <= MAX_CODE_SIZE:
                    res.append(p)
    return res

_LOG_RE = re.compile(r"File \"([^\"]+?\.py)\", line (\d+).*(Error|Exception)")


def error_sources_from_logs() -> Dict[pathlib.Path, str]:
    mapping: Dict[pathlib.Path, List[str]] = {}
    for log_path in (REPO_DIR / "logs").glob("*.log"):
        try:
            tail = log_path.read_text(errors="ignore").splitlines()[-MAX_LOG_LINES:]
        except Exception:
            continue
        snippet = "\n".join(tail)
        for m in _LOG_RE.finditer(snippet):
            rel = m.group(1).replace("\\", "/")
            src = (REPO_DIR / rel).resolve()
            if src.exists() and src.stat().st_size <= MAX_CODE_SIZE:
                mapping.setdefault(src, []).append(f"{log_path.name}: …{m.group(0)}")
    return {p: "\n".join(snips[-3:]) for p, snips in mapping.items()}

# ─────────────────────────── ASK GPT ───────────────────────────────

def ask_gpt(code: str, filename: str, error_snippet: str | None) -> str:
    user_msg = f"FILE: {filename}\n\n{code}"
    if error_snippet:
        user_msg += textwrap.dedent(
            f"""
            \n---\nLOG EXCERPT:\n{error_snippet}\n"""
        )
    wait = 15
    while True:
        try:
            resp = openai.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": SYSTEM_NOTE},
                    {"role": "user",   "content": user_msg},
                ],
            )
            answer = resp.choices[0].message.content
            if DEBUG:
                print("\n===== PROMPT =====\n", user_msg[:1500], "…")
                print("\n===== ANSWER =====\n", answer[:1500], "…")
            return answer.strip()
        except openai.RateLimitError:
            print(f"⏳ Rate‑limit – wait {wait}s…")
            time.sleep(wait)
            wait = min(wait + 5, 60)
        except Exception as e:
            print("❌ OpenAI error:", e)
            return code  # keep original

# ───────────────────── apply patch to single file ──────────────────

def apply_patch(path: pathlib.Path, snippet: str | None) -> bool:
    original = path.read_text(encoding="utf-8")
    fixed = ask_gpt(original, str(path.relative_to(REPO_DIR)), snippet)

    # normalise newlines for diff
    def norm(s: str) -> str:
        return s.replace("\r\n", "\n").rstrip() + "\n"

    if norm(fixed) != norm(original):
        path.write_text(fixed, encoding="utf-8")
        return True
    return False

# ───────────────────────────── MAIN ────────────────────────────────

def main():
    try:
        git("fetch", "--quiet")
    except Exception:
        pass

    modified = set(modified_py_files())
    errors = error_sources_from_logs()
    targets = modified.union(errors.keys())

    if not targets:
        print("Brak nowych zmian i brak nowych błędów w logach.")
        return

    any_change = False
    for file in sorted(targets):
        print(f"⚙️  GPT-fix {file.relative_to(REPO_DIR)} …")
        if apply_patch(file, errors.get(file)):
            any_change = True
            print("   ✓ zmodyfikowano")
        else:
            print("   ↺ bez zmian")

    if any_change:
        git("add", "-A")
        git("commit", "-m", "Patch from GPT (o3, indent-aware)")
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        git("push", "origin", branch)
        print("🚀 Wypchnięto poprawki.")
    else:
        print("Nie było realnych zmian — pomijam commit.")


if __name__ == "__main__":
    main()
