# Comment Generator desktop app

Native Windows version built with Python and PySide6.

## Run during development

From this folder:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build a Windows executable

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name CommentGenerator main.py
```

The executable will be created in `dist`. Python is bundled into the executable, so the end user does not need Python installed.

## Add another template

Add another dictionary to `templates.py` with a `name`, `comment`, and `fields`. Use matching placeholders such as `{operator}` in the comment and field IDs in the `fields` list.
