from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app.core.database import database
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
from app.api.auth.dependencies import get_current_user
from typing import List
from bson import ObjectId, json_util
import os
import base64
import aiofiles
import uuid
from datetime import datetime

router = APIRouter()

# Định nghĩa MongoDB collection
user_collection = database.get_collection("newfeeds")

UPLOAD_DIRECTORY = "./data/newfeeds/"


async def save_file(dataFile: UploadFile, user_id):
    # Tạo tên file mới ngẫu nhiên
    file_extension = os.path.splitext(dataFile.filename)[1]  # Lấy phần mở rộng file
    random_filename = f"{uuid.uuid4()}{file_extension}"  # Tạo tên file ngẫu nhiên

    file_type = dataFile.content_type.split("/")[0]  # Lấy loại file

    # check UPLOAD_DIRECTORY/user_id is exist
    if os.path.isdir(UPLOAD_DIRECTORY + user_id) is False:
        os.mkdir(UPLOAD_DIRECTORY + user_id)

    file_path = os.path.join(UPLOAD_DIRECTORY + user_id, random_filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        # Read and write the file in chunks to handle large files
        while content := await dataFile.read(1024):  # Read in chunks of 1024 bytes
            await out_file.write(content)

    return file_path, file_type


@router.post("/newPosts")
async def newPosts(
    status: str,
    dataFile: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    # check user is database
    checkUser = await user_collection.find_one(
        {"_id": ObjectId(current_user["user_id"])}
    )

    if checkUser is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Thêm trường time_stamp vào data
    time_stamp = datetime.now()  # Lấy thời gian hiện tại

    if dataFile != None:
        # save file
        file_path, file_type = await save_file(dataFile, str(current_user["user_id"]))

        # save data
        data = {
            "user_id": current_user["user_id"],
            "status": status,
            "file": file_path,
            "file_type": file_type,
            "time_stamp": time_stamp,
        }
    else:
        data = {
            "user_id": current_user["user_id"],
            "status": status,
            "file": None,
            "file_type": None,
            "time_stamp": time_stamp,
        }

    # insert data
    newPost = await user_collection.insert_one(data)
    return {"status": "success", "data": str(newPost.inserted_id)}


async def get_file(file_path):
    async with aiofiles.open(file_path, "rb") as out_file:
        content = await out_file.read()
        return content


@router.get("/getPosts/{post_id}")
async def getPosts(post_id: str):
    # check post is database
    checkPost = await user_collection.find_one({"_id": ObjectId(post_id)})

    if checkPost is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # get file
    if checkPost["file"] != None:
        file = await get_file(checkPost["file"])
        file = base64.b64encode(file).decode("utf-8")
    else:
        file = None

    # get user
    user = await database.user.find_one({"_id": ObjectId(checkPost["user_id"])})[
        "username"
    ]

    return {
        "status": "success",
        "data": {
            "user_id": checkPost["user_id"],
            "username": user,
            "status": checkPost["status"],
            "file": file,
            "file_type": checkPost["file_type"],
            "time_stamp": checkPost["time_stamp"],
        },
    }


@router.get("/getPosts/{user_id}")
async def getPosts(user_id: str):
    # check user is database
    checkUser = await database.user.find_one({"_id": ObjectId(user_id)})

    if checkUser is None:
        raise HTTPException(status_code=404, detail="User not found")

    # get posts
    posts = await user_collection.find({"user_id": user_id}).to_list(length=1000)

    # get file
    result = []
    for post in posts:
        result.append(getPosts(post["_id"]))

    return {"status": "success", "data": result}


@router.delete("/deletePosts/{post_id}")
async def deletePosts(post_id: str, current_user: str = Depends(get_current_user)):
    # check post is database
    checkPost = await user_collection.find_one({"_id": ObjectId(post_id)})

    if checkPost is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # check user is post
    if checkPost["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="User not found")

    # delete post
    await user_collection.delete_one({"_id": ObjectId(post_id)})

    return {"status": "success"}
