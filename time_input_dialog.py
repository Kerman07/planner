from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QTimeEdit,
                           QLineEdit, QPushButton)
from PyQt5.QtCore import QTime

class TimeInputDialog(QDialog):
    def __init__(self, event=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Add' if event else 'Edit'} Event")
        
        main_layout = QVBoxLayout()    
        input_layout = QHBoxLayout()
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        if event:
            self.time_edit.setTime(QTime(event.event_date.hour, event.event_date.minute))
        else:
            self.time_edit.setTime(QTime(9, 0))
        
        self.text_field = QLineEdit()
        self.text_field.setPlaceholderText("Enter description:")
        if event:
            self.text_field.setText(event.description)
        
        input_layout.addWidget(self.time_edit)
        input_layout.addWidget(self.text_field)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(input_layout)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def get_time(self):
        return self.time_edit.time().toString("HH:mm")
    
    def get_text(self):
        return self.text_field.text()
