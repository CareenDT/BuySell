import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, orm, JSON
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Chat(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now())
    contents = Column(JSON, default=JSON())

    user = orm.relationship("User")