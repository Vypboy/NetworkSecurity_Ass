from datetime import datetime, timedelta
import jwt

#
secret_key = "drive_sync_secret_key"

# time deadline for access token (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 600


def create_access_token(user_id: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


def verify_access_token(token: str):
    try:
        decoded_jwt = jwt.decode(token, secret_key, algorithms=["HS256"])
        return decoded_jwt
    except:
        return False
