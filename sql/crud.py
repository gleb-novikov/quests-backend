import random
from datetime import timedelta, datetime
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from emails.email import send_activation_email, send_reset_email
from sql import schemas
from sql import models
from config.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30 * 6


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(db: Session, user_id: int) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> models.User:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_temp_token(db: Session, temp_token: str) -> models.User:
    return db.query(models.User).filter(models.User.temp_token == temp_token).first()


def get_user_by_token(db: Session, token: str) -> models.User:
    return db.query(models.User).filter(models.User.token == token).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def delete_user(db: Session, user: models.User):
    delete_progress(db, user)
    db.delete(user)
    db.commit()


async def create_user(db: Session, user: schemas.UserRegistration) -> schemas.UserTempToken:
    hashed_password = get_password_hash(user.password)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": hashed_password}, expires_delta=access_token_expires)
    temp_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    activation_code = ''.join(str(x) for x in random.sample(range(0, 9), 6))
    db_user = models.User(email=user.email, name=user.name, hashed_password=hashed_password, temp_token=temp_token,
                          activation_code=activation_code, token=token)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    await send_activation_email(db_user.email, {'name': db_user.name, 'activation_code': db_user.activation_code})
    return db_user


async def confirm_user(db: Session, user: schemas.User):
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def reset_password(db: Session, user: models.User):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    temp_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    activation_code = ''.join(str(x) for x in random.sample(range(0, 9), 6))

    user.temp_token = temp_token
    user.activation_code = activation_code
    db.add(user)
    db.commit()
    db.refresh(user)
    await send_reset_email(user.email, {'name': user.name, 'activation_code': user.activation_code})


async def reset_password_new(db: Session, user: models.User, password: str):
    user.hashed_password = get_password_hash(password)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    user.token = create_access_token(data={"sub": user.hashed_password}, expires_delta=access_token_expires)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def patch_me(db: Session, db_user: models.User, user: schemas.UserUpdate):
    user_data = user.dict(exclude_unset=True)
    for key, value in user_data.items():
        if value != "":
            if key == 'password':
                key = 'hashed_password'
                value = get_password_hash(value)
            setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_quests(db: Session):
    quests = schemas.Quests()
    quests.quests = db.query(models.Quest).all()
    return quests


def get_progress_by_token(db: Session, token: str):
    user = get_user_by_token(db, token)
    progress = schemas.ProgressObject()
    progress.progress = db.query(models.Progress).filter(models.Progress.user_id == user.id).all()
    return progress


def delete_progress(db: Session, user: models.User):
    db_progress = db.query(models.Progress).filter(models.Progress.user_id == user.id).all()
    for i in db_progress:
        db.delete(i)
        db.commit()


def post_progress(db: Session, token: str, progress: schemas.ProgressObject):
    user = get_user_by_token(db, token)
    delete_progress(db, user)
    for i in progress.progress:
        db_progress = models.Progress(user_id=user.id, quest_id=i.quest_id, location_id=i.location_id)
        db.add(db_progress)
        db.commit()
        db.refresh(db_progress)
    return get_progress_by_token(db, token)
