from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField, StringField
from wtforms.validators import DataRequired


class AnswerForm(FlaskForm):
    answer = StringField('Ответ')
    submit = SubmitField('Сдать ответ')