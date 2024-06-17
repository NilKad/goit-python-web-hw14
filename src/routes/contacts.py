from datetime import datetime, timedelta
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User
from src.schemas.contact import (
    ContactResponse,
    ContactSchema,
)
from src.database.db import get_db
from src.services.auth import auth_service


from src.repositories import contacts as repositories_contact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/search", response_model=list[ContactResponse])
async def search_contacts(
    first_name: str = Form(None),
    last_name: str = Form(None),
    email: str = Form(None),
    limit: int = Query(10, ge=10, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Search for contacts based on the given filters and return a list of Contact objects.

    :param first_name: The first name to search for.
    :type first_name: str
    :param last_name: The last name to search for.
    :type last_name: str
    :param email: The email to search for.
    :type email: str
    :param limit: The maximum number of contacts to retrieve.
    :type limit: int
    :param offset: The number of contacts to skip before starting to retrieve.
    :type offset: int
    :param db: The database session for executing the query.
    :type db: AsyncSession
    :param user: The user for which to retrieve contacts.
    :type user: User
    :return: A list of Contact objects that match the search criteria.
    :rtype: List[Contact]
    """
    filters = {}
    if first_name:
        filters["first_name"] = first_name
    if last_name:
        filters["last_name"] = last_name
    if email:
        filters["email"] = email
    # print(f"router contacts search filter = {filter}")
    contacts = await repositories_contact.search_contacts(
        filters, limit, offset, db, user
    )
    print(f"return from function {contacts=}")
    return contacts


# search_contacts_next_birthday
@router.get("/next_birthday", response_model=list[ContactResponse])
async def next_birthday(
    next_day: int = 7,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Retrieves contacts whose birthday matches the next specified number of days within the database.

    :param next_day: The number of days to search for contacts with matching birthdays. Defaults to 7.
    :type next_day: int
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object for whom to find contacts with matching birthdays.
    :type user: User
    :return: A list of Contact objects whose birthdays match the next specified number of days.
    :rtype: List[ContactResponse]
    """
    bd_list = []
    for i in range(next_day):
        date_search = datetime.now().date() + timedelta(days=i)
        date_search = datetime.strftime(date_search, "%m-%d")
        bd_list.append(date_search)
    contacts = await repositories_contact.next_birthday(bd_list, db, user)
    return contacts


@router.get("/{contact_id}", response_model=Optional[ContactResponse])
async def get_contact_by_id(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Retrieves a contact by its ID from the database.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object representing the current user.
    :type user: User
    :return: The Contact object if found, otherwise a JSONResponse with a 404 status code.
    :rtype: Optional[ContactResponse]
    """
    contact = await repositories_contact.get_contact_by_id(contact_id, db, user)
    if contact is None:
        # raise HTTPException(
        #     status_code=status.HTTP_404_NOT_FOUND,
        #     # status_code=400,
        #     detail=f"Contact with id {contact_id} not found",
        # )
        # return None
        return JSONResponse(status_code=404, content={"detail": "Contact not found"})
    return contact


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    limit: int = Query(10, ge=10, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Get a list of contacts from the database based on the given pagination parameters.

    :param limit: The maximum number of contacts to retrieve. Default is 10. Must be between 10 and 500.
    :type limit: int
    :param offset: The number of contacts to skip before starting to retrieve. Default is 0. Must be non-negative.
    :type offset: int
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object representing the current user.
    :type user: User
    :return: A list of Contact objects.
    :rtype: list[ContactResponse]
    """
    contacts = await repositories_contact.get_contacts(limit, offset, db, user)
    return contacts


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def add_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Add a new contact to the database.

    :param body: The contact data to be added.
    :type body: ContactSchema
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object representing the current user.
    :type user: User
    :return: The newly created Contact object.
    :rtype: ContactResponse
    :raises HTTPException: If the contact data is invalid or if there is an error adding the contact to the database.
    """
    contact = await repositories_contact.add_contact(body, db, user)
    print(f"### return contact: {contact}")
    return contact


@router.put("/{contact_id}", response_model=Optional[ContactResponse])
async def update_contact(
    body: ContactSchema,
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Updates a contact in the database.

    :param body: The updated contact data.
    :type body: ContactSchema
    :param contact_id: The ID of the contact to update. Defaults to 1.
    :type contact_id: int, optional
    :param db: The database session for executing the query. Defaults to the result of `get_db` dependency.
    :type db: AsyncSession, optional
    :param user: The current user. Defaults to the result of `auth_service.get_current_user` dependency.
    :type user: User, optional

    :return: The updated contact if found, otherwise a JSONResponse with a 404 status code.
    :rtype: Optional[ContactResponse]
    """
    contact = await repositories_contact.update_contact(contact_id, body, db, user)
    if contact is None:
        return JSONResponse(status_code=404, content={"detail": "Contact not found"})
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Deletes a contact from the database.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: The database session for executing the query. Defaults to the result of `get_db` dependency.
    :type db: AsyncSession
    :param user: The current user. Defaults to the result of `auth_service.get_current_user` dependency.
    :type user: User

    :return: The deleted contact if successful.
    :rtype: Any
    """
    contact = await repositories_contact.delete_contact(contact_id, db, user)
    return contact
