from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField, StringField
from wtforms.validators import DataRequired, Length


class TournamentForm(FlaskForm):
    name =StringField('Название', validators=[Length(min=1, message='Поле не должно быть пустым')])
    level = SelectField('Класс', choices=[5, 6, 7, 8, 9, 10, 11])
    submit = SubmitField('Продолжить')