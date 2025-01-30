from sqlalchemy.orm import Session
from . import models, schemas


async def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


async def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


async def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(
        models.User.username == username).first()


async def check_if_user_exists(db: Session, user_data: schemas.UserBase):
    if await get_user_by_email(db, user_data.email):
        return 'Email already exists.'
    if await get_user_by_username(db, user_data.username):
        return 'Username already exists.'


async def create_user(db: Session, user: schemas.UserCreate):
    user = models.User(username=user.username,
                       email=user.email,
                       password=user.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def delete_user(db: Session, user_id: int):
    user = await get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return user
    return None


async def update_user(db: Session,
                      user_id: int,
                      user_update: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


async def update_password(db: Session,
                         user: models.User,
                         new_password: str):
    setattr(user, "password", new_password)
    db.commit()
    db.refresh(user)
    return user
