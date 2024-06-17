import logging
from typing import Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Depends,
    Request,
    status,
    Security,
)

# from fastapi.responses import FileResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    OAuth2PasswordRequestForm,
    HTTPBearer,
)
from fastapi_limiter.depends import RateLimiter

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.email import send_email
from src.database.db import get_db

# from src.entity.models import Todo
from src.repositories import users as repositories_users
from src.schemas.user import RequestEmail, UserSchema, UserResponse, TokenSchema
from src.services.auth import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])

get_refresh_token = HTTPBearer()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post(
    "/signup",
    response_model=Optional[UserResponse],
    status_code=status.HTTP_201_CREATED,
    # dependencies=[Depends(RateLimiter(times=2, seconds=60))],
)
async def signup(
    body: UserSchema,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Sign up a new user.

    :warning: This function should be called with caution, as it may raise an :class:`HTTPException` if the user already exists.

    This function handles the HTTP POST request to the "/signup" endpoint. It creates a new user account by
    validating the provided user data and adding it to the database. If the user already exists, it raises an
    :class:`HTTPException` with a status code of 409.

    :param body: The user data to be used for creating the new user account.
    :type body: :class:`UserSchema`
    :param bt: An instance of the :class:`BackgroundTasks` class used for scheduling background tasks.
    :type bt: :class:`BackgroundTasks`
    :param request: The incoming request object.
    :type request: :class:`Request`
    :param db: An instance of the :class:`AsyncSession` class used for database operations.
    :type db: :class:`AsyncSession`
    :return: The newly created user account, or :const:`None` if the user already exists.
    :rtype: :class:`Optional[:class:`UserResponse`]`
    :raises HTTPException: If the user already exists.

    :dependencies:
        - :class:`RateLimiter`: A rate limiter dependency that limits the number of requests to this endpoint within a
          specified time period.
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.add_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))

    # print()
    # new_user = User(
    #     email=body.username, password=hash_handler.get_password_hash(body.password)
    # )

    return new_user


@router.post("/login", response_model=Optional[TokenSchema])
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Handles the login request for the user.

    This function is responsible for authenticating the user and generating JWT tokens for access and refresh purposes.
    It expects a POST request to the "/login" endpoint with the following parameters:

    :param body: An instance of `OAuth2PasswordRequestForm` containing the user's email and password.
    :type body: OAuth2PasswordRequestForm
    :param db: An instance of `AsyncSession` for accessing the database.
    :type db: AsyncSession

    :return: A dictionary containing the generated access token, refresh token, and token type.
    :rtype: dict

    :raises HTTPException: with status code 401 and detail "Invalid email" if the user is not found.
    :raises HTTPException: with status code 401 and detail "Invalid password" if the password is incorrect.

    :dependencies:
        - `repositories_users.get_user_by_email` for retrieving the user by email.
        - `auth_service.create_access_token` for generating the access token.
        - `auth_service.create_refresh_token` for generating the refresh token.
        - `repositories_users.update_token` for updating the user's token in the database.
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    # user = db.query(User).filter(User.email == body.username).first()
    if user is None:
        logger.error("User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not auth_service.verify_password(body.password, user.password):
        logger.error("password incorrect")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh_token", response_model=Optional[TokenSchema])
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Refreshes the access and refresh tokens for the authenticated user.

    This function is responsible for refreshing the access and refresh tokens for the authenticated user. It expects a POST request to the "/refresh_token" endpoint with the following parameters:

    :param credentials: An instance of `HTTPAuthorizationCredentials` containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: An instance of `AsyncSession` for accessing the database.
    :type db: AsyncSession

    :return: A dictionary containing the refreshed access token, refresh token, and token type.
    :rtype: dict

    :raises HTTPException: with status code 401 and detail "Invalid refresh token" if the refresh token is invalid or expired.

    :dependencies:
        - `auth_service.decode_refresh_token` for decoding the refresh token.
        - `repositories_users.get_user_by_email` for retrieving the user by email.
        - `auth_service.create_access_token` for generating the access token.
        - `auth_service.create_refresh_token` for generating the refresh token.
        - `repositories_users.update_token` for updating the user's token in the database.
    """
    print(credentials.credentials)
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/request_email/{email}")
async def resend_request_email(
    email: str,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint to resend the email confirmation request for a specific email address.

    :param email: The email address for which the confirmation request is being resent.
    :type email: str
    :param bt: An instance of the BackgroundTasks class for handling background tasks.
    :type bt: BackgroundTasks
    :param request: The incoming request object.
    :type request: Request
    :param db: An instance of the AsyncSession class for asynchronous database operations.
    :type db: AsyncSession
    :return: A message indicating the status of the email confirmation request.
    :rtype: dict
    """
    user = await repositories_users.get_user_by_email(email, db)

    if user.is_verified:
        return {"message": "Your email is already confirmed"}
    if user:
        bt.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint to request an email confirmation for a specific email address.

    :param body: The request body containing the email address.
    :type body: RequestEmail
    :param bt: An instance of the BackgroundTasks class for handling background tasks.
    :type bt: BackgroundTasks
    :param request: The incoming request object.
    :type request: Request
    :param db: An instance of the AsyncSession class for asynchronous database operations.
    :type db: AsyncSession
    :return: A dictionary containing a message indicating the status of the email confirmation request.
    :rtype: dict
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.is_verified:
        return {"message": "Your email is already confirmed"}
    if user:
        bt.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms the email of a user by verifying the token provided in the URL.

    :param token: The token received in the URL to confirm the email.
    :type token: str
    :param db: An instance of the AsyncSession class for accessing the database.
    :type db: AsyncSession
    :return: A dictionary with a message indicating the status of the email confirmation.
    :rtype: dict
    :raises HTTPException: with status code 400 and detail "Verification error" if the user is not found.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    print(user)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.is_verified:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirm_email(email, db)
    print("ok confirmed")
    return {"message": "Email confirmed"}


# @router.get("/{username}")
# async def confirm_open_email(
#     username: str, response: Response, db: AsyncSession = Depends(get_db)
# ):
#     print("-----------------------------------")
#     print(f"{username} письмо было открыто")
#     return FileResponse(
#         "src/static/pixel.png",
#         media_type="image/png",
#         content_disposition_type="inline",
#     )
