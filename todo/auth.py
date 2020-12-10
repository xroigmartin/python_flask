import functools
from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect
)
from werkzeug.security import check_password_hash, generate_password_hash
from todo.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register' , methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db, cursor = get_db()
        error =  None
        cursor.execute(
            'select id from user where username = %s', (username,)
        )
        if not username:
            error = 'Username is required'
        if not password:
            error = 'Password is required'
        elif cursor.fetchone() is not None:
            error = 'User {} exists'.format(username)
        
        if error is None:
            cursor.execute(
                'insert into user (username, password) values (%s, %s)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)
    
    return render_template('auth/register.html')

@bp.route('login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db, cursor = get_db()
        error = None

        cursor.execute(
            'select * from user where username = %s', (username,)
        )

        user = cursor.fetchone()

        if user is None:
            error = 'User or password incorrect'
        elif not check_password_hash(user['password'], password):
            error = 'User or password incorrect'
        
        if error == None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('todo.index'))
        
        flash(error)
    
    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        db, cursor = get_db()

        cursor.execute(
            'select * from user where id = %s', (user_id,)
        )

        g.user = cursor.fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))