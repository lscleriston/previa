import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import backend.db.database as database

router = APIRouter()

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-previa-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: str

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: Optional[bool] = False

class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[str]
    is_admin: Optional[bool]

class UserInDB(User):
    password_hash: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user_by_username(username: str) -> Optional[UserInDB]:
    row = database.get_user_by_username(username)
    if not row:
        return None
    return UserInDB(
        id=row['id'],
        username=row['username'],
        is_admin=bool(row['is_admin']),
        created_at=row['created_at'],
        password_hash=row['password_hash'],
    )


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível autenticar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return User(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


async def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_active_admin)):
    users = database.list_users()
    return [User(**u) for u in users]


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate, current_user: User = Depends(get_current_active_admin)):
    existing = database.get_user_by_username(user_create.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já existe")
    password_hash = get_password_hash(user_create.password)
    created_user = database.create_user(user_create.username, password_hash, int(user_create.is_admin))
    return User(**created_user)


@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, current_user: User = Depends(get_current_active_admin)):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    password_hash = None
    if user_update.password:
        password_hash = get_password_hash(user_update.password)
    updated = database.update_user(
        user_id,
        username=user_update.username,
        password_hash=password_hash,
        is_admin=int(user_update.is_admin) if user_update.is_admin is not None else None,
    )
    return User(**updated)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_active_admin)):
    if database.get_user_by_id(user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    database.delete_user(user_id)
    return {"detail": "Usuário removido com sucesso"}
