"""Comment Generator desktop application."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QPlainTextEdit, QPushButton, QSizePolicy,
    QSplitter, QVBoxLayout, QWidget,
)

from templates import TEMPLATES


class CommentGeneratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.templates = TEMPLATES
        self.selected_template = None
        self.field_widgets = {}
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
        root_layout.setContentsMargins(32, 28, 32, 28)
        root_layout.setSpacing(12)

        eyebrow = QLabel("EVERYDAY TASK NOTES")
        eyebrow.setObjectName("eyebrow")
        root_layout.addWidget(eyebrow)
        title = QLabel("Comment Generator")
        title.setObjectName("title")
        root_layout.addWidget(title)
        subtitle = QLabel("Find a task, enter the details, and copy the finished comment.")
        subtitle.setObjectName("subtitle")
        root_layout.addWidget(subtitle)

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

    def clear_form(self):
        while self.details_form.rowCount():
            self.details_form.removeRow(0)
        self.field_widgets.clear()

    @staticmethod
    def field_value(widget):
        return widget.toPlainText().strip() if isinstance(widget, QPlainTextEdit) else widget.text().strip()

    def update_preview(self):
        if self.selected_template is None:
            return
        values = {}
        for field in self.selected_template["fields"]:
            value = self.field_value(self.field_widgets[field["id"]])
            values[field["id"]] = value or f"[{field['label']}]"
        comment = self.selected_template["comment"]
        for key, value in values.items():
            comment = comment.replace("{" + key + "}", value)
        self.preview.setPlainText(comment)
        self.character_count.setText(f"{len(comment)} characters")
        self.status_label.clear()

    def copy_comment(self):
        QApplication.clipboard().setText(self.preview.toPlainText())
        self.status_label.setText("Comment copied to clipboard.")


STYLESHEET = """
QWidget#root { background: #f5f7fb; color: #1d2633; }
QLabel#eyebrow { color: #4f46e5; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; }
QLabel#title { color: #1d2633; font-size: 32px; font-weight: 800; }
QLabel#subtitle, QLabel#muted { color: #778293; font-size: 13px; }
QLabel#section-label { color: #4f5b6b; font-size: 12px; font-weight: 700; }
QLabel#content-title { color: #1d2633; font-size: 22px; font-weight: 700; padding-bottom: 8px; }
QLabel#status { color: #16845b; font-size: 12px; }
QLineEdit, QPlainTextEdit, QListWidget { color: #344052; background: #ffffff; border: 1px solid #dfe4ec; border-radius: 8px; padding: 8px; }
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #4f46e5; }
QListWidget { padding: 5px; }
QListWidget::item { padding: 11px 9px; border-radius: 6px; color: #566274; }
QListWidget::item:hover, QListWidget::item:selected { color: #4f46e5; background: #eef0ff; }
QLabel { color: #4f5b6b; }
QPushButton#copy-button { color: white; background: #4f46e5; border: 0; border-radius: 7px; padding: 10px 16px; font-weight: 700; }
QPushButton#copy-button:hover { background: #4338ca; }
QPushButton#copy-button:disabled { background: #aeb5c5; }
"""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont))
    app.setStyleSheet(STYLESHEET)
    window = CommentGeneratorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
