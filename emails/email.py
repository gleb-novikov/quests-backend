from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from config.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    TEMPLATE_FOLDER='./templates/email'
)


async def send_activation_email(email_to: str, body: dict):
    message = MessageSchema(
        subject='Активация аккаунта',
        recipients=[email_to],
        template_body=body,
        subtype='html',
    )
    fast_mail = FastMail(conf)
    await fast_mail.send_message(message, template_name='activation.html')


async def send_reset_email(email_to: str, body: dict):
    message = MessageSchema(
        subject='Сброс пароля',
        recipients=[email_to],
        template_body=body,
        subtype='html',
    )
    fast_mail = FastMail(conf)
    await fast_mail.send_message(message, template_name='reset.html')
