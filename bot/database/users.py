import datetime
from typing import Optional, List

from pyrogram.types import User
import sqlalchemy
from sqlalchemy import VARCHAR, Column, DateTime, Integer, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot import logger, SCHEMA
from bot.database import BASE

ACCEPTED_TEXT = "Hello {user}, you are accepted to {chat}!"

# Database essentials
engine = create_async_engine(SCHEMA)
async_session = async_sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)

class UserChannelSettings(BASE):
    __tablename__ = "user_channel_settings"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(sqlalchemy.BigInteger, nullable=False)
    channel_id = Column(sqlalchemy.BigInteger, nullable=False)

    def __init__(self, user_id: int, channel_id: int):
        self.user_id = user_id
        self.channel_id = channel_id

    def __repr__(self):
        return f"<UserChannelSettings user_id={self.user_id} channel_id={self.channel_id}>"

class GroupSettings(BASE):
    __tablename__ = "group_settings"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    group_id = Column(sqlalchemy.BigInteger, nullable=False)
    welcome_on = Column(sqlalchemy.Boolean, default=False)
    welcome_message = Column(sqlalchemy.String, default=ACCEPTED_TEXT)

    def __init__(self, group_id: int, welcome_on: bool, welcome_message: str = ACCEPTED_TEXT):
        self.group_id = group_id
        self.welcome_on = welcome_on
        self.welcome_message = welcome_message

    def __repr__(self):
        return f"<GroupSettings group_id={self.group_id} welcome_on={self.welcome_on}> welcome_message={self.welcome_message}>"

async def get_or_create(session, model, defaults=None, **kwargs):
    instance = await session.execute(select(model).filter_by(**kwargs))
    instance = instance.scalar_one_or_none()
    if instance:
        return instance, False
    else:
        params = {**kwargs, **(defaults or {})}
        instance = model(**params)
        session.add(instance)
        await session.commit()
        return instance, True

async def update_user_channel_settings(user_id: int, channel_id: int) -> bool:
    try:
        async with async_session() as session:
            user_channel_settings, created = await get_or_create(session, UserChannelSettings, user_id=user_id, channel_id=channel_id)
            return created
    except SQLAlchemyError as e:
        logger.error(f"Error in update_user_channel_settings: {e}")
        return False

async def delete_user_channel_settings(user_id: int, channel_id: int) -> bool:
    try:
        async with async_session() as session:
            user_channel_settings, _ = await get_or_create(session, UserChannelSettings, user_id=user_id, channel_id=channel_id)
            if user_channel_settings:
                await session.delete(user_channel_settings)
                await session.commit()
                return True
            else:
                return False
    except SQLAlchemyError as e:
        logger.error(f"Error in delete_user_channel_settings: {e}")
        return False

async def update_welcome_setting(group_id: int, welcome_on: bool) -> bool:
    try:
        async with async_session() as session:
            group_settings_results = await session.execute(
                select(GroupSettings).filter_by(group_id=group_id)
            )
            group_settings = group_settings_results.scalar_one_or_none()

            if group_settings:
                group_settings.welcome_on = welcome_on
            else:
                group_settings = GroupSettings(group_id=group_id, welcome_on=welcome_on)
                session.add(group_settings)

            await session.commit()
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error in update_welcome_setting: {e}")
        return False

async def get_welcome_setting(group_id: int) -> Optional[bool]:
    try:
        async with async_session() as session:
            group_settings_results = await session.execute(
                select(GroupSettings).filter_by(group_id=group_id)
            )
            group_settings = group_settings_results.scalar_one_or_none()

            if group_settings:
                return group_settings.welcome_on
            else:
                return None
    except SQLAlchemyError as e:
        logger.error(f"Error in get_welcome_setting: {e}")
        return None

async def set_welcome_message(group_id: int, new_message: str) -> bool:
    try:
        async with async_session() as session:
            group_settings, _ = await get_or_create(session, GroupSettings, welcome_on=True, group_id=group_id)
            group_settings.welcome_message = new_message
            await session.commit()
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error in set_welcome_message: {e}")
        return False

async def get_welcome_message(group_id: int) -> str:
    try:
        async with async_session() as session:
            group_settings, _ = await get_or_create(session, GroupSettings, group_id=group_id)
            return group_settings.welcome_message or ACCEPTED_TEXT
    except SQLAlchemyError as e:
        logger.error(f"Error in get_welcome_message: {e}")
        return ACCEPTED_TEXT
