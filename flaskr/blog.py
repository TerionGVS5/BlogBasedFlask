from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, rating'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True, estimate=False):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, rating'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if not estimate and check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/like', methods=('POST',))
@login_required
def like(id):
    get_post(id, estimate=True)
    id_user = g.user['id']
    db = get_db()
    exp = db.execute('SELECT mark FROM user_marks WHERE id_post = ? and id_user = ?', (id, id_user)).fetchone()
    if exp is None:
        db.execute('INSERT INTO user_marks (id_post, id_user, mark) VALUES (?, ?, ?) ', (id, id_user, 1))
        db.commit()
        db.execute(
            'UPDATE post SET rating = rating + 1 WHERE id = ?', (id, ))
        db.commit()
    elif exp['mark'] == 1:
        flash('You already liked this post.')
    elif exp['mark'] == -1:
        db.execute('DELETE FROM user_marks WHERE id_post = ? and id_user = ?', (id, id_user))
        db.commit()
        db.execute('UPDATE post SET rating = rating + 1 WHERE id = ?', (id,))
        db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/dislike', methods=('POST',))
@login_required
def dislike(id):
    get_post(id, estimate=True)
    id_user = g.user['id']
    db = get_db()
    exp = db.execute('SELECT mark FROM user_marks WHERE id_post = ? and id_user = ?', (id, id_user)).fetchone()
    if exp is None:
        db.execute('INSERT INTO user_marks (id_post, id_user, mark) VALUES (?, ?, ?) ', (id, id_user, -1))
        db.commit()
        db.execute(
            'UPDATE post SET rating = rating - 1 WHERE id = ?', (id, ))
        db.commit()
    elif exp['mark'] == -1:
        flash('You already disliked this post.')
    elif exp['mark'] == 1:
        db.execute('DELETE FROM user_marks WHERE id_post = ? and id_user = ?', (id, id_user))
        db.commit()
        db.execute('UPDATE post SET rating = rating - 1 WHERE id = ?', (id,))
        db.commit()
    return redirect(url_for('blog.index'))
