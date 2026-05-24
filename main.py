from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models import registry, Ticket

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret'

TICKET_CATALOG = {
    'std': {'kind': 'Стандарт', 'name': 'Стандартный билет',
            'desc': 'Свободный вход в постоянную экспозицию в любой день.', 'price': 600},
    'exh': {'kind': 'Выставка', 'name': 'Билет на выставку',
            'desc': 'Полный доступ ко всем выставкам сезона.', 'price': 1400},
    'vip': {'kind': 'VIP', 'name': 'VIP билет',
            'desc': 'Экскурсия с куратором, доступ в фонды и закрытые залы.', 'price': 4800},
}

TICKET_STYLES = {
    'Стандартный билет': 's-red',
    'Билет на выставку': 's-blue',
    'VIP билет': 's-black',
}

ARCHETYPES = [
    {'name': 'Архетип семьи', 'desc': 'Тёплый круг родового тепла',
     'bg': 'linear-gradient(135deg,#6b4a2a 0%,#2a1a0e 100%)'},
    {'name': 'Архетип любви', 'desc': 'Жест, обещание и кольцо',
     'bg': 'linear-gradient(135deg,#4a2818 0%,#1a0f06 100%)'},
    {'name': 'Архетип мужества', 'desc': 'Воин на пороге битвы',
     'bg': 'linear-gradient(135deg,#5a2818 0%,#2a0e0e 100%)'},
    {'name': 'Архетип братства', 'desc': 'Один шаг — общее дело',
     'bg': 'linear-gradient(135deg,#3a2818 0%,#1a0a04 100%)'},
    {'name': 'Архетип кошачий', 'desc': 'Тишина, изящество, шёпот лап',
     'bg': 'linear-gradient(135deg,#4a3a1a 0%,#1a1408 100%)'},
]

OTHER_CARDS = [
    {'t': 'Расписание', 'd': 'Ежедневно, кроме вторника. С 10:00 до 22:00'},
    {'t': 'Как добраться', 'd': 'ул. Парадная, 12. Корпус «А», подъезд с колоннадой'},
    {'t': 'Магазин', 'd': 'Каталоги выставок, репродукции, открытки и сувениры'},
    {'t': 'Лекторий', 'd': 'Программа лекций и образовательных встреч'},
    {'t': 'Экскурсии', 'd': 'Авторские маршруты с куратором выставки'},
    {'t': 'Контакты', 'd': '+7 (000) 000 00 00 · hello@galereya.ru'},
]


def current_user():
    uid = session.get('user_id')
    return registry.get(uid) if uid else None


def send_password_email(to_email, login_password):
    smtp_server = 'smtp.gmail.com'
    port = 587
    sender_email = "egorskurenkov391@gmail.com"
    password = "sgvf tpfb nxop lqbh"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "Пароль от вашего аккаунта"
    msg.attach(MIMEText(f"Ваш пароль: {login_password}", 'plain'))
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False


@app.route('/')
@app.route('/yar_galery/')
@app.route('/yar_galery/home/')
def home():
    return render_template(
        'home.html',
        section=request.args.get('section'),
        archetypes=ARCHETYPES,
        other_cards=OTHER_CARDS,
    )


@app.route('/yar_galery/buy_ticket/')
def buy_ticket():
    return render_template('buy_ticket.html', tickets=TICKET_CATALOG)


@app.route('/yar_galery/tour/')
def tour():
    rooms = ['Парадный №1', 'Восточное крыло', 'Скульптурный', 'Колоннада', 'Лекторий', 'Закрытый №12']
    return render_template('tour.html', rooms=rooms)


@app.route('/yar_galery/account/')
def account():
    user = current_user()
    if not user:
        return redirect(url_for('home'))
    tab = request.args.get('tab', 'tickets')
    edit = bool(request.args.get('edit'))
    return render_template(
        'account.html',
        user=user, tab=tab, edit=edit,
        ticket_styles=TICKET_STYLES,
    )


@app.route('/yar_galery/order/', methods=['POST'])
def order():
    user = current_user()
    if not user:
        return {'error': 'Пользователь не авторизован'}, 401
    data = request.get_json() or {}
    key = data.get('ticket_key', 'exh')
    info = TICKET_CATALOG.get(key)
    if not info:
        return {'error': 'Неверный тип билета'}, 400
    try:
        qty = max(1, int(data.get('quantity', 1)))
    except (TypeError, ValueError):
        return {'error': 'Неверное количество'}, 400
    date = (data.get('date') or '').strip()
    time = (data.get('time') or '').strip()
    if not date:
        return {'error': 'Укажите дату'}, 400

    ticket = Ticket(
        ticket_type=info['name'],
        date=f"{date} {time}".strip(),
        quantity=qty,
        price=info['price'] * qty,
        qr=str(uuid.uuid4())[:4].upper(),
    )
    user.add_ticket(ticket)
    registry.save()
    flash('Билет приобретён', 'ok')
    return {'ok': True}, 200


@app.route('/yar_galery/ticket/<int:idx>/delete/', methods=['POST'])
def delete_ticket(idx):
    user = current_user()
    if not user:
        return redirect(url_for('home'))
    user.remove_ticket(idx)
    registry.save()
    flash('Билет удалён', 'ok')
    return redirect(url_for('account'))


@app.route('/yar_galery/ticket/change/', methods=['POST'])
def change_ticket():
    user = current_user()
    if not user:
        return redirect(url_for('home'))
    try:
        idx = int(request.form.get('idx'))
    except (TypeError, ValueError):
        return redirect(url_for('account'))
    new_type = request.form.get('new_type')
    if 0 <= idx < len(user.tickets) and new_type:
        t = user.tickets[idx]
        new_price = next((v['price'] for v in TICKET_CATALOG.values() if v['name'] == new_type), t.price)
        updated = Ticket(
            ticket_type=new_type, date=t.date, quantity=t.quantity,
            price=new_price * t.quantity, qr=t.qr,
        )
        user.update_ticket(idx, updated)
        registry.save()
        flash('Тип билета изменён', 'ok')
    return redirect(url_for('account'))


@app.route('/yar_galery/profile/update/', methods=['POST'])
def update_profile():
    user = current_user()
    if not user:
        return redirect(url_for('home'))
    fields = {
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'email': request.form.get('email'),
    }
    pwd = request.form.get('password')
    if pwd:
        fields['password'] = pwd
    registry.update_profile(user.id, **fields)
    flash('Данные обновлены', 'ok')
    return redirect(url_for('account', tab='profile'))


@app.route('/yar_galery/login/', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    if not email or not password:
        return {'error': 'Заполните все поля'}, 400
    user = registry.authenticate(email, password)
    if not user:
        return {'error': 'Неверный email или пароль'}, 401
    session['user_id'] = user.id
    session['username'] = f"{user.first_name} {user.last_name}"
    session['user_email'] = user.email
    return {'ok': True}, 200


@app.route('/yar_galery/register/', methods=['POST'])
def register():
    data = request.get_json() or {}
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    if not all([first_name, last_name, email, password]):
        return {'error': 'Заполните все поля'}, 400
    user = registry.add(first_name, last_name, email, password)
    if not user:
        return {'error': 'Пользователь с таким email уже существует'}, 400
    session['user_id'] = user.id
    session['username'] = f"{user.first_name} {user.last_name}"
    session['user_email'] = user.email
    return {'ok': True}, 200


@app.route('/yar_galery/resetPassword/', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    email = (data.get('email') or '').strip()
    if not all([first_name, last_name, email]):
        return {'error': 'Заполните все поля'}, 400
    pwd = registry.reset_password_lookup(first_name, last_name, email)
    if not pwd:
        return {'error': 'Пользователь не найден'}, 404
    if send_password_email(email, pwd):
        return {'ok': True}, 200
    return {'error': 'Ошибка отправки письма'}, 500


@app.route('/yar_galery/logout/')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
