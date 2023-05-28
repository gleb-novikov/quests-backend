from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from sql.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    token = Column(String)
    temp_token = Column(String)
    activation_code = Column(String)
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    name = Column(String)


class Quest(Base):
    __tablename__ = 'quests'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    preview_url = Column(String)
    description = Column(String)
    time = Column(Integer)
    distance = Column(Integer)

    locations = relationship('Location', back_populates='quest')


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    story = Column(String)
    epilog = Column(String)
    quest_id = Column(Integer, ForeignKey('quests.id'))

    quest = relationship('Quest', back_populates='locations')


class Progress(Base):
    __tablename__ = 'progress'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    quest_id = Column(Integer, ForeignKey('quests.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))
