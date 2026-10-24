from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(200))

class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

class UserSession(Base):
    __tablename__ = "sessions"
    id = Column(String(64), primary_key=True)
    user_id = Column(ForeignKey("users.id"))

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    text = Column(Text)
    author_id = Column(ForeignKey("users.id"))
    category_id = Column(ForeignKey("category.id"))
    author = relationship("User")
    category = relationship("Category")
    comments = relationship("Comment", cascade="all, delete")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    post_id = Column(ForeignKey("posts.id"))
    user_id = Column(ForeignKey("users.id"))