from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QTimeEdit,
    QLineEdit,
    QPushButton,
)


class TimeInputDialog(QDialog):
    def __init__(self, event=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Add' if event else 'Edit'} Event")

        mainLayout = QVBoxLayout()
        inputLayout = QHBoxLayout()

        self.timeEdit = QTimeEdit()
        self.timeEdit.setDisplayFormat("HH:mm")
        if event:
            self.timeEdit.setTime(QTime(event.event_date.hour, event.event_date.minute))
        else:
            self.timeEdit.setTime(QTime(9, 0))

        self.textField = QLineEdit()
        self.textField.setPlaceholderText("Enter description:")
        if event:
            self.textField.setText(event.description)

        inputLayout.addWidget(self.timeEdit)
        inputLayout.addWidget(self.textField)

        buttonLayout = QHBoxLayout()
        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")

        okButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)

        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        mainLayout.addLayout(inputLayout)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

    def getTime(self):
        return self.timeEdit.time().toString("HH:mm")

    def getText(self):
        return self.textField.text()
