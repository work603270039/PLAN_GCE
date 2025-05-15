#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cycle_runner.py – pełny cykl: pull → patch → run → log → patch → push
====================================================================
Uruchom jeden plik, a otrzymasz automatyczny „mini-CI” offline + GitHub.

**Kolejność:**
1. *autocommit* — jeżeli w katalogu są nie-zacommitowane zmiany,
   zapisuje je jako `WIP auto-save`, żeby `git pull --rebase` nie został
   zablokowany.
2. `git pull --rebase origin main` — podciąga najnowszy kod (bez merge-
   commitów).
3. **gpt_patch.py** (tag `pre-run`) — usuwa błędy typu IndentationError
   zanim program się uruchomi.
4. Uruchamia `main.py`; `stdout`+`stderr` zapisuje do
   `logs/run_<YYYYMMDD-HHMMSS>.log`, jednocześnie pokazując w konsoli.
5. Dodaje log do repo komendą `git add -f`, omijając `.gitignore`, i
   commit-uje z wiadomością `log run <plik>`.
6. **gpt_patch.py** (tag `post-run`) — analizuje świeży log i poprawia
   kod, jeśli pojawiły się nowe tracebacki.
7. `git push origin <branch>` — wypycha cały zestaw commitów.

Skrypt NA KOŃCU nie rzuca wyjątków — jeśli któryś krok zwróci nie-zero
`returncode`, wypisze ostrzeżenie i kontynuuje, tak aby push zawsze
spróbował się wykonać.
"""

from __future__ import annotations
import subprocess, datetime, pathlib, sys, os, shlex

# ───────────────────────── KONFIG ─────────────────────────
REPO = pathlib.Path(__file__).resolve().parent
PY   = sys.executable
LOGS = REPO / "logs"
LOGS.mkdir(exist_ok=True)

# ───────────────────────── helpers ─────────────────────────

def run(cmd: str | list[str], ok_codes={0}):
    """Uruchom polecenie; zwróć kod wyjścia; wypisz ostrzeżenie jeśli ≠ 0."""
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = cmd
    proc = subprocess.run(cmd_list, cwd=REPO, text=True)
    if proc.returncode not in ok_codes:
        print(f"⚠️  cmd {' '.join(cmd_list)} exit {proc.returncode}")
    return proc.returncode


def autocommit():
    # 0 – brak różnic, 1 – różnice, 128 – błąd repo
    if run(["git", "diff", "--quiet"], ok_codes={0,1}):
        print("📝 WIP auto-save…")
        run(["git", "add", "-A"])
        run(["git", "commit", "-m", "WIP auto-save"])


def git_pull():
    print("🔄 git pull --rebase…")
    run(["git", "pull", "--rebase", "origin", "main"], ok_codes={0,1})


def patch_code(tag: str):
    print(f"🩹 gpt_patch.py ({tag})…")
    run([PY, "gpt_patch.py"], ok_codes={0})


def run_main() -> pathlib.Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    logfile = LOGS / f"run_{stamp}.log"
    print(f"▶️  main.py → {logfile.relative_to(REPO)}")
    with logfile.open("w", encoding="utf-8", buffering=1) as f:
        proc = subprocess.Popen([PY, "main.py"], cwd=REPO,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True)
        for line in proc.stdout:   # mirror to console + file
            print(line, end="")
            f.write(line)
        proc.wait()
        print(f"◀️  main.py exit {proc.returncode}")
    return logfile


def add_log(path: pathlib.Path):
    run(["git", "add", "-f", str(path)])
    run(["git", "commit", "-m", f"log run {path.name}"])


def final_push():
    branch = subprocess.check_output([
        "git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO, text=True).strip()
    print("🚀 git push…")
    run(["git", "push", "origin", branch])

# ─────────────────────────── cycle ─────────────────────────

def main():
    os.chdir(REPO)
    autocommit()
    git_pull()
    patch_code("pre-run")
    log_file = run_main()
    add_log(log_file)
    patch_code("post-run")
    final_push()


if __name__ == "__main__":
    main()
