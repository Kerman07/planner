from datetime import datetime, time, timedelta
from sqlalchemy import Column, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    event_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)

    def __str__(self):
        return f"{self.event_date.strftime('%H:%M')} | {self.description}"

    @classmethod
    def eventsFromMidnight(cls, session):
        today_midnight = datetime.combine(datetime.today(), time.min)

        return session.query(cls)\
                      .filter(cls.event_date >= today_midnight)\
                      .order_by(cls.event_date)\
                      .all()

    @classmethod
    def eventsOnDate(cls, session, specific_date):
        start_of_day = specific_date.replace(hour=0, minute=0, second=0)
        end_of_day = start_of_day + timedelta(days=1)

        return session.query(cls)\
                      .filter(cls.event_date >= start_of_day, cls.event_date < end_of_day)\
                      .order_by(cls.event_date)\
                      .all()

