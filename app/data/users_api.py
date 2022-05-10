import flask
from flask import render_template, redirect, session
from data import db_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from data.users import User
from functools import wraps

blueprint = flask.Blueprint(
    'users_api',
    __name__,
    template_folder='templates'
)


def login_required(f): #функция, непозволяющая не авторизованным пользователям смотреть некоторые страницы
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        else:
            return redirect('/login')

    return wrap


@blueprint.route('/show_rating', methods=['GET', 'POST'])
@login_required
def show_rating():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    users.sort(key=lambda x: x.rating, reverse=True)
    return render_template('show_rating.html', title='Rating', users=users, num=len(users))