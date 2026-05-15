import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Column
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Order(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)

    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)

    amount = Column(Float, nullable=False, default=0.0)

    status = Column(String, nullable=False, default="pending", index=True)

    transaction_id = Column(String, nullable=True, index=True)


    payment_method = Column(String, nullable=True)

    created_date = Column(DateTime, default=datetime.datetime.now())

    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])

