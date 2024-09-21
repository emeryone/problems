from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField, StringField, DateTimeField, DateTimeLocalField
from wtforms.validators import DataRequired, Length


class CreateTournamentForm(FlaskForm):
    start_date = DateTimeLocalField('Начало турнира', format="%Y-%m-%dT%H:%M")
    end_date = DateTimeLocalField('Окончание турнира', format="%Y-%m-%dT%H:%M")
    submit = SubmitField('Завершить создание турнира')