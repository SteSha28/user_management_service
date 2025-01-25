from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String(30), nullable=True)
    last_name = Column(String(30), nullable=True)
    dob = Column(Date, nullable=True)
    created_at = Column(Date, server_default=func.now())
    gender = Column(String(20), nullable=False, default="not_specified")
    profile_image = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    source_id = Column(Integer, ForeignKey("source_users.id",
                                           ondelete="SET NULL"), nullable=True)
    role_id = Column(Integer, ForeignKey("role.id",
                                         ondelete="SET NULL"), nullable=True)

    source = relationship("Source_user",
                          back_populates="user",
                          passive_deletes=True)
    role = relationship("Role",
                        back_populates="user",
                        passive_deletes=True)


class Source_user(Base):
    __tablename__ = "source_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    user = relationship("User",
                        back_populates="source",
                        passive_deletes=True)


class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    user = relationship("User",
                        back_populates="role")
