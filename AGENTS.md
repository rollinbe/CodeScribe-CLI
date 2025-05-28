# Contributor & Agent Guide for CodeScribe

## Dev Environment Tips

- Use `python codescribe.py --help` to list available CLI options.
- Run `chmod +x codescribe.py` to make the script directly executable.
- Use `--minimal` to exclude boilerplate files (e.g. `dist/`, `.csproj`, `package-lock.json`).
- Test locally before committing. Run from the root directory to ensure relative imports work.

## Testing Instructions

- Test scripts live in `tests/test_codescribe.py` and use **Pytest**.
- From the repo root, run:

  ```bash
  pytest tests/
    ```
To test CLI behavior:

python codescribe.py --source <project> --minimal

python codescribe.py --source <project> --ignore-spec

python codescribe.py --source <project> --export-txt

python codescribe.py --source <project> --txt

python codescribe.py --source <project> --max-size 10

After any file move or CLI argument change, verify the full test suite still passes.

Add or update tests for any new feature or fix.

do not increment the version number of codescribe if it is not requested in the prompt. In this case add changes to change log in the last version at the same date


Linting & Style
Follow PEP8 (auto-lint with black or ruff recommended).

All new .py files must include encoding and a module-level docstring.

Keep user-facing help texts clear, in French.

Git & Commits
for create new branch use only basic char compatible with url .

Always leave the working tree in a clean state (git status must be clean).

If pre-commit fails, fix and retry before committing.

Each commit must include all changes. No amendments or force pushes.

PR Instructions
If an agent opens a PR:

Title format: [CodeScribe] <short description>

Summary must mention:

Options or arguments affected (e.g. --minimal)

Files added or modified

Tests added or adjusted

Output files generated (e.g. structure_complete.md)

Respect de la portée --minimal
Agents doivent s’assurer que les fichiers suivants sont exclus si --minimal est activé :

package-lock.json

tsconfig*.json, angular.json

dist/, src/index.html, environment*.ts, styles.css

.csproj, .sln, appsettings.json

.venv/, __pycache__/, *.spec.ts

Contact
Author: Benjamin Rollin
Email: benjamin.rollin [at] pm.me