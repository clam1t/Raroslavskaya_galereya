import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from db import db

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret'

@app.route('/')
@app.route('/yar_galery/')
@app.route('/yar_galery/home/')
def home():
    return render_template('home.html')

@app.route('/yar_galery/logout/')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/yar_galery/buy_ticket/')
def buy_ticket():
    return render_template('home.html')



@app.route('/yar_galery/register/')
def register():
    return render_template('register.html')

@app.route('/yar_galery/home/login/', methods=['POST'])
def login():
    first_name = request.form['first_name']
    second_name = request.form['second_name']
    password = request.form['password']
    if not all([first_name, second_name, password]):
        return redirect(url_for('login_page', error='Заполните все поля'))

    user = db.con.execute(
        'SELECT id '
        'FROM users '
        'WHERE first_name = ? AND second_name = ? AND password = ?',
        (first_name, second_name, password)
    ).fetchone()
    if user:
        session['username'] = f"{first_name} {second_name}"
        session['user_id'] = user['id']
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login_page', error='Неверные данные'))



if __name__ == '__main__':
    app.run(debug=True)
