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
from pathlib import Path
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

app = FastAPI()

models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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


@app.post("/register/",
          response_model=schemas.User,
          status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate,
                      db: Session = Depends(get_db)):
    detail = await crud.check_if_user_exists(db, user)
    if detail:
        raise HTTPException(status_code=400,
                            detail=detail)
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
        raise HTTPException(status_code=404,
                            detail="User not found")
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


@app.delete("/users/{user_id}/",
            status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int,
                      user_token_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if user_id == user_token_id:
        user = await crud.delete_user(db, user_id=user_id)
        if user is None:
            raise HTTPException(status_code=404,
                                detail="User not found")
        return
    else:
        raise HTTPException(status_code=403, detail='Forbidden')
