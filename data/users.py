import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, orm, Column, String, Integer
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    surname = Column(String, nullable=True)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)

    hashed_password = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    modified_date = Column(DateTime, default=datetime.datetime.now())