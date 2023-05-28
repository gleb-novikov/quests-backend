from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from sql import crud, models, schemas
from sql.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/auth/registration", response_model=schemas.UserTempToken)
async def create_user(user: schemas.UserRegistration, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        if db_user.is_active:
            return JSONResponse(status_code=400, content={'message': 'Пользователь с таким email уже зарегистрирован.'})
        else:
            crud.delete_user(db, db_user)
    return await crud.create_user(db=db, user=user)


@app.post("/auth/registration/confirm")
async def confirm_user(token: Annotated[str, Depends(oauth2_scheme)], user: schemas.UserConfirm,
                       db: Session = Depends(get_db)):
    db_user = crud.get_user_by_temp_token(db, token)
    if db_user.activation_code == user.activation_code:
        await crud.confirm_user(db, db_user)
    else:
        return JSONResponse(status_code=400, content={'message': 'Неверный код активации.'})
    return JSONResponse(status_code=200, content={})


@app.post("/auth/login", response_model=schemas.User)
async def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user and crud.verify_password(user.password, db_user.hashed_password):
        if db_user.is_active:
            return db_user
        else:
            return JSONResponse(status_code=400, content={'message': 'Аккаунт не активирован.'})
    else:
        return JSONResponse(status_code=400, content={'message': 'Неверные данные для входа.'})


@app.post("/auth/reset")
async def reset_password(user: schemas.UserBase, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        await crud.reset_password(db, db_user)
    else:
        return JSONResponse(status_code=400, content={'message': 'Аккаунт не найден.'})
    return JSONResponse(status_code=200, content={})


@app.post("/auth/reset/code", response_model=schemas.UserTempToken)
async def reset_password_code(user: schemas.UserResetCode, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user.activation_code == user.activation_code:
        await crud.confirm_user(db, db_user)
    else:
        return JSONResponse(status_code=400, content={'message': 'Неверный код активации.'})
    return db_user


@app.post("/auth/reset/new")
async def reset_password_new(token: Annotated[str, Depends(oauth2_scheme)], user: schemas.UserResetNew,
                             db: Session = Depends(get_db)):
    db_user = crud.get_user_by_temp_token(db, token)
    await crud.reset_password_new(db, db_user, user.password)
    return JSONResponse(status_code=200, content={})


@app.get("/users/me", response_model=schemas.User)
def get_me(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    db_user = crud.get_user_by_token(db, token=token)
    if db_user:
        if db_user.is_active:
            return db_user
        else:
            return JSONResponse(status_code=400, content={'message': 'Аккаунт не активирован.'})
    else:
        return JSONResponse(status_code=400, content={'message': 'Невалидный токен.'})


@app.patch("/users/me", response_model=schemas.User)
async def patch_me(token: Annotated[str, Depends(oauth2_scheme)], user: schemas.UserUpdate,
                   db: Session = Depends(get_db)):
    db_user = crud.get_user_by_token(db, token=token)
    if db_user:
        if db_user.is_active:
            return crud.patch_me(db, db_user=db_user, user=user)
        else:
            return JSONResponse(status_code=400, content={'message': 'Аккаунт не активирован.'})
    else:
        return JSONResponse(status_code=400, content={'message': 'Невалидный токен.'})


@app.delete("/users/me")
async def delete_me(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    db_user = crud.get_user_by_token(db, token=token)
    if db_user:
        if db_user.is_active:
            crud.delete_user(db, user=db_user)
            return JSONResponse(status_code=200, content={})
        else:
            return JSONResponse(status_code=400, content={'message': 'Аккаунт не активирован.'})
    else:
        return JSONResponse(status_code=400, content={'message': 'Невалидный токен.'})


@app.get("/quests", response_model=schemas.Quests)
def get_quests(db: Session = Depends(get_db)):
    return crud.get_quests(db)


@app.get("/progress", response_model=schemas.ProgressObject)
def get_progress(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    return crud.get_progress_by_token(db, token)


@app.post("/progress", response_model=schemas.ProgressObject)
def post_progress(token: Annotated[str, Depends(oauth2_scheme)], progress: schemas.ProgressObject,
                  db: Session = Depends(get_db)):
    return crud.post_progress(db, token, progress)
