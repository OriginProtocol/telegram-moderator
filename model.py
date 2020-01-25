from sqlalchemy import Column, DateTime, BigInteger, String, Integer, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import os

# Localhost url: postgresql://localhost/postgres
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
    chat_id = Column(BigInteger)
    time = Column(DateTime, default=func.now())


class MessageHide(Base):
    __tablename__ = 'telegram_message_hides'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    message = Column(String)
    time = Column(DateTime, default=func.now())


class UserBan(Base):
    __tablename__ = 'telegram_user_bans'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    reason = Column(String)
    time = Column(DateTime, default=func.now())


from sqlalchemy import create_engine
engine = create_engine(postgres_url)

from sqlalchemy.orm import sessionmaker
session = sessionmaker()
session.configure(bind=engine)
Base.metadata.create_all(engine)

print ("Created database model")
