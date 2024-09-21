import flask
from flask import render_template, redirect
from data import db_session
from data.problems import Problems, users_to_problems, tournament_to_problems
from data.problems_form import ProblemsForm
from data.answer_form import AnswerForm
from flask_login import current_user
from flask_login import LoginManager, login_user, logout_user
from sqlalchemy import and_
from data.users import User
from functools import wraps
from flask import Flask, redirect, session
from data.tournament import Tournament, users_to_tournaments


def login_required(f):  #функция, непозволяющая не авторизованным пользователям смотреть некоторые страницы
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        else:
            return redirect('/login')

    return wrap


blueprint = flask.Blueprint(
    'problems_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/add_problem', methods=['GET', 'POST'])
@login_required
def add_problem():
    form = ProblemsForm()
    if current_user.role > 0:  #добавлять задачи может только пользователь с правами учителя
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            problem = Problems()
            problem.text = form.text.data
            problem.level = int(form.level.data)
            problem.difficulty = int(form.difficulty.data)
            problem.answer = form.answer.data
            problem.comment = form.comment.data
            problem.owner = current_user.id
            problem.theme = form.theme.data
            problem.solution = form.solution.data
            db_sess.add(problem)
            db_sess.commit()
            return redirect('/')
        return render_template('problems_form.html', title='Add problem',
                               form=form)
    return redirect('/deny')


@blueprint.route('/deny')
@login_required
def deny():
    return render_template('deny.html', title='Deny')
