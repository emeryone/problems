from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField, StringField
from wtforms.validators import DataRequired


class ProblemsForm(FlaskForm):
    text = TextAreaField('Условие')
    difficulty = SelectField('Сложность', choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    level = SelectField('Класс', choices=[5, 6, 7, 8, 9, 10, 11])
    answer = StringField('Ответ')
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Добавить')