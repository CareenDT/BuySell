import datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, orm, Column, String, Integer
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    username = Column(String, nullable=True)
    about = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)

    hashed_password = Column(String, nullable=True)

    joined_date = Column(DateTime, default=datetime.datetime.now())
    modified_date = Column(DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return f"{self.username}: {self.joined_date}"
    
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
