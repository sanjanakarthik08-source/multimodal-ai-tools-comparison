# CAPSTONE 57 Flask Project

## Structure
- `app.py`: Flask routes, SQLite database, scoring, task set and quiz
- `templates/`: HTML pages
- `static/style.css`: website styling
- `requirements.txt`: dependency list
- `capstone57.db`: created automatically when the app first runs

## Run in VS Code (Windows)
1. Install Python 3.10 or later.
2. Open this folder in VS Code.
3. In the terminal, run:
   ```powershell
   py -m venv .venv
   .venv\\Scripts\\Activate.ps1
   python -m pip install -r requirements.txt
   python app.py
   ```
   If PowerShell activation is blocked, run `.venv\\Scripts\\python.exe -m pip install -r requirements.txt` and `.venv\\Scripts\\python.exe app.py`.
4. Open `http://127.0.0.1:5000/`.

## Run in an online coding platform
Upload the files while preserving the `templates` and `static` folders. Install dependencies using `pip install -r requirements.txt` and run `python app.py`. Configure the platform to expose port 5000 if needed.

## Scoring
Each tested record has six criteria scored 0–5. Percentage = sum of scores / 30 × 100. Unavailable features are recorded separately and do not count as zero.

## Important
The app does not call provider APIs or automatically run experiments. Test the tools manually and enter real observations. Avoid private or confidential materials.
