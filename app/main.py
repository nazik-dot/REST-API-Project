import secrets
from fastapi import Cookie, FastAPI, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn
from database import get_db
from models import Category, User, UserSession, Post, Comment
from auth import hash_password, check_password

app = FastAPI()

class Creds(BaseModel):
    username: str
    password: str

@app.post("/register", status_code=201)
def register(data: Creds, db: Session=Depends(get_db)):
    q = db.query(User).filter_by(username=data.username)
    if q.first():
        raise HTTPException(400, "Name is unavailable")
    user = User(username=data.username, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return {"id": user.id}

@app.post("/login")
def login(data: Creds, res: Response, db: Session=Depends(get_db)):
    q = db.query(User).filter_by(username=data.username)
    user = q.first()
    if not user or not check_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect data")
    sid = secrets.token_hex(32)
    db.add(UserSession(id=sid, user_id=user.id))
    db.commit()
    res.set_cookie("session_id", sid, httponly=True)
    return {"ok": True}

def current_user(session_id: str=Cookie(None), db: Session=Depends(get_db)):
    s = None
    if session_id:
        s = db.get(UserSession, session_id)
    if not s:
        raise HTTPException(401, "Log in!")
    return db.get(User, s.user_id)

@app.post("/logout")
def logout(res: Response, session_id: str=Cookie(None), db: Session=Depends(get_db)):
    db.query(UserSession).filter_by(id=session_id).delete()
    db.commit()
    res.delete_cookie("session_id")
    return {"ok": True}

class PostIn(BaseModel):
    title: str
    text: str
    category_id: int

class PostOut(BaseModel):
    id: int
    author_id: int
    model_config = {"from_attributes": True}

@app.post("/posts", response_model=PostOut)
def create_post(data: PostIn, user: User=Depends(current_user), db: Session=Depends(get_db)):
    post = Post(**data.model_dump(), author_id=user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@app.get("/posts", response_model=list[PostOut])
def list_posts(db: Session=Depends(get_db)):
    return db.query(Post).all()

@app.get("/post/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session=Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "Not Found")
    return post

@app.put("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: int, data: PostIn, user: User=Depends(current_user), db: Session=Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.author_id != user.id:
        raise HTTPException(404, "Not Found")
    post.title = data.title
    post.text = data.text
    post.category_id = data.category_id
    db.commit()
    return post

@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, user: User=Depends(current_user), db: Session=Depends(get_db)):
    post = db.get(Post, post_id)
    if post and post.author_id == user.id:
        db.delete(post)
        db.commit()

class CommentIn(BaseModel):
    text: str

@app.post("/posts/{post_id}/comments", status_code=201)
def add_comment(post_id: int, data: CommentIn, user: User=Depends(current_user), db: Session=Depends(get_db)):
    c = Comment(text=data.text, post_id=post_id, user_id=user.id)
    db.add(c)
    db.commit()
    return {"id": c.id, "text": c.text}

@app.get("/posts/{post_id}/comments")
def comments(post_id: int, db: Session=Depends(get_db)):
    rows = db.query(Comment).filter_by(post_id=post_id)
    return [{"id": c.id, "text": c.text} for c in rows]

class CategoryIn(BaseModel):
    name: str

@app.post("/categories", status_code=201)
def add_category(data: CategoryIn, db: Session=Depends(get_db)):
    c = Category(name=data.name)
    db.add(c)
    db.commit()
    return {"id": c.id, "name": c.name}

@app.get("/categories")
def categories(db: Session=Depends(get_db)):
    return db.query(Category).all()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)