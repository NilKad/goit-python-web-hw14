import pickle
import cloudinary
import cloudinary.uploader

from typing import Optional
from fastapi import (
    APIRouter,
    File,
    Depends,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.schemas.user import UserResponse
from src.models.models import User

from src.services.auth import auth_service

from src.database.db import get_db
from src.config.config import config
from src.repositories import users as repositories_users

router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_KEY,
    api_secret=config.CLOUDINARY_SECRET,
    secure=True,
)


@router.get(
    "/me",
    response_model=Optional[UserResponse],
    dependencies=[Depends(RateLimiter(times=2, seconds=10))],
)
async def get_current_uesr(user: User = Depends(auth_service.get_current_user)):
    """
    Get the current user.

    :return: The current user object.
    :rtype: Optional[UserResponse]
    :depends: The current user is obtained from the authentication service using the `auth_service.get_current_user` dependency.
    :rate-limited: The route is protected by a rate limiter that allows a maximum of 2 requests per 10 seconds.
    """
    return user


@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=2, seconds=20))],
)
async def set_user_avatar(
    file: UploadFile = File(),
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A function to set the user's avatar by uploading the file to Cloudinary, updating the user's avatar URL, and caching the user data.

    :param file: The file to be uploaded as the user's avatar.
    :type file: UploadFile, optional
    :param user: The current user object.
    :type user: User, optional
    :param db: The asynchronous database session.
    :type db: AsyncSession, optional
    :return: The updated user object after setting the avatar.
    :rtype: User
    """
    public_id = f"web21/{user.email}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    print(f"cloudinary res: {res}")
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = await repositories_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user
