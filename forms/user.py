from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField("Remember_me")
    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])

    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Confirm password', validators=[DataRequired()])

    email = EmailField('Email', validators=[DataRequired()])
    about = TextAreaField("About")

    submit = SubmitField('Submit')