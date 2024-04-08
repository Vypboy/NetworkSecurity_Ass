from fastapi import APIRouter, HTTPException, Depends
from app.core.database import database
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
from app.api.auth.dependencies import get_current_user
from app.api.user.models import FriendRequestModel
from app.api.user.models import FriendListModel
from app.api.user.models import AcceptFriendRequestModel
from app.api.user.models import RejectFriendRequestModel
from typing import List
from bson import ObjectId, json_util
import os
import base64

router = APIRouter()

# Định nghĩa MongoDB collection
user_collection = database.get_collection("contacts")

UPLOAD_DIRECTORY = "./data/avatars/"


@router.post("/send-friend-request")
async def send_friend_request(
    request: FriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    if request.receiver_id == current_user_id["user_id"]:
        raise HTTPException(
            status_code=400, detail="Cannot send friend request to yourself."
        )

    # Lưu lời mời kết bạn vào cơ sở dữ liệu
    existing_request = await user_collection.find_one(
        {
            "sender_id": current_user_id["user_id"],
            "receiver_id": request.receiver_id,
            "status": "pending",
        }
    )
    if existing_request:
        raise HTTPException(status_code=400, detail="Friend request already sent.")
    await user_collection.insert_one(
        {"sender_id": current_user_id["user_id"], **request.dict()}
    )
    return {"message": "Friend request sent successfully."}


@router.post("/accept-friend-request")
async def accept_friend_request(
    request: AcceptFriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    if request.receiver_id != current_user_id["user_id"]:
        raise HTTPException(
            status_code=400, detail="Cannot accept friend request sent to someone else."
        )

    # find friend request
    friend_request = await user_collection.find_one(
        {
            "sender_id": request.sender_id,
            "receiver_id": request.receiver_id,
            "status": "pending",
        }
    )

    # update friend request
    if friend_request:
        await user_collection.update_one(
            {"_id": friend_request["_id"]},
            {"$set": {"status": "accepted"}},
        )
    else:
        raise HTTPException(status_code=400, detail="Friend request not found.")

    return {"message": "Friend request accepted."}


@router.post("/reject-friend")
async def reject_friend_request(
    request: RejectFriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    # check current user is receiver
    if (
        request.receiver_id != current_user_id["user_id"]
        and request.sender_id != current_user_id["user_id"]
    ):
        raise HTTPException(
            status_code=400, detail="Cannot reject friend request sent to someone else."
        )

    # Xóa lời mời kết bạn khỏi cơ sở dữ liệu
    await user_collection.delete_one(
        {"sender_id": request.sender_id, "receiver_id": request.receiver_id}
    )
    await user_collection.delete_one(
        {"sender_id": request.receiver_id, "receiver_id": request.sender_id}
    )

    return {"message": "Friend request rejected."}


async def get_friends_list(user_id: str):
    friends_list = []

    # Lấy danh sách lời mời kết bạn
    friend_requests = await user_collection.find(
        {"sender_id": user_id, "status": "pending"}
    ).to_list(length=10000)

    # Lấy danh sách bạn bè
    friends = await user_collection.find(
        {
            "$or": [{"sender_id": user_id}, {"receiver_id": user_id}],
            "status": "accepted",
        }
    ).to_list(length=10000)

    # Kết hợp thông tin từ danh sách bạn bè
    for friend in friends:
        # Xác định ID của người bạn
        friend_id = (
            friend["receiver_id"]
            if friend["sender_id"] == user_id
            else friend["sender_id"]
        )

        # Truy vấn thông tin chi tiết từ cơ sở dữ liệu người dùng
        friend_info = await database.users.find_one({"_id": ObjectId(friend_id)})

        # check field avatar is exist
        if "avatar" in friend_info:
            avatar = friend_info["avatar"]
            image_path = os.path.join(UPLOAD_DIRECTORY, avatar)
            if os.path.exists(image_path):
                imageFile = os.path.join(image_path)
                # Mở và đọc file ảnh
                with open(imageFile, "rb") as image:
                    img = image.read()
                    # Chuyển đổi ảnh sang base64
                    conver_img = base64.b64encode(img).decode()
                    friends_list.append(
                        {
                            "id": str(friend_info["_id"]),
                            "name": friend_info.get("name"),
                            "avatar": conver_img,
                            "status": "accepted",
                        }
                    )
            else:
                friends_list.append(
                    {
                        "id": str(friend_info["_id"]),
                        "name": friend_info.get("name"),
                        "avatar": "",
                        "status": "accepted",
                    }
                )
        else:
            friends_list.append(
                {
                    "id": str(friend_info["_id"]),
                    "name": friend_info.get("name"),
                    "avatar": "",
                    "status": "accepted",
                }
            )

    for friend in friend_requests:
        # Xác định ID của người bạn
        friend_id = (
            friend["receiver_id"]
            if friend["sender_id"] == user_id
            else friend["sender_id"]
        )

        # Truy vấn thông tin chi tiết từ cơ sở dữ liệu người dùng
        friend_info = await database.users.find_one({"_id": ObjectId(friend_id)})

        # check field avatar is exist
        if "avatar" in friend_info:
            avatar = friend_info["avatar"]
            image_path = os.path.join(UPLOAD_DIRECTORY, avatar)
            if os.path.exists(image_path):
                imageFile = os.path.join(image_path)
                # Mở và đọc file ảnh
                with open(imageFile, "rb") as image:
                    img = image.read()
                    # Chuyển đổi ảnh sang base64
                    conver_img = base64.b64encode(img).decode()
                    friends_list.append(
                        {
                            "id": str(friend_info["_id"]),
                            "name": friend_info.get("name"),
                            "avatar": conver_img,
                            "status": "pending",
                        }
                    )
            else:
                friends_list.append(
                    {
                        "id": str(friend_info["_id"]),
                        "name": friend_info.get("name"),
                        "avatar": "",
                        "status": "pending",
                    }
                )
        else:
            friends_list.append(
                {
                    "id": str(friend_info["_id"]),
                    "name": friend_info.get("name"),
                    "avatar": "",
                    "status": "pending",
                }
            )

    return friends_list


@router.get("/get-all-friends/{user_id}")
async def get_all_friends(current_user_id: str = Depends(get_current_user)):
    user_id = current_user_id["user_id"]
    friends_list = await get_friends_list(user_id)

    return friends_list
