from flask_login import LoginManager, login_user, logout_user, login_required
from flask import Flask, render_template, redirect
from data import db_session
from data.users import User
import flask
from data.login_form import LoginForm
from data.reg_form import RegForm

blueprint = flask.Blueprint(
    'auth_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@blueprint.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = User()
        user.name = form.name.data
        user.surname = form.surname.data
        user.email = form.email.data
        user.hashed_password = user.set_password(form.password.data)
        try:
            db_sess.add(user)
            db_sess.commit()
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        except Exception:
            return render_template('reg_form.html', message="Почта занята", form=form)
    return render_template('reg_form.html', title='Registration',
                           form=form)


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@blueprint.route('/')
def index():
    session = db_session.create_session()
    return render_template('base.html')


@blueprint.route('/help') #страница с правилами
def help_1():
    session = db_session.create_session()
    return render_template('help.html')