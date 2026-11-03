"""Comment Generator desktop application."""

import copy
import json
import re
import sys
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QStandardPaths, Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QSizePolicy, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from templates import TEMPLATES


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.drag_offset = None
        self.setObjectName("title-bar")
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(4)

        layout.addStretch()

        minimize = QPushButton("—")
        minimize.setObjectName("window-button")
        minimize.clicked.connect(window.showMinimized)
        layout.addWidget(minimize)

        maximize = QPushButton("□")
        maximize.setObjectName("window-button")
        maximize.clicked.connect(self.toggle_maximize)
        layout.addWidget(maximize)

        close = QPushButton("×")
        close.setObjectName("close-button")
        close.clicked.connect(window.close)
        layout.addWidget(close)

    def toggle_maximize(self):
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, _event):
        self.drag_offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()


class TemplateEditorDialog(QDialog):
    def __init__(self, template=None, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("Edit template" if template else "Add template")
        self.setMinimumSize(700, 560)
        self.build_ui()
        if template:
            self.load_template(template)

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Edit comment template" if self.template else "Add comment template")
        title.setObjectName("content-title")
        layout.addWidget(title)
        help_text = QLabel("Use placeholders such as {operator} to control placement. Fields without placeholders are added as labeled lines automatically.")
        help_text.setObjectName("subtitle")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Example: Job retry")
        form.addRow("Task name", self.name_input)
        self.comment_input = QPlainTextEdit()
        self.comment_input.setPlaceholderText("Write the comment and add placeholders like {operator}...")
        self.comment_input.setFixedHeight(130)
        form.addRow("Comment", self.comment_input)
        layout.addLayout(form)

        fields_label = QLabel("Required fields")
        fields_label.setObjectName("section-label")
        layout.addWidget(fields_label)
        self.fields_table = QTableWidget(0, 4)
        self.fields_table.setHorizontalHeaderLabels(["Field ID", "Label", "Multiline", "Blank line after"])
        self.fields_table.horizontalHeader().setStretchLastSection(True)
        self.fields_table.setColumnWidth(0, 190)
        self.fields_table.setColumnWidth(1, 250)
        self.fields_table.setColumnWidth(2, 90)
        self.fields_table.setMinimumHeight(170)
        layout.addWidget(self.fields_table)

        field_buttons = QHBoxLayout()
        add_field = QPushButton("Add field")
        add_field.clicked.connect(self.add_field_row)
        remove_field = QPushButton("Remove selected field")
        remove_field.clicked.connect(self.remove_field_row)
        field_buttons.addWidget(add_field)
        field_buttons.addWidget(remove_field)
        field_buttons.addStretch()
        layout.addLayout(field_buttons)

        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        actions.accepted.connect(self.validate_and_accept)
        actions.rejected.connect(self.reject)
        layout.addWidget(actions)

    def load_template(self, template):
        self.name_input.setText(template["name"])
        self.comment_input.setPlainText(template["comment"])
        for field in template["fields"]:
            self.add_field_row(field)

    def add_field_row(self, field=None):
        row = self.fields_table.rowCount()
        self.fields_table.insertRow(row)
        self.fields_table.setItem(row, 0, QTableWidgetItem(field.get("id", "") if field else ""))
        self.fields_table.setItem(row, 1, QTableWidgetItem(field.get("label", "") if field else ""))
        multiline = QTableWidgetItem()
        multiline.setFlags(multiline.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        multiline.setCheckState(Qt.CheckState.Checked if field and field.get("multiline") else Qt.CheckState.Unchecked)
        self.fields_table.setItem(row, 2, multiline)
        space_after = QTableWidgetItem()
        space_after.setFlags(space_after.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        space_after.setCheckState(Qt.CheckState.Checked if field and field.get("space_after") else Qt.CheckState.Unchecked)
        self.fields_table.setItem(row, 3, space_after)

    def remove_field_row(self):
        row = self.fields_table.currentRow()
        if row >= 0:
            self.fields_table.removeRow(row)

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        comment = self.comment_input.toPlainText().strip()
        if not name or not comment:
            QMessageBox.warning(self, "Missing information", "Enter both a task name and a comment template.")
            return

        fields = []
        seen_ids = set()
        for row in range(self.fields_table.rowCount()):
            id_item = self.fields_table.item(row, 0)
            label_item = self.fields_table.item(row, 1)
            field_id = id_item.text().strip() if id_item else ""
            label = label_item.text().strip() if label_item else ""
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", field_id) or not label:
                QMessageBox.warning(self, "Invalid field", "Each field needs a valid ID and label. Field IDs may use letters, numbers, and underscores.")
                return
            if field_id in seen_ids:
                QMessageBox.warning(self, "Duplicate field", f"The field ID '{field_id}' is used more than once.")
                return
            seen_ids.add(field_id)
            fields.append({
                "id": field_id,
                "label": label,
                "multiline": self.fields_table.item(row, 2).checkState() == Qt.CheckState.Checked,
                "space_after": self.fields_table.item(row, 3).checkState() == Qt.CheckState.Checked,
            })

        self.result_template = {
            "id": self.template["id"] if self.template else f"custom-{uuid4().hex}",
            "name": name,
            "comment": comment,
            "fields": fields,
        }
        self.accept()


class CommentGeneratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.templates_path = self.get_templates_path()
        self.templates = self.load_templates()
        self.selected_template = None
        self.field_widgets = {}
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Comment Generator")
        self.setMinimumSize(900, 620)
        self.resize(1050, 700)
        self.build_ui()
        self.load_task_list()

    def build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(22, 18, 22, 22)
        root_layout.setSpacing(14)

        root_layout.addWidget(TitleBar(self))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root_layout.addWidget(splitter, 1)

        task_panel = QWidget()
        task_layout = QVBoxLayout(task_panel)
        task_layout.setContentsMargins(0, 16, 14, 0)
        task_label = QLabel("Search tasks")
        task_label.setObjectName("section-label")
        task_layout.addWidget(task_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by task name...")
        self.search_input.textChanged.connect(self.load_task_list)
        task_layout.addWidget(self.search_input)
        self.task_list = QListWidget()
        self.task_list.setWordWrap(True)
        self.task_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_list.currentItemChanged.connect(self.select_task)
        task_layout.addWidget(self.task_list, 1)
        task_actions = QHBoxLayout()
        add_template = QPushButton("+ Add template")
        add_template.clicked.connect(self.add_template)
        edit_template = QPushButton("Edit selected")
        edit_template.clicked.connect(self.edit_template)
        task_actions.addWidget(add_template)
        task_actions.addWidget(edit_template)
        task_layout.addLayout(task_actions)
        splitter.addWidget(task_panel)

        self.content_panel = QWidget()
        content_layout = QVBoxLayout(self.content_panel)
        content_layout.setContentsMargins(14, 16, 0, 0)
        self.selected_label = QLabel("Select a task to begin")
        self.selected_label.setObjectName("content-title")
        content_layout.addWidget(self.selected_label)

        self.details_form = QFormLayout()
        self.details_form.setVerticalSpacing(12)
        self.details_form.setLabelAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addLayout(self.details_form)

        result_label = QLabel("Generated comment")
        result_label.setObjectName("section-label")
        content_layout.addWidget(result_label)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Your generated comment will appear here.")
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self.preview, 1)

        footer = QHBoxLayout()
        self.character_count = QLabel("0 characters")
        self.character_count.setObjectName("muted")
        footer.addWidget(self.character_count)
        footer.addStretch()
        self.copy_button = QPushButton("Copy comment")
        self.copy_button.setObjectName("copy-button")
        self.copy_button.clicked.connect(self.copy_comment)
        self.copy_button.setEnabled(False)
        footer.addWidget(self.copy_button)
        content_layout.addLayout(footer)
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        content_layout.addWidget(self.status_label)
        splitter.addWidget(self.content_panel)
        splitter.setSizes([360, 610])

    @staticmethod
    def get_templates_path():
        app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        return Path(app_data) / "templates.json"

    def load_templates(self):
        try:
            if self.templates_path.exists():
                with self.templates_path.open("r", encoding="utf-8") as file:
                    saved = json.load(file)
                if isinstance(saved, list):
                    return saved
        except (OSError, json.JSONDecodeError):
            pass
        return copy.deepcopy(TEMPLATES)

    def save_templates(self):
        try:
            self.templates_path.parent.mkdir(parents=True, exist_ok=True)
            with self.templates_path.open("w", encoding="utf-8") as file:
                json.dump(self.templates, file, indent=2)
        except OSError as error:
            QMessageBox.warning(self, "Could not save templates", str(error))

    def load_task_list(self):
        query = self.search_input.text().strip().lower()
        current_id = self.selected_template["id"] if self.selected_template else None
        self.task_list.blockSignals(True)
        self.task_list.clear()
        for template in self.templates:
            if query and query not in template["name"].lower():
                continue
            item = QListWidgetItem(template["name"])
            item.setData(Qt.ItemDataRole.UserRole, template["id"])
            self.task_list.addItem(item)
            if template["id"] == current_id:
                self.task_list.setCurrentItem(item)
        self.task_list.blockSignals(False)

    def select_task(self, current, _previous):
        if current is None:
            return
        template_id = current.data(Qt.ItemDataRole.UserRole)
        self.selected_template = next((item for item in self.templates if item["id"] == template_id), None)
        if self.selected_template is None:
            return
        self.selected_label.setText(self.selected_template["name"])
        self.clear_form()
        for field in self.selected_template["fields"]:
            if field.get("multiline"):
                widget = QPlainTextEdit()
                widget.setPlaceholderText(f"Enter {field['label'].lower()}...")
                widget.setFixedHeight(72)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText(f"Enter {field['label'].lower()}...")
            widget.textChanged.connect(self.update_preview)
            self.field_widgets[field["id"]] = widget
            self.details_form.addRow(QLabel(field["label"]), widget)
        self.copy_button.setEnabled(True)
        self.update_preview()

    def select_template_by_id(self, template_id):
        for row in range(self.task_list.count()):
            item = self.task_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == template_id:
                self.task_list.blockSignals(True)
                self.task_list.setCurrentItem(item)
                self.task_list.blockSignals(False)
                self.select_task(item, None)
                return

    def add_template(self):
        dialog = TemplateEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.templates.append(dialog.result_template)
            self.save_templates()
            self.load_task_list()
            self.select_template_by_id(dialog.result_template["id"])

    def edit_template(self):
        if self.selected_template is None:
            QMessageBox.information(self, "Select a template", "Choose a template before editing it.")
            return
        dialog = TemplateEditorDialog(template=copy.deepcopy(self.selected_template), parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.result_template
            for index, template in enumerate(self.templates):
                if template["id"] == updated["id"]:
                    self.templates[index] = updated
                    break
            self.save_templates()
            self.selected_template = updated
            self.load_task_list()
            self.select_template_by_id(updated["id"])

    def clear_form(self):
        while self.details_form.rowCount():
            self.details_form.removeRow(0)
        self.field_widgets.clear()

    @staticmethod
    def field_value(widget):
        return widget.toPlainText().strip() if isinstance(widget, QPlainTextEdit) else widget.text().strip()

    def update_preview(self, *_args):
        if self.selected_template is None:
            return
        values = {}
        for field in self.selected_template["fields"]:
            value = self.field_value(self.field_widgets[field["id"]])
            values[field["id"]] = value or f"[{field['label']}]"
        comment = self.selected_template["comment"]
        used_fields = set(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", comment))
        for field in self.selected_template["fields"]:
            key = field["id"]
            value = values[key]
            if field.get("space_after"):
                value += "\n\n"
            comment = comment.replace("{" + key + "}", value)
        missing_fields = []
        for field in self.selected_template["fields"]:
            if field["id"] not in used_fields:
                line = f"{field['label']}: {values[field['id']]}"
                if field.get("space_after"):
                    line += "\n"
                missing_fields.append(line)
        if missing_fields:
            comment = comment.rstrip() + "\n\n" + "\n".join(missing_fields)
        self.preview.setPlainText(comment)
        self.character_count.setText(f"{len(comment)} characters")
        self.status_label.clear()

    def copy_comment(self):
        QApplication.clipboard().setText(self.preview.toPlainText())
        self.status_label.setText("Comment copied to clipboard.")


STYLESHEET = """
QWidget#root { background: #e9edf3; color: #172033; }
QWidget#title-bar { background: #e9edf3; border-bottom: 1px solid #dce2eb; }
QLabel#window-title { color: #273247; font-size: 13px; font-weight: 700; }
QPushButton#window-button, QPushButton#close-button { min-width: 30px; max-width: 30px; min-height: 26px; max-height: 26px; color: #7a8495; background: transparent; border: 0; border-radius: 6px; font-size: 15px; }
QPushButton#window-button:hover { color: #273247; background: #eef1f7; }
QPushButton#close-button:hover { color: #ffffff; background: #e45769; }
QLabel#eyebrow { color: #5b55e8; font-size: 10px; font-weight: 800; letter-spacing: 1.6px; }
QLabel#title { color: #172033; font-size: 36px; font-weight: 700; }
QLabel#subtitle, QLabel#muted { color: #718096; font-size: 14px; }
QLabel#section-label { color: #455166; font-size: 12px; font-weight: 700; }
QLabel#content-title { color: #172033; font-size: 24px; font-weight: 700; padding-bottom: 8px; }
QLabel#status { color: #16845b; font-size: 12px; }
QLineEdit, QPlainTextEdit, QListWidget { color: #273247; background: #ffffff; border: 1px solid #dce2eb; border-radius: 8px; padding: 9px; font-size: 13px; }
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #7169eb; background: #ffffff; }
QListWidget { padding: 5px; }
QListWidget::item { padding: 11px 9px; border-radius: 6px; color: #536077; font-size: 13px; }
QListWidget::item:hover, QListWidget::item:selected { color: #4d47cf; background: #eeefff; }
QLabel { color: #455166; font-size: 13px; }
QPushButton { color: #536077; background: #ffffff; border: 1px solid #dce2eb; border-radius: 7px; padding: 8px 11px; font-size: 12px; font-weight: 600; }
QPushButton:hover { color: #4d47cf; border-color: #bcb8f5; background: #f5f4ff; }
QPushButton#copy-button { color: white; background: #5b55e8; border: 0; border-radius: 7px; padding: 10px 16px; font-size: 13px; font-weight: 700; }
QPushButton#copy-button:hover { background: #4d47cf; }
QPushButton#copy-button:disabled { background: #aeb5c5; }
"""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    families = set(QFontDatabase.families())
    preferred_family = next((family for family in ("Segoe UI", "Arial", "DejaVu Sans", "Liberation Sans") if family in families), "Sans Serif")
    app_font = QFont(preferred_family, 10)
    app_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(app_font)
    app.setStyleSheet(STYLESHEET)
    window = CommentGeneratorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
