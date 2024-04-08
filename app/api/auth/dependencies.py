from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .accesstoken import verify_access_token  # Đảm bảo đường dẫn import chính xác

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    decoded_jwt = verify_access_token(token)
    if not decoded_jwt:
        raise credentials_exception
    return decoded_jwt.get("sub")
