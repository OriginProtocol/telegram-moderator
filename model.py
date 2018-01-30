from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import os

postgres_url = os.environ["TELEGRAM_BOT_POSTGRES_URL"]


'''
This model has been referenced from: https://www.pythoncentral.io/sqlalchemy-orm-examples/
'''

Base = declarative_base()


class User(Base):
    __tablename__ = 'telegram_users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)


class Message(Base):
    __tablename__ = 'telegram_messages'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    message = Column(String)
    # Use default=func.now() to set the default hiring time
    # of an Employee to be the current time when an
    # Employee record was created
    time = Column(DateTime, default=func.now())


from sqlalchemy import create_engine
engine = create_engine(postgres_url)

from sqlalchemy.orm import sessionmaker
session = sessionmaker()
session.configure(bind=engine)
Base.metadata.create_all(engine)
print "Created database model"
