import flask
from flask import render_template, redirect
from data import db_session
from data.problems import Problems, users_to_problems
from data.problems_form import ProblemsForm
from data.answer_form import AnswerForm
from flask_login import current_user
from flask_login import LoginManager, login_user, logout_user
from sqlalchemy import and_
from data.users import User
from functools import wraps
from flask import Flask, redirect, session


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
            db_sess.add(problem)
            db_sess.commit()
            return redirect('/show_problems')
        return render_template('problems_form.html', title='Add problem',
                               form=form)
    return redirect('/deny')


@blueprint.route('/show_problems', methods=['GET', 'POST'])
@login_required
def show_problems():
    db_sess = db_session.create_session()
    problems = db_sess.query(Problems).all()
    return render_template('show_problems.html', title='Show problems',
                           problems=problems, num=len(problems))


@blueprint.route('/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def problem_answer(problem_id):
    form = AnswerForm()
    db_sess = db_session.create_session()
    problem = db_sess.query(Problems).filter(Problems.id == problem_id).first()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    if form.validate_on_submit():
        s = (users_to_problems.select()
             .where(and_(users_to_problems.c.user == current_user.id, users_to_problems.c.problem == problem_id)))
        u_result = db_sess.execute(s).all()
        if not u_result:
            if form.answer.data == problem.answer:
                u = users_to_problems.insert().values(result=problem.difficulty,
                                                      user=current_user.id, problem=problem_id)
                db_sess.execute(u)
                db_sess.commit()
                user.rating = user.rating + problem.difficulty
                db_sess.commit()
                return redirect('/right_answer')
            u = users_to_problems.insert().values(result=0, user=current_user.id, problem=problem_id)
            db_sess.execute(u)
            db_sess.commit()
            return redirect('/wrong_answer')
        if u_result[0][2] == -2: #проверка, что задача сдана меньше двух раз
            return redirect('/answer_exceed')
        if u_result[0][2] > 0: #проверка, что по задаче еще не дан правильный ответ
            return redirect('/have_right_answer')
        if form.answer.data == problem.answer:
            u = users_to_problems.update().values(result=problem.difficulty) \
                .where(and_(users_to_problems.c.user == current_user.id, users_to_problems.c.problem == problem_id))
            db_sess.execute(u)
            db_sess.commit()
            user.rating = user.rating + problem.difficulty
            db_sess.commit()
            return redirect('/right_answer')
        u = users_to_problems.update().values(result=-2) \
            .where(and_(users_to_problems.c.user == current_user.id, users_to_problems.c.problem == problem_id))
        db_sess.execute(u)
        db_sess.commit()
        user.rating = user.rating - 2
        db_sess.commit()
        return redirect('/wrong_answer')
    return render_template('answer_form.html', title='Answer',
                           problem=problem, form=form)


@blueprint.route('/right_answer')
@login_required
def right_answer():
    return render_template('right_answer.html', title='Right answer')


@blueprint.route('/wrong_answer')
@login_required
def wrong_answer():
    return render_template('wrong_answer.html', title='Right answer')


@blueprint.route('/answer_exceed')
@login_required
def answer_exceed():
    return render_template('answer_exceed.html', title='Answer exceed')


@blueprint.route('/have_right_answer')
@login_required
def have_right_answer():
    return render_template('have_right_answer.html', title='Answer exceed')


@blueprint.route('/deny')
@login_required
def deny():
    return render_template('deny.html', title='Deny')
