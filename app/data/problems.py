import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase

users_to_problems = sqlalchemy.Table(
    'users_to_problems',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('user', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('problem', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('problems.id')),
    sqlalchemy.Column('result', sqlalchemy.Integer, default=0) #колонка для счета баллов за задачу
)


class Problems(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'problems'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    owner = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    text = sqlalchemy.Column(sqlalchemy.String)
    difficulty = sqlalchemy.Column(sqlalchemy.Integer)
    level = sqlalchemy.Column(sqlalchemy.Integer)
    answer = sqlalchemy.Column(sqlalchemy.String)
    comment = sqlalchemy.Column(sqlalchemy.String, default='')
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)


