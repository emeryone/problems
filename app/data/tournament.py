import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase

users_to_tournaments = sqlalchemy.Table(
    'users_to_tournaments',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('user', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('tournament', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('tournament.id')),
    sqlalchemy.Column('score', sqlalchemy.Integer, default=0) #колонка для счета баллов в турнире
)


tournament_set = sqlalchemy.Table(
    'tournament_set',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('tournament', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('tournament.id')),
    sqlalchemy.Column('position', sqlalchemy.String),
    sqlalchemy.Column('state', sqlalchemy.Integer, default=0),
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True)
)


class Tournament(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tournament'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    owner = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    name = sqlalchemy.Column(sqlalchemy.String)
    level = sqlalchemy.Column(sqlalchemy.Integer)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    state = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    start_date = sqlalchemy.Column(sqlalchemy.DateTime)
    end_date = sqlalchemy.Column(sqlalchemy.DateTime)

    problems = orm.relation("Problems", secondary="tournament_to_problems", backref="tournament")
