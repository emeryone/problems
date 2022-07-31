from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField, StringField
from wtforms.validators import DataRequired, Length


class ProblemsForm(FlaskForm):
    text = TextAreaField('Условие', validators=[Length(min=1, message='Поле не должно быть пустым')])
    difficulty = SelectField('Сложность', choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    level = SelectField('Класс', choices=[5, 6, 7, 8, 9, 10, 11])
    answer = StringField('Ответ', validators=[Length(min=1, message='Поле не должно быть пустым')])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Добавить')