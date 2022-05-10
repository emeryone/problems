from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, StringField, EmailField, PasswordField
from wtforms.validators import DataRequired


class RegForm(FlaskForm):
    name = StringField('Имя')
    surname = StringField('Фамилия')
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
