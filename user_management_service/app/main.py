from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jwt import decode
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from app import models, schemas, crud
from .auth import create_jwt_token
from .database import engine, get_db
from .utils import verify_password, hash_password
from datetime import timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import random
import smtplib
import string
from typing import Annotated
import os

models.Base.metadata.create_all(bind=engine)

load_dotenv()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = str(os.getenv("ALGORITHM"))
ACCESS_TOKEN_EXPIRE_MINUTES = float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",
                                              default=0))
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

app = FastAPI()

models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
confirmation_codes = {}


async def send_confirmation_code(email_request: str):
    email = email_request
    confirmation_code = generate_confirmation_code()

    try:
        msg = MIMEMultipart()
        msg['From'] = f'avc99@tpu.ru'
        msg['To'] = email
        msg['Subject'] = "Код подтверждения регистрации"

        body = f"Ваш код подтверждения: {confirmation_code}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(msg['From'], email, msg.as_string())
        server.quit()

        return confirmation_code

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Ошибка при отправке письма: {str(e)}")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise credentials_exception
        return user_id
    except InvalidTokenError:
        raise credentials_exception


def generate_confirmation_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits,
                                  k=length))


@app.post("/register/",
          response_model=schemas.User,
          status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate,
                      db: Session = Depends(get_db)):
    detail = await crud.check_if_user_exists(db, user)
    if detail:
        raise HTTPException(status_code=400, detail=detail)
    user.password = hash_password(user.password)
    new_user = await crud.create_user(db, user=user)
    return new_user


@app.post("/login/")
async def login(request: Request,
                form_data: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    user = await crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password,
                                       user.password):
        raise HTTPException(status_code=401,
                            detail="Incorrect email or password")
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"Authorization": create_jwt_token(data={"id": user.id},
                                              expires_delta=token_expires),
            "token_type": "Bearer"}


@app.get("/users/{user_id}/",
         response_model=schemas.User)
async def read_user(user_id: int,
                    user_token_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    user = await crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}/", response_model=schemas.User)
async def update_user(user_id: int,
                      user_update: schemas.UserUpdate,
                      user_token_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if user_id == user_token_id:
        user = await crud.update_user(db=db, user_id=user_id,
                                      user_update=user_update)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    else:
        raise HTTPException(status_code=403, detail='Forbidden')


@app.put("/users/{user_id}/reset-password/", response_model=schemas.User)
async def reset_user_password(user_id: int,
                              user_update: schemas.PasswordUpdate,
                              user_token_id: int = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    if user_id == user_token_id:
        user = await crud.get_user_by_id(db, user_id=user_token_id)
        if confirmation_codes[user.id] == user_update.confirm_code:
            if not verify_password(user_update.last_password, user.password):
                raise HTTPException(status_code=401,
                                    detail='Uncorrect password')
            user = await crud.update_password(db=db, user=user,
                                              new_password=hash_password(
                                                user_update.password))
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        else:
            return {"message": "Invalid confirmation code"}
    else:
        raise HTTPException(status_code=403, detail='Forbidden')


@app.delete("/users/{user_id}/",
            status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int,
                      user_token_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if user_id == user_token_id:
        user = await crud.delete_user(db, user_id=user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return
    else:
        raise HTTPException(status_code=403, detail='Forbidden')


@app.get("/users/send")
async def send_confirm_mail(user_token_id: int = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    user = await crud.get_user_by_id(db, user_id=user_token_id)
    code = await send_confirmation_code(user.email)
    confirmation_codes[user.id] = code
    return {"message": "Confirmation code sent"}


# @app.put("/users/repassword")
# async def user_password_recovery(user_update: schemas.UserRecovery,
#                                  db: Session = Depends(get_db)):
#     user = await crud.get_user_by_email(db, email=user_update.email)
#     if 
