from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, StringField, EmailField, PasswordField
from wtforms.validators import DataRequired, Length


class RegForm(FlaskForm):
    name = StringField('Имя', validators=[Length(min=1, message='Поле не должно быть пустым')])
    surname = StringField('Фамилия', validators=[Length(min=1, message='Поле не должно быть пустым')])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
