import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, orm, Column, String, Integer, JSON, Float
from sqlalchemy_serializer import SerializerMixin

from data.users import User
from .db_session import SqlAlchemyBase


class Products(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(Integer, ForeignKey("users.id"), nullable=True)

    name = Column(String, nullable=False, default="Unnamed product")
    description = Column(String, nullable=True, default="This product has no description")
    pricing = Column(Float, nullable=False)
    image = Column(String, nullable=True, default=None)

    created_date = Column(DateTime, default=datetime.datetime.now())
    modified_date = Column(DateTime, nullable=True)

    user = orm.relationship("User")
