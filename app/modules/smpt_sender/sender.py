import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config._settings import settings


async def email_sender(
    email: str,
    subject: str,
    body_text: str,
):
    server = smtplib.SMTP_SSL(host='smtp.yandex.ru')
    msg = MIMEMultipart()

    message = body_text

    # параметры сообщения
    password = settings.SMTP_PASSWORD
    msg['From'] = "Sandr.2004@yandex.ru"
    msg['To'] = email
    msg['Subject'] = subject

    # Тело сообщения
    msg.attach(MIMEText(message, 'plain'))

    # Логин
    server.login("Sandr.2004@yandex.ru", password)
    server.auth_plain()

    # Отправка
    server.sendmail("Sandr.2004@yandex.ru", msg['To'], msg.as_string())

    server.quit()


