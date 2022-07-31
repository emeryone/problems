from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField, StringField
from wtforms.validators import DataRequired, Length


class AnswerForm(FlaskForm):
    answer = StringField('Ответ', validators=[Length(min=1, message='Поле не должно быть пустым')])
    submit = SubmitField('Сдать ответ')