# Vendo Sync v12 — kolory wg statusu (overdue / normal / done)

| Status           | colorId | Wygląd w Google |
|------------------|---------|-----------------|
| **Overdue**      | 11      | Czerwony |
| **Normal**       | 5       | Żółty |
| **Done (#done)** | 8       | Szary |

* Priorytet **nie** wpływa już na kolor.  
* Bloki spełniające `#due` + FREEZE_DAYS (domyślnie 2) nie są przesuwane,
  ale jeśli nie mają koloru — dostają kolor statusu.  
* `#lateXd` ⟹ opis aktualizuje się przy każdym przeniesieniu lub utworzeniu.

Uruchom:
```powershell
python -m venv .venv; .venv\Scripts\Activate
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pytz
python main.py
```
* `#done` wydarzenia otrzymują od razu kolor szary (8).
