import email
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import Contact, User
from src.schemas.contact import ContactSchema
from src.repositories.contacts import (
    get_contacts,
    search_contacts,
    get_contact_by_id,
    add_contact,
    update_contact,
    delete_contact,
)

contacts = [
    Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="jone.doe@example.com",
        phone="1234567890",
        birthday="01.01.2000",
    ),
    Contact(
        id=2,
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="0503220000",
        birthday="02.02.2000",
    ),
]


class TestAsyncTodo(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.user = User(
            id=1,
            username="test_user",
            password="qwerty",
            role="user",
            avatar="",
            email="jone.doe@example.com",
        )
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        # mocked_contacts.scalars.return_value.filter_by.return_value.offset.return_value.limit.return_value.all.return_value = (
        #     contacts
        # )

        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(
            limit, offset=offset, db=self.session, user=self.user
        )
        self.assertEqual(result, contacts)

    async def test_search_contacts(self):
        limit = 10
        offset = 0
        filters = {}
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await search_contacts(
            filters=filters, limit=limit, offset=offset, db=self.session, user=self.user
        )
        self.assertEqual(result, contacts)

    async def test_get_contact_by_id(self):
        contact = contacts[0]
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        result = await get_contact_by_id(contact_id=1, db=self.session, user=self.user)
        self.assertEqual(result, contact)

    async def test_add_contact(self):
        body = ContactSchema(
            first_name="test first_name",
            last_name="test last_name",
            email="test@email.com",
            phone="1234567890",
            birthday="2000-01-01",
        )
        result = await add_contact(body=body, db=self.session, user=self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(
            result.first_name,
            body.first_name,
            "First name does not match",
        )
        self.assertEqual(
            result.last_name,
            body.last_name,
            "Last name does not match",
        )
        print(f"{result=}")
        self.assertEqual(result.email, body.email, "Email does not match")
        self.assertEqual(result.phone, body.phone, "Phone number does not match")
        self.assertEqual(result.birthday, body.birthday, "Birthday does not match")

    async def test_update_contact(self):
        body = ContactSchema(
            first_name="new first_name",
            last_name="new last_name",
            email="new@email.com",
            phone="2233445566",
            birthday="2002-02-02",
        )
        new_contact = Contact(
            id=1,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            phone=body.phone,
            birthday=body.birthday,
            user_id=1,
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = new_contact
        self.session.execute.return_value = mocked_contact
        result = await update_contact(
            contact_id=new_contact.id, body=body, db=self.session, user=self.user
        )
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, new_contact.first_name)
        self.assertEqual(result.last_name, new_contact.last_name)
        self.assertEqual(result.email, new_contact.email)
        self.assertEqual(result.phone, new_contact.phone)
        self.assertEqual(result.birthday, new_contact.birthday)

    async def test_delete_contact(self):
        contact_dict = {
            key: value
            for key, value in contacts[0].__dict__.items()
            if not key.startswith("_")
        }
        del_contact = Contact(**contact_dict)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = del_contact
        self.session.execute.return_value = mocked_contact

        result = await delete_contact(
            contact_id=del_contact.id, db=self.session, user=self.user
        )
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)


if __name__ == "__main__":
    unittest.main()
