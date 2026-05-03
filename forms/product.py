from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired, NumberRange, Length

class ProductForm(FlaskForm):
    name = StringField("Название товара", validators=[DataRequired(message="Введите название товара"), Length(min=4, message="название должно содержать больше 4 символов")])
    description = TextAreaField("Описание")
    price = FloatField("Цена", validators=[DataRequired(message="Введите цену"), NumberRange(min=0, message="цена должна быть больше 0")])
    image = FileField("Изображение")
    submit = SubmitField("Добавить товар")

class ProductSearchForm(FlaskForm):
    search = StringField("Название товара")
    submit = SubmitField("Искать")