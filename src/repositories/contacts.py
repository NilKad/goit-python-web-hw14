import logging
import pprint
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Contact, User
from src.schemas.contact import ContactSchema


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    """
    Retrieves a list of contacts from the database based on the specified limit and offset.

    :param limit: The maximum number of contacts to retrieve.
    :type limit: int
    :param offset: The number of contacts to skip before starting to retrieve.
    :type offset: int
    :param db: The database session for executing the query.
    :type db: AsyncSession
    :param user: The user for which to retrieve contacts.
    :type user: User
    :return: A list of Contact objects that match the specified limit and offset.
    :rtype: List[Contact]
    """

    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def search_contacts(
    filters: dict, limit: int, offset: int, db: AsyncSession, user: User
):
    """
    Search for contacts based on the given filters and return a list of Contact objects.

    :param filters: A dictionary containing the search filters. The keys are the field names and the values are the search values.
    :type filters: dict
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

    logging.info(f"search contacts, filter={filters}")
    stmt = select(Contact).where(Contact.user == user)

    for field, value in filters.items():
        if value:
            stmt = stmt.where(getattr(Contact, field).ilike(f"%{value}%"))
    stmt = stmt.offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    print(contacts)
    return contacts.scalars().all()


async def get_contact_by_id(contact_id: int, db: AsyncSession, user: User):
    """
    Retrieves a contact by ID from the database.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session for executing the query.
    :type db: AsyncSession
    :param user: The user requesting the contact.
    :type user: User
    :return: The contact object with the specified ID, or None if not found.
    :rtype: Contact
    """

    stmt = select(Contact).filter_by(id=contact_id)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def add_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
    Adds a new contact to the database.

    :param body: The ContactSchema object representing the contact data to be added.
    :type body: ContactSchema
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object adding the contact.
    :type user: User
    """

    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    print("!!!! add contact, commet & refresh")
    print(contact)
    return contact


async def update_contact(
    contact_id: int, body: ContactSchema, db: AsyncSession, user: User
):
    """
    A function to update a contact in the database.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The ContactSchema object with updated contact data.
    :type body: ContactSchema
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object updating the contact.
    :type user: User
    :return: The updated contact object.
    :rtype: Contact
    """

    stmt = select(Contact).filter_by(id=contact_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact is None:
        return None
    contact.first_name = body.first_name
    contact.last_name = body.last_name
    contact.phone = body.phone
    contact.email = body.email
    contact.birthday = body.birthday
    contact.addition = body.addition
    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Deletes a contact from the database based on the provided contact ID.

    :param contact_id: The ID of the contact to be deleted.
    :type contact_id: int
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object performing the deletion.
    :type user: User
    :return: The deleted contact object, or None if the contact was not found.
    :rtype: Contact or None
    """

    stmt = select(Contact).filter_by(id=contact_id)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact is None:
        return None
    await db.delete(contact)
    await db.commit()
    return contact


async def next_birthday(bd_list: list[str], db: AsyncSession, user: User):
    """
    Retrieves contacts whose birthday matches the provided list within the database.

    :param bd_list: A list of strings representing the birthdays to search for.
    :type bd_list: list[str]
    :param db: The AsyncSession database session for executing the query.
    :type db: AsyncSession
    :param user: The User object for whom to find contacts with matching birthdays.
    :type user: User
    :return: A list of Contact objects whose birthdays match the provided list.
    :rtype: List[Contact]
    """

    stmt = select(Contact).filter(
        func.to_char(func.to_date(Contact.birthday, "YYYY-MM-DD"), "MM-DD").in_(bd_list)
    )
    contacts = await db.execute(stmt)
    return contacts.scalars().all()
