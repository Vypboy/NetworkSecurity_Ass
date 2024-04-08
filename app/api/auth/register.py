from app.api.auth.models import RegistrationRequest  # Mô hình mới cho yêu cầu đăng ký
import hashlib
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from app.core.database import database
from app.api.auth.models import EmailRequest  # Mô hình mới để xử lý yêu cầu email
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.api.auth.models import PasswordResetRequest, PasswordResetModel, UserInfo
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
from app.api.auth.dependencies import get_current_user
from bson import ObjectId
import os
import uuid


router = APIRouter()
user_collection = database.get_collection("users")

UPLOAD_DIRECTORY = "./data/avatars/"


sender_email = "webchat6969@gmail.com"
sender_password = "fxvn uepm wsqe pqmw"


def send_email(sender_email, sender_password, receiver_email, subject, message):
    # Create a multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Add body to email
    msg.attach(MIMEText(message, "plain"))

    # Create SMTP session
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


def send_verification_email(email: str, code: str):
    sender_email = "webchat6969@gmail.com"  # Địa chỉ email của bạn
    sender_password = "fxvn uepm wsqe pqmw"  # Mật khẩu email của bạn
    receiver_email = email  # Địa chỉ email của người nhận
    subject = "Webchat Verification Code"  # Chủ đề email
    message = f"Your verification code is {code}"  # Nội dung email

    send_email(sender_email, sender_password, receiver_email, subject, message)


async def check_account(email):
    user = await user_collection.find_one({"email": email})
    if user:
        # Check if the 'password' key exists in the 'user' dictionary
        if "password" in user:
            return True
        else:
            return False
    else:
        return False


@router.post("/request-verification")
async def request_verification(email_request: EmailRequest):
    # Kiểm tra tài khoản đã được đăng ký chưa
    if await check_account(email_request.email):
        raise HTTPException(status_code=400, detail="Email has been registered")
    # Tạo mã xác nhận
    verification_code = str(random.randint(100000, 999999))
    # Lưu mã xác nhận và email vào cơ sở dữ liệu tạm thời
    temp_data = {
        "email": email_request.email,
        "verification_code": verification_code,
    }
    await user_collection.insert_one(temp_data)

    # Gửi email với mã xác nhận
    send_verification_email(email_request.email, verification_code)

    return {"message": "Verification email sent"}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
async def register(registration_request: RegistrationRequest):
    # Tìm kiếm mã xác nhận trong cơ sở dữ liệu
    temp_data = await user_collection.find_one({"email": registration_request.email})
    if (
        not temp_data
        or temp_data["verification_code"] != registration_request.verification_code
    ):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Băm mật khẩu
    hashed_password = hash_password(registration_request.password)

    # Tạo document người dùng
    user_document = {
        "email": registration_request.email,
        "password": hashed_password,
    }

    # Chèn vào cơ sở dữ liệu người dùng
    result = await user_collection.insert_one(user_document)

    # Xóa dữ liệu tạm thời
    await user_collection.delete_one({"email": registration_request.email})

    return {"user_id": str(result.inserted_id), "email": registration_request.email}


@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    user = await user_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(
            status_code=404, detail="User with this email does not exist"
        )

    # Tạo mã xác nhận
    verification_code = str(random.randint(100000, 999999))
    # Lưu mã xác nhận vào cơ sở dữ liệu
    await user_collection.update_one(
        {"email": request.email}, {"$set": {"reset_code": verification_code}}
    )

    # Gửi email với mã xác nhận
    send_verification_email(request.email, verification_code)

    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(reset_request: PasswordResetModel):
    # Kiểm tra mã xác nhận
    user = await user_collection.find_one(
        {"email": reset_request.email, "reset_code": reset_request.verification_code}
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Invalid email or verification code"
        )
    else:
        # Xóa mã xác nhận trong cơ sở dữ liệu
        await user_collection.update_one(
            {"email": reset_request.email}, {"$unset": {"reset_code": ""}}
        )

    # Băm mật khẩu mới và cập nhật vào cơ sở dữ liệu
    hashed_password = hash_password(reset_request.new_password)
    await user_collection.update_one(
        {"email": reset_request.email}, {"$set": {"password": hashed_password}}
    )

    return {"message": "Password has been reset successfully"}


# đặt tên cho user
@router.post("/set-info")
async def set_info(info: UserInfo, current_user_id: str = Depends(get_current_user)):
    # check if user is logged in
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    # check if user is existed
    user_id = ObjectId(current_user_id["user_id"])
    user = await user_collection.find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # update info
    await user_collection.update_one(
        {"_id": user_id},
        {"$set": {"email": info.email, "name": info.name, "phone": info.phone}},
    )

    return {"message": "Set info successfully"}


@router.post("/set-avatar")
async def set_avatar(
    image: UploadFile = File(...), current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = ObjectId(current_user_id["user_id"])
    user = await user_collection.find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Tạo tên file duy nhất và lưu file
    filename = f"{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"

    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    with open(file_path, "wb") as file_out:
        file_out.write(await image.read())

    # Lưu đường dẫn vào cơ sở dữ liệu
    await user_collection.update_one(
        {"_id": user_id},
        {"$set": {"avatar": filename}},
    )

    return {"message": "Set avatar successfully"}


@router.get("/get-info")
async def get_info(current_user_id: str = Depends(get_current_user)):
    # check if user is logged in
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    # check if user is existed
    user_id = ObjectId(current_user_id["user_id"])
    user = await user_collection.find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user["email"],
        "name": user["name"],
        "phone": user["phone"],
        "avatar": user["avatar"],
    }


@router.get("/get-avatar")
async def get_avatar(current_user_id: str = Depends(get_current_user)):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = ObjectId(current_user_id["user_id"])
    user = await user_collection.find_one({"_id": user_id})

    if not user or "avatar" not in user:
        raise HTTPException(status_code=404, detail="User or avatar not found")

    avatar_path = os.path.join(UPLOAD_DIRECTORY, user["avatar"])
    return FileResponse(avatar_path)
