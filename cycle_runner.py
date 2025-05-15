#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cycle_runner.py – pełny cykl: pull → patch → run → log → patch → push
====================================================================
1. autocommit          –  „WIP auto-save”, jeśli cokolwiek jest nie-staged
2. git pull --rebase   –  synchronizacja z GitHubem
3. gpt_patch.py        –  pre-run: usuwa błędy typu IndentationError
4. main.py             –  uruchamia program, loguje stdout+stderr do logs/
5. commit log          –  git add -f <log>, commit  „log run …”
6. gpt_patch.py        –  post-run: analizuje świeży log, poprawia kod
7. git push            –  wypycha wszystkie commity

Skrypt stara się **nie przerywać** cyklu; jeśli dowolny krok zwróci
exit-code ≠ 0, wypisze ostrzeżenie i kontynuuje do końca.
"""
from __future__ import annotations
import subprocess, datetime, pathlib, sys, os, shlex

REPO  = pathlib.Path(__file__).resolve().parent
PY    = sys.executable
LOGS  = REPO / "logs"
LOGS.mkdir(exist_ok=True)

# ────────── helpers ──────────
def run(cmd: str | list[str], ok_codes={0}):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    rc = subprocess.run(cmd, cwd=REPO, text=True).returncode
    if rc not in ok_codes:
        print(f"⚠️  cmd {' '.join(cmd)} exit {rc}")
    return rc

def autocommit():
    if run(["git", "diff", "--quiet"], ok_codes={0,1}):     # 1 ⇒ są zmiany
        print("📝 WIP auto-save…")
        run(["git", "add", "-A"])
        run(["git", "commit", "-m", "WIP auto-save"])

def git_pull():
    print("🔄 git pull --rebase…")
    run(["git", "pull", "--rebase", "origin", "main"], ok_codes={0,1})

def patch(tag: str):
    print(f"🩹 gpt_patch.py ({tag})…")
    run([PY, "gpt_patch.py"], ok_codes={0})

def run_main() -> pathlib.Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log = LOGS / f"run_{stamp}.log"
    print(f"▶️  main.py → {log.relative_to(REPO)}")
    with log.open("w", encoding="utf-8", buffering=1) as f:
        p = subprocess.Popen([PY, "main.py"],
                             cwd=REPO,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             text=True)
        for line in p.stdout:
            print(line, end=""); f.write(line)
        p.wait()
        print(f"◀️  main.py exit {p.returncode}")
    return log

def add_log(path: pathlib.Path):
    run(["git", "add", "-f", str(path)])
    run(["git", "commit", "-m", f"log run {path.name}"])

def final_push():
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=REPO, text=True).strip()
    print("🚀 git push…")
    run(["git", "push", "origin", branch])

# ───────────── cycle ─────────────
def main():
    os.chdir(REPO)
    autocommit()
    git_pull()
    patch("pre-run")
    log_file = run_main()
    add_log(log_file)
    patch("post-run")
    final_push()

if __name__ == "__main__":
    main()
