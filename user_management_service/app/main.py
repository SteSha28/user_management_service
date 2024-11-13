from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/",
          response_model=schemas.User,
          status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate,
                db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400,
                            detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/{user_id}",
         response_model=schemas.User)
def read_user(user_id: int,
              db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404,
                            detail="User not found")
    return user


@app.delete("/users/{user_id}",
            status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int,
                db: Session = Depends(get_db)):
    user = crud.delete_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404,
                            detail="User not found")
    return


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int,
                user_update: schemas.UserUpdate,
                db: Session = Depends(get_db)):
    user = crud.update_user(db=db, user_id=user_id, user_update=user_update)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
