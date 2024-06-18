import logging
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service
from src.config.config import config

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# async def send_email(*args, **kwargs):
async def send_email(email, username, link, templates, host, *rest):
    # email, username, link, templates, *rest = kwargs.values()
    # print(f"-----____________________!!!!kwargs: {kwargs=}")
    # print(f"{email=} {username=} {link=} {templates=} {host=}")
    try:
        # token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={
                "link": link,
                "username": username,
                # "link": link,
                # "token": token_verification,
            },
            subtype=MessageType.html,
        )
        print(f"{conf=}")
        fm = FastMail(conf)
        await fm.send_message(message, template_name=templates)
        logging.info(f"Message sent to {email=}")
    except ConnectionErrors as err:
        logging.error(f"Failed to send email to {email}: {err}")
        # print(err)


# TODO : сделать функцию подтверждения email
async def send_confirm_email(**kwargs):
    token_verification = auth_service.create_email_token({"sub": kwargs.get("email")})
    kwargs["link"] = (
        f'{kwargs.get("host")}api/auth/confirmed_email/{token_verification}'
    )
    kwargs["templates"] = "verify_email.html"
    print(f"-----____________________!!!!kwargs: {kwargs=}")
    await send_email(**kwargs)


# TODO : сделать функцию отправки на email ссылки для сброса пароля
async def send_email_reset_password(**kwargs):
    token_verification = auth_service.create_email_token({"sub": kwargs.get("email")})
    kwargs["link"] = (
        f'{kwargs.get("host")}api/auth/confirmed_email/{token_verification}'
    )
    kwargs["templates"] = "verify_email.html"
    print(f"-----____________________!!!!kwargs: {kwargs=}")
    await send_email(**kwargs)
