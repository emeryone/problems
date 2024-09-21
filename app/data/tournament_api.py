import flask
from flask import render_template, redirect
from data import db_session
from data.problems import Problems, users_to_problems, tournament_to_problems
from flask_login import current_user
from data.tournament_form import TournamentForm
from data.tournament import Tournament, users_to_tournaments, tournament_set
from data.add_problem_to_tournament_form import AddProblemToTournamentForm
from flask_login import LoginManager, login_user, logout_user
from sqlalchemy import and_
from data.users import User
from functools import wraps
from flask import Flask, redirect, session
from data.answer_form import AnswerForm
from data.create_tournament_form import CreateTournamentForm
import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler


def login_required(f):  #функция, непозволяющая не авторизованным пользователям смотреть некоторые страницы
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        else:
            return redirect('/login')

    return wrap


blueprint = flask.Blueprint(
    'tournament_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/add_tournament', methods=['GET', 'POST'])
@login_required
def add_tournament():
    form = TournamentForm()
    if current_user.role > 0:  #добавлять турнир может только пользователь с правами учителя
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            tournament = Tournament()
            tournament.name = form.name.data
            tournament.level = int(form.level.data)
            tournament.owner = current_user.id
            db_sess.add(tournament)
            db_sess.commit()
            return redirect('/choose_problems/' + str(tournament.id))
        return render_template('tournament_form.html', title='Add tournament',
                               form=form)
    return redirect('/deny')


@blueprint.route('/add/<int:problem_id>/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def add_problem_to_tournament(problem_id, tournament_id):
    form = AddProblemToTournamentForm()
    if current_user.role > 0:  # добавлять турнир может только пользователь с правами учителя
        db_sess = db_session.create_session()
        problem = db_sess.query(Problems).filter(Problems.id == problem_id).first()
        tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
        if form.validate_on_submit():
            s = (tournament_to_problems.select()
                 .where(tournament_to_problems.c.tournament == tournament_id))
            p_result = db_sess.execute(s).all()
            positions = []
            for p in p_result:
                positions.append(p[2])
            if problem not in tournament.problems:
                if form.position.data not in positions:
                    t = tournament_to_problems.insert().values(position=form.position.data,
                                                               tournament=tournament_id, problem=problem_id)
                    db_sess.execute(t)
                    db_sess.commit()
                    return redirect('/tournament/' + str(tournament_id))
                return redirect('/position_already_is_in_tournament/' + str(tournament_id))
            return redirect('/problem_already_is_in_tournament/' + str(tournament_id))
        return render_template('add_problem_to_tournament.html', title='Add problem to tournament',
                               form=form)
    return redirect('/deny')


@blueprint.route('/<int:problem_id>/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def problem_to_tournament_info(problem_id, tournament_id):
    db_sess = db_session.create_session()
    problem = db_sess.query(Problems).filter(Problems.id == problem_id).first()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if current_user.role > 0:  # смотреть информацию по задачам может только пользователь с правами учителя
        return render_template('problem_to_tournament_info.html', problem=problem, tournament_id=tournament_id,
                               tournament=tournament)
    return redirect('/deny')


@blueprint.route('/choose_problems/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def choose_problems(tournament_id):
    db_sess = db_session.create_session()
    problems = db_sess.query(Problems).all()
    return render_template('choose_problems.html', title='Chose problems', problems=problems, num=len(problems),
                           tournament_id=tournament_id)


@blueprint.route('/deny')
@login_required
def deny():
    return render_template('deny.html', title='Deny')


@blueprint.route('/position_already_is_in_tournament/<int:tournament_id>')
@login_required
def position_already_is_in_tournament(tournament_id):
    return render_template('position_already_is_in_tournament.html', tournament_id=tournament_id)


@blueprint.route('/problem_already_is_in_tournament/<int:tournament_id>')
@login_required
def problem_already_is_in_tournament(tournament_id):
    return render_template('problem_already_is_in_tournament.html', tournament_id=tournament_id)


@blueprint.route('/tournament/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def show_tournament(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    problems = tournament.problems
    problems_positions = []
    for problem in problems:
        s = (tournament_to_problems.select()
             .where(and_(tournament_to_problems.c.tournament == tournament.id,
                         tournament_to_problems.c.problem == problem.id)))
        p_result = db_sess.execute(s).all()
        problems_positions.append([p_result[0][2], problem])
    problems_positions.sort(key=lambda x: x[0])
    return render_template('show_tournament.html', tournament=tournament, problems=problems_positions,
                           num=len(tournament.problems))


@blueprint.route('/my_tournaments', methods=['GET', 'POST'])
@login_required
def my_tournaments():
    db_sess = db_session.create_session()
    tournaments = db_sess.query(Tournament).filter(Tournament.owner == current_user.id).all()
    tournament_archive = []
    tournament_open = []
    tournament_running = []
    tournament_waiting = []
    for tournament in tournaments:
        if tournament.state == 0:
            tournament_waiting.append(tournament)
        elif tournament.state == 1:
            tournament_open.append(tournament)
        elif tournament.state == 2:
            tournament_running.append(tournament)
        elif tournament.state == 3:
            tournament_archive.append(tournament)
    return render_template('my_tournaments.html', tournaments1=tournament_waiting, num1=len(tournament_waiting),
                           tournaments2=tournament_running, num2=len(tournament_running),
                           tournaments3=tournament_open, num3=len(tournament_open),
                           tournaments4=tournament_archive, num4=len(tournament_archive),
                           title='My tournaments')


@blueprint.route('/delete_problem_from_tournament/<int:tournament_id>/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def delete_problem_from_tournament(tournament_id, problem_id):
    db_sess = db_session.create_session()
    p = tournament_to_problems.delete() \
        .where(and_(tournament_to_problems.c.tournament == tournament_id,
                    tournament_to_problems.c.problem == problem_id))
    db_sess.execute(p)
    db_sess.commit()
    return redirect('/tournament/' + str(tournament_id))


@blueprint.route('/all_tournaments', methods=['GET', 'POST'])
@login_required
def all_tournaments():
    db_sess = db_session.create_session()
    tournaments = db_sess.query(Tournament).filter(Tournament.state == 1).all()
    return render_template('all_tournaments.html', title='Show tournaments',
                           tournaments=tournaments, num=len(tournaments))


@blueprint.route('/add_user_to_tournament/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def add_user_to_tournament(tournament_id):
    if current_user.role < 1:  #только ученики могут участвовать в турнирах
        db_sess = db_session.create_session()
        tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
        if tournament.state == 1:
            s = (users_to_tournaments.select()
                 .where(and_(users_to_tournaments.c.user == current_user.id,
                             users_to_tournaments.c.tournament == tournament_id)))
            u_result = db_sess.execute(s).all()
            if not u_result:
                u = users_to_tournaments.insert().values(user=current_user.id, tournament=tournament_id)
                db_sess.execute(u)
                db_sess.commit()
                return redirect('/student_tournaments')
            return redirect('/you_are_already_in_tournament')
        return redirect('/tournament_base/' + str(tournament_id))
    return redirect('/students_only')


@blueprint.route('/you_are_already_in_tournament', methods=['GET', 'POST'])
@login_required
def you_are_already_in_tournament():
    return render_template('you_are_already_in_tournament.html')


@blueprint.route('/students_only', methods=['GET', 'POST'])
@login_required
def students_only():
    return render_template('students_only.html')


@blueprint.route('/student_tournaments', methods=['GET', 'POST'])
@login_required
def student_tournaments():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    tournament_archive = []
    tournament_running = []
    tournament_open =[]
    for tournament in user.tournaments:
        if tournament.state == 1:
            tournament_open.append(tournament)
        elif tournament.state == 2:
            tournament_running.append(tournament)
        elif tournament.state == 3:
            tournament_archive.append(tournament)
    return render_template('student_tournaments.html',
                           tournament_running=tournament_running, num1=len(tournament_running),
                           tournament_open=tournament_open,num2=len(tournament_open),
                           tournament_archive=tournament_archive, num3=len(tournament_archive))


@blueprint.route('/delete_user_from_tournament/<int:tournament_id>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_user_from_tournament(tournament_id, user_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.state == 1:
        u = users_to_tournaments.delete() \
            .where(and_(users_to_tournaments.c.tournament == tournament_id,
                        users_to_tournaments.c.user == user_id))
        db_sess.execute(u)
        db_sess.commit()
        return redirect('/student_tournaments')
    return redirect('/tournament_base/' + str(tournament_id))


@blueprint.route('/answer/<int:tournament_id>/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def answer(tournament_id, problem_id):
    form = AnswerForm()
    db_sess = db_session.create_session()
    problem = db_sess.query(Problems).filter(Problems.id == problem_id).first()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.state == 2:
        if tournament in user.tournaments:
            u = tournament_set.select().where(and_(tournament_set.c.tournament == tournament_id,
                                                   tournament_set.c.state == current_user.id))
            user_problem = db_sess.execute(u).all()
            p = tournament_to_problems.select() \
                .where(and_(tournament_to_problems.c.tournament == tournament_id,
                            tournament_to_problems.c.problem == problem_id))
            problem_position = db_sess.execute(p).all()
            if user_problem[0][1] == problem_position[0][2]:
                if form.validate_on_submit():
                    s = (users_to_problems.select()
                         .where(and_(users_to_problems.c.user == current_user.id,
                                     users_to_problems.c.problem == problem_id,
                                     users_to_problems.c.tournament == tournament_id)))
                    u_result = db_sess.execute(s).all()
                    tries = u_result[0][4]
                    if problem_position[0][2] == '0-0':
                        if tries == 1:
                            if form.answer.data == problem.answer:
                                print(1)
                                result = 10
                                u = users_to_problems.update().values(result=result) \
                                    .where(and_(users_to_problems.c.user == current_user.id,
                                                users_to_problems.c.problem == problem_id,
                                                users_to_problems.c.tournament == tournament_id))
                                db_sess.execute(u)
                                db_sess.commit()
                                s = (users_to_tournaments.select()
                                     .where(and_(users_to_tournaments.c.user == current_user.id,
                                                 users_to_tournaments.c.tournament == tournament_id)))
                                s_result = db_sess.execute(s).all()
                                score = s_result[0][2] + result
                                u = users_to_tournaments.update().values(score=score) \
                                    .where(and_(users_to_tournaments.c.user == current_user.id,
                                                users_to_tournaments.c.tournament == tournament_id))
                                db_sess.execute(u)
                                db_sess.commit()
                                put_problem(tournament_id, problem_id)
                                return redirect('/right_answer/' + str(tournament_id))
                            u = users_to_problems.update().values(result=0) \
                                .where(and_(users_to_problems.c.user == current_user.id,
                                            users_to_problems.c.problem == problem_id,
                                            users_to_problems.c.tournament == tournament_id))
                            db_sess.execute(u)
                            db_sess.commit()
                            put_problem(tournament_id, problem_id)
                            return redirect('/wrong_answer/' + str(tournament_id))
                        return redirect('/answer_exceed/' + str(tournament_id))
                    if tries == 1:
                        if form.answer.data == problem.answer:
                            result = int(problem_position[0][2][0]) + int(problem_position[0][2][2])
                            u = users_to_problems.update().values(result=result) \
                                .where(and_(users_to_problems.c.user == current_user.id,
                                            users_to_problems.c.problem == problem_id,
                                            users_to_problems.c.tournament == tournament_id))
                            db_sess.execute(u)
                            db_sess.commit()
                            s = (users_to_tournaments.select()
                                 .where(and_(users_to_tournaments.c.user == current_user.id,
                                             users_to_tournaments.c.tournament == tournament_id)))
                            s_result = db_sess.execute(s).all()
                            score = s_result[0][2] + result
                            u = users_to_tournaments.update().values(score=score) \
                                .where(and_(users_to_tournaments.c.user == current_user.id,
                                            users_to_tournaments.c.tournament == tournament_id))
                            db_sess.execute(u)
                            db_sess.commit()
                            put_problem(tournament_id, problem_id)
                            return redirect('/right_answer/' + str(tournament_id))
                        u = users_to_problems.update().values(result=0) \
                            .where(and_(users_to_problems.c.user == current_user.id,
                                        users_to_problems.c.problem == problem_id,
                                        users_to_problems.c.tournament == tournament_id))
                        db_sess.execute(u)
                        db_sess.commit()
                        put_problem(tournament_id, problem_id)
                        return redirect('/wrong_answer/' + str(tournament_id))
                    if form.answer.data == problem.answer:
                        result = max(int(problem_position[0][2][0]), int(problem_position[0][2][2]))
                        u = users_to_problems.update().values(result=result, tries=2) \
                            .where(and_(users_to_problems.c.user == current_user.id,
                                        users_to_problems.c.problem == problem_id))
                        db_sess.execute(u)
                        db_sess.commit()
                        s = (users_to_tournaments.select()
                             .where(and_(users_to_tournaments.c.user == current_user.id,
                                         users_to_tournaments.c.tournament == tournament_id)))
                        s_result = db_sess.execute(s).all()
                        score = s_result[0][2] + result
                        u = users_to_tournaments.update().values(score=score) \
                            .where(and_(users_to_tournaments.c.user == current_user.id,
                                        users_to_tournaments.c.tournament == tournament_id))
                        db_sess.execute(u)
                        db_sess.commit()
                        put_problem(tournament_id, problem_id)
                        return redirect('/right_answer/' + str(tournament_id))
                    result = -min(int(problem_position[0][2][0]), int(problem_position[0][2][2]))
                    u = users_to_problems.update().values(result=result, tries=2) \
                        .where(and_(users_to_problems.c.user == current_user.id,
                                    users_to_problems.c.problem == problem_id))
                    db_sess.execute(u)
                    db_sess.commit()
                    s = (users_to_tournaments.select()
                         .where(and_(users_to_tournaments.c.user == current_user.id,
                                     users_to_tournaments.c.tournament == tournament_id)))
                    s_result = db_sess.execute(s).all()
                    score = s_result[0][2] + result
                    u = users_to_tournaments.update().values(score=score) \
                        .where(and_(users_to_tournaments.c.user == current_user.id,
                                    users_to_tournaments.c.tournament == tournament_id))
                    db_sess.execute(u)
                    db_sess.commit()
                    put_problem(tournament_id, problem_id)
                    return redirect('/wrong_answer/' + str(tournament_id))
                return render_template('answer_form.html', title='Answer', problem=problem, form=form,
                                       tournament=tournament, position=problem_position[0][2])
            return redirect('/show_user_problem/' + str(tournament_id))
        return redirect('/you_are_not_in_tournament')
    return redirect('/tournament_not_in_proper_state')


@blueprint.route('/discard_problem/<int:tournament_id>/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def discard_problem(tournament_id, problem_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.state == 2:
        if tournament in user.tournaments:
            put_problem(tournament_id, problem_id)
            return redirect('/show_free_problems/' + str(tournament_id))
        return redirect('/you_are_not_in_tournament')
    return redirect('/tournament_not_in_proper_state')


@blueprint.route('/tournament_not_in_proper_state/<int:tournament_id>')
@login_required
def tournament_not_in_proper_state(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    return render_template('tournament_not_in_proper_state.html', title='Tournament not in proper state',
                           tournament=tournament)


@blueprint.route('/right_answer/<int:tournament_id>')
@login_required
def right_answer(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    return render_template('right_answer.html', title='Right answer', tournament=tournament)


@blueprint.route('/wrong_answer/<int:tournament_id>')
@login_required
def wrong_answer(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    return render_template('wrong_answer.html', title='Wrong answer', tournament=tournament)


@blueprint.route('/answer_exceed/<int:tournament_id>')
@login_required
def answer_exceed(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    return render_template('answer_exceed.html', title='Answer exceed', tournament=tournament)


@blueprint.route('/have_right_answer/<int:tournament_id>')
@login_required
def have_right_answer(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    return render_template('have_right_answer.html', title='Have right answer', tournament=tournament)


@blueprint.route('/you_are_not_in_tournament')
@login_required
def you_are_not_in_tournament():
    return render_template('you_are_not_in_tournament.html', title='You are not in tournament')


@blueprint.route('/tournament_rating/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def tournament_rating(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    s = (users_to_tournaments.select().where(users_to_tournaments.c.tournament == tournament_id))
    u_result = db_sess.execute(s).all()
    users = []
    for u in u_result:
        user = db_sess.query(User).filter(User.id == u[0]).first()
        users.append([user.surname, user.name, u[2]])
    users.sort(key=lambda x: x[2], reverse=True)
    return render_template('tournament_rating.html', tournament=tournament, users=users,
                           num=len(users), title='Tournament rating')


def tournament_add_positions(tournament_id):
    positions = ['0-0', '0-1', '0-2', '0-3', '0-4', '0-5', '0-6', '1-1', '1-2', '1-3',
                 '1-4', '1-5', '1-6', '2-2', '2-3', '2-4', '2-5', '2-6', '3-3', '3-4',
                 '3-5', '3-6', '4-4', '4-5', '4-6', '5-5', '5-6', '6-6']
    db_sess = db_session.create_session()
    s = (users_to_tournaments.select().where(users_to_tournaments.c.tournament == tournament_id))
    u_result = db_sess.execute(s).all()
    n = (len(u_result) + 9) // 10   # на каждые 10 участников добавляется комплект задач
    for j in range(n):
        for i in range(28):
            t = tournament_set.insert().values(tournament=tournament_id, position=positions[i], state=0)
            db_sess.execute(t)
            db_sess.commit()


@blueprint.route('/get_problem/<int:tournament_id>/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def get_problem(tournament_id, problem_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    if tournament.state == 2:
        if tournament in user.tournaments:
            s = tournament_to_problems.select() \
                .where(and_(tournament_to_problems.c.tournament == tournament_id,
                            tournament_to_problems.c.problem == problem_id))
            p_result = db_sess.execute(s).all()
            position = p_result[0][2]
            s = tournament_set.select().where(and_(tournament_set.c.tournament == tournament_id,
                                                   tournament_set.c.position == position, tournament_set.c.state == 0))
            s_result = db_sess.execute(s).all()
            s = users_to_problems.select() \
                .where(and_(users_to_problems.c.tournament == tournament_id,
                            users_to_problems.c.problem == problem_id,
                            users_to_problems.c.user == current_user.id))
            u_result = db_sess.execute(s).all()
            s = tournament_set.select().where(and_(tournament_set.c.tournament == tournament_id,
                                                   tournament_set.c.state == current_user.id))
            user_problems = db_sess.execute(s).all()
            if len(user_problems) > 0:
                return redirect('/show_user_problem/' + str(tournament_id))
            if u_result:
                tries = u_result[0][4]
                result = u_result[0][3]
                if result > 0:
                    return redirect('/have_right_answer/' + str(tournament_id))
                if tries > 1:
                    return redirect('/answer_exceed/' + str(tournament_id))
                if tries == 1 and position == '0-0':
                    return redirect('/answer_exceed/' + str(tournament_id))
            if not s_result:
                return redirect('/show_free_problems/' + str(tournament_id))
            line_id = s_result[0][3]
            u = tournament_set.update().values(state=current_user.id).where(tournament_set.c.id == line_id)
            db_sess.execute(u)
            db_sess.commit()
            if not u_result:
                p = users_to_problems.insert().values(user=current_user.id, problem=problem_id,
                                                      tournament=tournament_id, tries=1)
            else:
                p = users_to_problems.update().values(tries=2) \
                    .where(and_(users_to_problems.c.tournament == tournament_id,
                                users_to_problems.c.problem == problem_id,
                                users_to_problems.c.user == current_user.id))
            db_sess.execute(p)
            db_sess.commit()
            return redirect('/show_user_problem/' + str(tournament_id))
        return redirect('/tournament_base/' + str(tournament_id))
    return redirect('/tournament_base/' + str(tournament_id))


@blueprint.route('/put_problem/<int:tournament_id>/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def put_problem(tournament_id, problem_id):
    db_sess = db_session.create_session()
    s = tournament_to_problems.select() \
        .where(and_(tournament_to_problems.c.tournament == tournament_id,
                    tournament_to_problems.c.problem == problem_id))
    p_result = db_sess.execute(s).all()
    position = p_result[0][2]
    s = tournament_set.select().where(and_(tournament_set.c.tournament == tournament_id,
                                           tournament_set.c.position == position,
                                           tournament_set.c.state == current_user.id))
    s_result = db_sess.execute(s).all()
    if s_result:
        u = tournament_set.update().values(state=0).where(and_(tournament_set.c.tournament == tournament_id,
                                                               tournament_set.c.state == current_user.id,
                                                               tournament_set.c.position == position))
        db_sess.execute(u)
        db_sess.commit()


@blueprint.route('/show_user_problem/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def show_user_problem(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    p = tournament_set.select().where(and_(tournament_set.c.tournament == tournament_id,
                                           tournament_set.c.state == current_user.id))
    p_result = db_sess.execute(p).all()
    if not p_result:
        return redirect('/tournament_base/' +str(tournament_id))
    position = p_result[0][1]
    s = tournament_to_problems.select() \
        .where(and_(tournament_to_problems.c.tournament == tournament_id,
                    tournament_to_problems.c.position == position))
    p_result = db_sess.execute(s).all()
    problem_id = p_result[0][1]
    problem = db_sess.query(Problems).filter(Problems.id == problem_id).first()
    return render_template('show_user_problem.html', problem=problem, position=position, tournament_id=tournament_id,
                           tournament=tournament)


@blueprint.route('/show_free_problems/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def show_free_problems(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    s = (tournament_set.select()
         .where(tournament_set.c.tournament == tournament_id,
                tournament_set.c.state == 0))
    p_result = db_sess.execute(s).all()
    problems_positions = []
    for p in p_result:
        s = (tournament_to_problems.select()
             .where(and_(tournament_to_problems.c.tournament == tournament_id,
                         tournament_to_problems.c.position == p[1])))
        s_result = db_sess.execute(s).all()
        problem_id = s_result[0][1]
        problem = db_sess.query(Problems).filter(Problems.id == problem_id).first()
        problems_positions.append([p[1], problem])
    problems_positions.sort(key=lambda x: x[0])
    return render_template('show_free_problems.html', problems=problems_positions, tournament_id=tournament_id,
                           num=len(problems_positions), tournament=tournament)


@blueprint.route('/create_tournament/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def create_tournament(tournament_id):
    form = CreateTournamentForm()
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.owner == current_user.id:
        if tournament.state == 0:
            if form.validate_on_submit():
                tournament.start_date = form.start_date.data
                tournament.end_date = form.end_date.data
                tournament.state = 1
                db_sess.commit()
                tournament_timer(tournament_id)
                return redirect('/')
            return render_template('create_tournament_form.html', form=form, title='Create tournament')
        return redirect('/tournament_base/' + str(tournament_id))
    return redirect('/deny')


def start_tournament(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.state == 1:
        tournament_add_positions(tournament_id)
        push_problems(tournament_id)
        tournament.state = 2
        db_sess.commit()


def end_tournament(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.state == 2:
        tournament.state = 3
        db_sess.commit()


@blueprint.route('/tournament_base/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def tournament_base(tournament_id):
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.state == 0:
        return redirect('/tournament/' + str(tournament_id))
    return render_template('tournament_base.html', tournament=tournament)


@blueprint.route('/tournaments_archive', methods=['GET', 'POST'])
@login_required
def tournaments_archive():
    db_sess = db_session.create_session()
    tournaments = db_sess.query(Tournament).filter(Tournament.state == 3).all()
    return render_template('tournaments_archive.html', title='Tournaments archive',
                           tournaments=tournaments, num=len(tournaments))


@blueprint.route('/tournament_table/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
def tournament_table(tournament_id):
    positions = ['0-0', '0-1', '0-2', '0-3', '0-4', '0-5', '0-6', '1-1', '1-2', '1-3',
                 '1-4', '1-5', '1-6', '2-2', '2-3', '2-4', '2-5', '2-6', '3-3', '3-4',
                 '3-5', '3-6', '4-4', '4-5', '4-6', '5-5', '5-6', '6-6']
    positions2 = ['0 0', '0 1', '0 2', '0 3', '0 4', '0 5', '0 6', '1 1', '1 2', '1 3',
                  '1 4', '1 5', '1 6', '2 2', '2 3', '2 4', '2 5', '2 6', '3 3', '3 4',
                  '3 5', '3 6', '4 4', '4 5', '4 6', '5 5', '5 6', '6 6']
    tournament_table = []
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament.state > 1:
        s = users_to_tournaments.select().where(users_to_tournaments.c.tournament == tournament_id)
        users = db_sess.execute(s).all()
        for u in users:
            user = db_sess.query(User).filter(User.id == u[0]).first()
            score = u[2]
            user_results = [user]
            s = tournament_set.select().where(and_(tournament_set.c.tournament == tournament_id,
                                                   tournament_set.c.state == user.id))
            s_result = db_sess.execute(s).all()
            if not s_result:
                user_position = ''
            else:
                user_position = s_result[0][1]
            for position in positions:
                s = tournament_to_problems.select().where(and_(tournament_to_problems.c.tournament == tournament_id,
                                                               tournament_to_problems.c.position == position))
                p_result = db_sess.execute(s).all()
                problem_id = p_result[0][1]
                s = users_to_problems.select().where(and_(users_to_problems.c.tournament == tournament_id,
                                                          users_to_problems.c.user == user.id,
                                                          users_to_problems.c.problem == problem_id))
                u_result = db_sess.execute(s).all()
                if not u_result:
                    user_results.append(['', ''])
                else:
                    if user_position == position:
                        user_results.append(['', ''])
                    else:
                        result = u_result[0][3]
                        tries = u_result[0][4]
                        user_results.append([result, tries])
            user_results.append(score)
            tournament_table.append(user_results)
        tournament_table.sort(key=lambda x: x[29], reverse=True)
        return render_template('tournament_table.html', title='Tournament table', tournament=tournament,
                               tournament_table=tournament_table, num=len(tournament_table), positions=positions2)
    return redirect('/tournament_base/' + str(tournament_id))


def push_problems(tournament_id):
    positions1 = ['0-1', '0-2', '0-3', '0-4', '0-5', '1-1', '1-2', '1-3', '1-4', '2-2']
    positions = []
    db_sess = db_session.create_session()
    s = users_to_tournaments.select().where(users_to_tournaments.c.tournament == tournament_id)
    users = db_sess.execute(s).all()
    n = (len(users) + 9) // 10
    for i in range(n):
        for p in positions1:
            positions.append(p)
    for i in range(len(users)):
        s = tournament_set.select().where(and_(tournament_set.c.tournament == tournament_id,
                                               tournament_set.c.position == positions[i], tournament_set.c.state == 0))
        s_result = db_sess.execute(s).all()
        line_id = s_result[0][3]
        user_id = users[i][0]
        u = tournament_set.update().values(state=user_id).where(tournament_set.c.id == line_id)
        db_sess.execute(u)
        db_sess.commit()
        s = tournament_to_problems.select().where(and_(tournament_to_problems.c.tournament == tournament_id,
                                                       tournament_to_problems.c.position == positions[i]))
        p_result = db_sess.execute(s).all()
        problem_id = p_result[0][1]
        p = users_to_problems.insert().values(user=user_id, problem=problem_id,
                                              tournament=tournament_id, tries=1)
        db_sess.execute(p)
        db_sess.commit()


def tournament_timer(tournament_id):
    global scheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(func=check_time, trigger="interval", seconds=30, id=str(tournament_id), args=[tournament_id])
    scheduler.start()


def check_time(tournament_id):
    global scheduler
    db_sess = db_session.create_session()
    tournament = db_sess.query(Tournament).filter(Tournament.id == tournament_id).first()
    dt = datetime.datetime.now()
    if int(dt.strftime("%Y%m%d%H%M")) == int(tournament.start_date.strftime("%Y%m%d%H%M")):
        start_tournament(tournament_id)
    elif int(dt.strftime("%Y%m%d%H%M")) == int(tournament.end_date.strftime("%Y%m%d%H%M")):
        end_tournament(tournament_id)
        scheduler.remove_job(str(tournament_id))
