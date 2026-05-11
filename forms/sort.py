from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired

class SortForm(FlaskForm):
    sort_type = RadioField('Сортировать',
                           choices=[
                               ('price_asc', 'По цене, дешевле'),
                               ('price_desc', 'По цене, дороже'),
                               ('newest', 'Сначала новые')
                           ],
                           validators=[DataRequired()])
    submit = SubmitField('Применить')