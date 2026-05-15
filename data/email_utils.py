import random
import string
from datetime import datetime, timedelta
from threading import Thread

from flask_mail import Message, Mail


def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def send_async_email(app, msg):
    with app.app_context():
        mail = Mail()
        mail.init_app(app)
        mail.send(msg)


def send_verification_email(app, user_email, code):
    subject = "Подтверждение регистрации — BuySell"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #2f2448; border-radius: 8px; background-color: #171124;">
        <h2 style="color: #8b5cf6;">Добро пожаловать в BuySell!</h2>
        <p style="font-size: 16px;">Ваш код подтверждения:</p>
        <div style="font-size: 32px; font-weight: bold; text-align: center; padding: 20px; background-color: #130f1f; border-radius: 8px; letter-spacing: 5px; color: #8b5cf6;">
            {code}
        </div>
        <p style="font-size: 14px; color: #c7bbdf; margin-top: 20px;">Код действителен в течение 10 минут.</p>
        <p style="font-size: 12px; color: #9389af;">Если вы не регистрировались в BuySell, просто проигнорируйте это письмо.</p>
    </div>
    """

    msg = Message(subject=subject, recipients=[user_email], html=html)

    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()


def save_verification_code(user, db_sess):
    code = generate_verification_code()
    user.email_verification_code = code
    user.email_verification_expires = datetime.now() + timedelta(minutes=10)
    db_sess.commit()
    return code


def verify_code(user, input_code):
    if not user.email_verification_code:
        return False, "Код не был отправлен"

    if user.email_verification_expires < datetime.now():
        return False, "Срок действия кода истёк. Запросите новый код"

    if user.email_verification_code != input_code:
        return False, "Неверный код подтверждения"

    if user.confirmed:
        return False, "Email уже подтверждён"

    return True, "OK"