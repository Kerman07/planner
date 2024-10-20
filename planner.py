import sys
from datetime import datetime, time, timedelta

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QCalendarWidget,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDialog,
    QInputDialog,
    QLCDNumber,
)
from PyQt5.QtCore import QDate, Qt, QTimer, QTime
from PyQt5 import QtGui
from PyQt5.QtGui import QTextCharFormat, QColor, QPixmap
from style import STYLESHEET
from os import path
from time_input_dialog import TimeInputDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.event import Event


class Calendar(QWidget):
    def __init__(self, width, height):
        super().__init__()
        engine = create_engine('sqlite:///events.db')
        Session = sessionmaker(bind=engine)
        self.session = Session()

        folder = path.dirname(__file__)
        self.icon_folder = path.join(folder, "icons")

        self.setWindowTitle("Planner")
        self.setWindowIcon(QtGui.QIcon(path.join(self.icon_folder, "window.png")))

        self.setGeometry(width // 4, height // 4, width // 2, height // 2)
        self.initUI()

    def initUI(self):
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)

        # format for dates in calendar that have events
        self.fmt = QTextCharFormat()
        self.fmt.setBackground(QColor(255, 165, 0, 100))

        # format for the current day
        cur_day_fmt = QTextCharFormat()
        cur_day_fmt.setBackground(QColor(0, 255, 90, 70))

        # format to change back to if all events are deleted
        self.delfmt = QTextCharFormat()
        self.delfmt.setBackground(Qt.transparent)

        # load events from the database
        self.events = Event.eventsFromMidnight(self.session)

        # format the dates in the calendar that have events
        for event in self.events:
            qdate = QDate(event.event_date.year, event.event_date.month, event.event_date.day)
            self.calendar.setDateTextFormat(qdate, self.fmt)

        # mark current day in calendar
        cur_date = QDate.currentDate()
        self.calendar.setDateTextFormat(cur_date, cur_day_fmt)

        # organize buttons and layouts for display
        self.addButton = QPushButton("Add Event")
        self.addButton.clicked.connect(self.addNote)
        self.editButton = QPushButton("Edit")
        self.editButton.clicked.connect(self.editNote)
        self.delButton = QPushButton("Delete")
        self.delButton.clicked.connect(self.delNote)

        self.calendar.selectionChanged.connect(self.showDateInfo)
        self.calendar.selectionChanged.connect(self.labelDate)
        self.calendar.selectionChanged.connect(self.highlightFirstItem)
        self.calendar.selectionChanged.connect(self.toggleAddEditDeleteButtons)

        self.note_group = QListWidget()
        self.note_group.setSortingEnabled(True)
        self.note_group.setStyleSheet("QListView::item {height: 40px;}")

        todayButton = QPushButton("Today")
        todayButton.clicked.connect(self.selectToday)
        self.label = QLabel()
        label_font = QtGui.QFont("Arial", 16)
        self.label.setFont(label_font)
        self.labelDate()
        self.showDateInfo()

        labelp = QLabel()
        pixmap = QPixmap(path.join(self.icon_folder, "calendar.png"))
        labelp.setPixmap(pixmap)

        # set up a timer that automatically updates every second
        self.lcd = QLCDNumber()
        self.lcd.setSegmentStyle(QLCDNumber.Filled)
        self.lcd.setMinimumWidth(80)
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
        self.showTime()

        hbox1 = QHBoxLayout()
        hbox1.addWidget(todayButton)
        hbox1.addStretch(1)
        hbox1.addWidget(self.label)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.addButton)
        hbox2.addWidget(self.editButton)
        hbox2.addWidget(self.delButton)

        hbox3 = QHBoxLayout()
        hbox3.addStretch(1)
        hbox3.addWidget(labelp)
        hbox3.addWidget(self.lcd)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.note_group)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        hbox = QHBoxLayout()
        hbox.addWidget(self.calendar, 55)
        hbox.addLayout(vbox, 45)

        self.setLayout(hbox)

    def showDateInfo(self):
        # add events to selected date
        date = self.calendar.selectedDate()
        specific_date = datetime(date.year(), date.month(), date.day())
        self.note_group.clear()
        for event in Event.eventsOnDate(self.session, specific_date):
            item = QListWidgetItem(str(event))
            item.setData(Qt.UserRole, event.id)
            self.note_group.addItem(item)

    def selectToday(self):
        self.calendar.setSelectedDate(QDate.currentDate())

    def toggleAddEditDeleteButtons(self):
        is_future_date = self.calendar.selectedDate() >= QDate.currentDate()
        has_events = self.note_group.count() > 0

        self.addButton.setEnabled(is_future_date)
        self.editButton.setEnabled(is_future_date and has_events)
        self.delButton.setEnabled(is_future_date and has_events)

    def addNote(self):
        # adding notes for selected date
        date = self.calendar.selectedDate().toPyDate()
        new_event_dialog = TimeInputDialog()

        if new_event_dialog.exec_() != QDialog.Accepted:
            return

        event_time_str = new_event_dialog.get_time()
        event_description = new_event_dialog.get_text()

        event_time = datetime.strptime(event_time_str, "%H:%M").time()
        event_date = datetime.combine(date, event_time)

        new_event = Event(event_date=event_date, description=event_description)

        qdate = QDate(new_event.event_date.year, new_event.event_date.month, new_event.event_date.day)
        self.calendar.setDateTextFormat(qdate, self.fmt)

        self.session.add(new_event)
        self.session.commit()
        
        self.showDateInfo()
        self.highlightFirstItem()
        self.toggleAddEditDeleteButtons()

    def delNote(self):
        # delete the currently selected item
        row = self.note_group.currentRow()
        item = self.note_group.item(row)

        reply = QMessageBox.question(
            self, " ", "Remove", QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return
        
        event = self.session.query(Event).filter(Event.id == item.data(Qt.UserRole)).first()
        self.session.delete(event)
        self.session.commit()

        self.note_group.takeItem(row)
        if self.note_group.count() == 0:
            self.calendar.setDateTextFormat(
                QDate(event.event_date.year, event.event_date.month, event.event_date.day), 
                self.delfmt
            )

        self.showDateInfo()
        self.highlightFirstItem()
            

    def editNote(self):
        # update current note
        item = self.note_group.currentItem()
        event = self.session.query(Event).filter(Event.id == item.data(Qt.UserRole)).first()
        
        edit_event_dialog = TimeInputDialog(event)

        if edit_event_dialog.exec_() != QDialog.Accepted:
            return
        
        event_time_str = edit_event_dialog.get_time()
        event_description = edit_event_dialog.get_text()

        event_time = datetime.strptime(event_time_str, "%H:%M").time()
        event.event_date = datetime.combine(event.event_date.date(), event_time)
        event.description = event_description
        
        self.session.commit()
        item.setText(str(event))

    def labelDate(self):
        # label to show the long name form of the selected date
        # format US style like "Thursday, February 20, 2020"
        selected_date = self.calendar.selectedDate()
        weekday = QDate.longDayName(selected_date.dayOfWeek())
        month = QDate.longMonthName(selected_date.month())
        
        self.label.setText(f"{weekday}, {month} {selected_date.day()}, {selected_date.year()}")

    def highlightFirstItem(self):
        # highlight the first item immediately after switching selection
        if self.note_group.count() > 0:
            self.note_group.setCurrentRow(0)

    def showTime(self):
        # keep the current time updated
        time = QTime.currentTime()
        text = time.toString("hh:mm")
        if time.second() % 2 == 0:
            text.replace(text[2], "")
        self.lcd.display(text)

    def closeEvent(self, e):
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    screen = app.primaryScreen()
    size = screen.size()
    window = Calendar(size.width(), size.height())
    window.show()
    sys.exit(app.exec_())
