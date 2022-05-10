from flask import Flask
from data import db_session, auth_api, problems_api
from data.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

#отдельный файл для добавления пользователя с правами учителя
def main():
    db_session.global_init("db/domino.db")
    teacher = User()
    teacher.name = 'Системы'
    teacher.surname = 'Администратор'
    teacher.role = 1
    teacher.email = 'admin@e.mail'
    teacher.hashed_password = teacher.set_password('P@ssw0rd')
    session = db_session.create_session()
    session.add(teacher)
    session.commit()


if __name__ == '__main__':
    main()