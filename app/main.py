from flask import Flask, redirect, session
from flask_login import LoginManager
from data import db_session, auth_api, problems_api, users_api
from data.users import User
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


db_session.global_init("db/domino.db")
app.register_blueprint(auth_api.blueprint)
app.register_blueprint(problems_api.blueprint)
app.register_blueprint(users_api.blueprint)


def main():
    app.run()


if __name__ == '__main__':
    main()