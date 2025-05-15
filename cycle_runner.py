#!/usr/bin/env python
"""
cycle_runner.py – resilient CI‑style loop
========================================
1. **Autocommit** wszystkich nie‑stage’owanych zmian (jeśli są) →
   „WIP auto‑save”. Zapobiega blokadzie przy `git pull`.
2. `git pull --rebase origin main`   – aktualizuje repo.
3. **gpt_patch.py** (log‑aware)      – naprawia kod przed run.
4. Uruchamia `main.py`, zapisując wynik do `logs/run_<stamp>.log`.
5. Dodaje log *(z ‑f, bo zwykle `logs/` jest w .gitignore)*, commit „log run”.
6. Wywołuje `gpt_patch.py` **ponownie** (bo log mógł wskazać nowe bugi).
7. Push.

Skrypt kończy się bez wyjątku nawet, gdy któryś krok zwróci błąd; zamiast
tego wypisuje ostrzeżenie i przechodzi dalej.
"""

import subprocess, datetime, pathlib, sys, os, shlex

REPO = pathlib.Path(__file__).resolve().parent
PY   = sys.executable
LOGS = REPO / "logs"
LOGS.mkdir(exist_ok=True)

# ───────────────────────── helpers ──────────────────────────

def run(cmd: str | list[str], ok_codes={0}):
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = cmd
    proc = subprocess.run(cmd_list, cwd=REPO, text=True)
    if proc.returncode not in ok_codes:
        print(f"⚠️  cmd failed ({proc.returncode}): {' '.join(cmd_list)}")
    return proc.returncode


def autocommit():
    if run(["git", "diff", "--quiet"], ok_codes={0,1}):  # 1 ⇒ zmiany
        print("📝 Committing unstaged changes…")
        run(["git", "add", "-A"])
        run(["git", "commit", "-m", "WIP auto‑save"])


def git_pull():
    run(["git", "pull", "--rebase", "origin", "main"], ok_codes={0,1})


def patch_code(tag="pre-run"):
    print(f"🩹 GPT patch ({tag})…")
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
        for line in proc.stdout:
            print(line, end="")
            f.write(line)
        proc.wait()
        print(f"◀️  main.py exited {proc.returncode}")
    return logfile


def add_log(path: pathlib.Path):
    run(["git", "add", "-f", str(path)])
    run(["git", "commit", "-m", f"log run {path.name}"])


def final_push():
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO, text=True).strip()
    run(["git", "push", "origin", branch])

# ─────────────────────────── cycle ──────────────────────────

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
