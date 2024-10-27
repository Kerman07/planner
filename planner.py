import sys
from datetime import datetime
from os import path

from PyQt5.QtCore import QDate, QTime, QTimer, Qt
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QTextCharFormat

from PyQt5.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLCDNumber,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.event import Event
from style import STYLESHEET
from time_input_dialog import TimeInputDialog


class Calendar(QWidget):
    def __init__(self, width, height, session):
        super().__init__()
        self.session = session

        folder = path.dirname(__file__)
        self.iconFolder = path.join(folder, "icons")

        self.setWindowTitle("Planner")
        self.setWindowIcon(QIcon(path.join(self.iconFolder, "window.png")))

        self.setGeometry(width // 4, height // 4, width // 2, height // 2)
        self.initUI()

    def initUI(self):
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)

        # format for dates in calendar that have events
        self.fmt = QTextCharFormat()
        self.fmt.setBackground(QColor(255, 165, 0, 100))

        # format for the current day
        curDayFmt = QTextCharFormat()
        curDayFmt.setBackground(QColor(0, 255, 90, 70))

        # format to change back to if all events are deleted
        self.delFmt = QTextCharFormat()
        self.delFmt.setBackground(Qt.transparent)

        # load events from the database
        self.events = Event.eventsFromMidnight(self.session)

        # format the dates in the calendar that have events
        for event in self.events:
            qdate = QDate(
                event.event_date.year, event.event_date.month, event.event_date.day
            )
            self.calendar.setDateTextFormat(qdate, self.fmt)

        # mark current day in calendar
        self.calendar.setDateTextFormat(QDate.currentDate(), curDayFmt)

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

        self.noteGroup = QListWidget()
        self.noteGroup.setSortingEnabled(True)
        self.noteGroup.setStyleSheet("QListView::item {height: 40px;}")

        todayButton = QPushButton("Today")
        todayButton.clicked.connect(self.selectToday)
        self.label = QLabel()
        labelFont = QFont("Arial", 16)
        self.label.setFont(labelFont)
        self.labelDate()
        self.showDateInfo()

        labelp = QLabel()
        pixmap = QPixmap(path.join(self.iconFolder, "calendar.png"))
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
        vbox.addWidget(self.noteGroup)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        hbox = QHBoxLayout()
        hbox.addWidget(self.calendar, 55)
        hbox.addLayout(vbox, 45)

        self.setLayout(hbox)

    def showDateInfo(self):
        # add events to selected date
        date = self.calendar.selectedDate()
        specificDate = datetime(date.year(), date.month(), date.day())
        self.noteGroup.clear()
        for event in Event.eventsOnDate(self.session, specificDate):
            item = QListWidgetItem(str(event))
            item.setData(Qt.UserRole, event.id)
            self.noteGroup.addItem(item)

    def selectToday(self):
        self.calendar.setSelectedDate(QDate.currentDate())

    def toggleAddEditDeleteButtons(self):
        isFutureDate = self.calendar.selectedDate() >= QDate.currentDate()
        hasEvents = self.noteGroup.count() > 0

        self.addButton.setEnabled(isFutureDate)
        self.editButton.setEnabled(isFutureDate and hasEvents)
        self.delButton.setEnabled(isFutureDate and hasEvents)

    def addNote(self):
        # adding notes for selected date
        date = self.calendar.selectedDate().toPyDate()
        newEventDialog = TimeInputDialog()

        if newEventDialog.exec_() != QDialog.Accepted:
            return

        eventTimeStr = newEventDialog.getTime()
        eventDescription = newEventDialog.getText()

        eventTime = datetime.strptime(eventTimeStr, "%H:%M").time()
        eventDate = datetime.combine(date, eventTime)

        newEvent = Event(event_date=eventDate, description=eventDescription)

        qdate = QDate(
            newEvent.event_date.year,
            newEvent.event_date.month,
            newEvent.event_date.day,
        )
        self.calendar.setDateTextFormat(qdate, self.fmt)

        self.session.add(newEvent)
        self.session.commit()

        self.showDateInfo()
        self.highlightFirstItem()
        self.toggleAddEditDeleteButtons()

    def delNote(self):
        # delete the currently selected item
        row = self.noteGroup.currentRow()
        item = self.noteGroup.item(row)

        reply = QMessageBox.question(
            self, " ", "Remove", QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        event = Event.eventById(self.session, item.data(Qt.UserRole))
        self.session.delete(event)
        self.session.commit()

        self.noteGroup.takeItem(row)
        if self.noteGroup.count() == 0:
            self.calendar.setDateTextFormat(
                QDate(
                    event.event_date.year, event.event_date.month, event.event_date.day
                ),
                self.delFmt,
            )

        self.showDateInfo()
        self.highlightFirstItem()

    def editNote(self):
        # update current note
        item = self.noteGroup.currentItem()
        event = Event.eventById(self.session, item.data(Qt.UserRole))

        editEventDialog = TimeInputDialog(event)

        if editEventDialog.exec_() != QDialog.Accepted:
            return

        eventTimeStr = editEventDialog.getTime()
        eventDescription = editEventDialog.getText()

        eventTime = datetime.strptime(eventTimeStr, "%H:%M").time()
        event.event_date = datetime.combine(event.event_date.date(), eventTime)
        event.description = eventDescription

        self.session.commit()
        item.setText(str(event))

    def labelDate(self):
        # label to show the long name form of the selected date
        # format US style like "Thursday, February 20, 2020"
        selectedDate = self.calendar.selectedDate()
        weekday = QDate.longDayName(selectedDate.dayOfWeek())
        month = QDate.longMonthName(selectedDate.month())

        self.label.setText(
            f"{weekday}, {month} {selectedDate.day()}, {selectedDate.year()}"
        )

    def highlightFirstItem(self):
        # highlight the first item immediately after switching selection
        if self.noteGroup.count() > 0:
            self.noteGroup.setCurrentRow(0)

    def showTime(self):
        # keep the current time updated
        time = QTime.currentTime()
        text = time.toString("hh:mm")
        if time.second() % 2 == 0:
            text.replace(text[2], "")
        self.lcd.display(text)

    def closeEvent(self, e):
        e.accept()


def open_db_session():
    engine = create_engine("sqlite:///events.db")
    Event.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    screen = app.primaryScreen()
    size = screen.size()
    window = Calendar(size.width(), size.height(), open_db_session())
    window.show()
    sys.exit(app.exec_())
