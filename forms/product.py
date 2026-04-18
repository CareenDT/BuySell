from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ProductForm(FlaskForm):
    name = StringField("Название товара", validators=[DataRequired(message="Введите название товара")])
    description = TextAreaField("Описание")
    price = FloatField("Цена", validators=[DataRequired(message="Введите цену"), NumberRange(min=0, message="цена должна быть больше 0")])
    submit = SubmitField("Добавить товар")