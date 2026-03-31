from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_token, get_current_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    if not verify_password(form.password, form.username):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": create_token(form.username), "token_type": "bearer"}


@router.get("/me")
def me(user: str = Depends(get_current_user)):
    return {"username": user}
