import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, orm, Column, String, Integer, JSON, Float
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Products(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String, nullable = False, default="Unnamed product")
    description = Column(String, nullable = True, default="This product has no description")
    pricing = Column(Float, nullable = False)

    created_date = Column(DateTime, default=datetime.datetime.now())
    modified_date = Column(DateTime, nullable=True)