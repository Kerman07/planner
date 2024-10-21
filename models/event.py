from datetime import datetime, time, timedelta
from sqlalchemy import Column, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    event_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)

    def __str__(self):
        return f"{self.event_date.strftime('%H:%M')} | {self.description}"

    @classmethod
    def eventsFromMidnight(cls, session):
        todayMidnight = datetime.combine(datetime.today(), time.min)

        return (
            session.query(cls)
            .filter(cls.event_date >= todayMidnight)
            .order_by(cls.event_date)
            .all()
        )

    @classmethod
    def eventsOnDate(cls, session, specific_date):
        startOfDay = specific_date.replace(hour=0, minute=0, second=0)
        endOfDay = startOfDay + timedelta(days=1)

        return (
            session.query(cls)
            .filter(cls.event_date >= startOfDay, cls.event_date < endOfDay)
            .order_by(cls.event_date)
            .all()
        )

    @classmethod
    def eventById(cls, session, id):
        return session.query(cls).filter(cls.id == id).first()
