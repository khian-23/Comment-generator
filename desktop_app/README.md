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

## Add or edit templates

Use the `+ Add template` button to create a new task. Use `Edit selected` after choosing a task to update its name, comment, or required fields. In the fields table, enable `Blank line after` when a field should be followed by an extra blank line. Templates are saved in the operating system's application data folder and are loaded automatically the next time the app starts.

When writing a comment, use placeholders such as `{operator}`. Add a field with the matching ID `operator` and a user-facing label such as `Operator`.

## Add another template

The five starter templates are defined in `templates.py`. New templates should normally be added through the app so they are saved automatically.
