from typing import Optional
from datetime import datetime
from fastapi import UploadFile, File
from pydantic import BaseModel, Field
from typing import List
from bson import ObjectId
from datetime import datetime


class MessageModel(BaseModel):
    room_id: str
    content: str
    format: str

    class Config:
        schema_extra = {
            "example": {
                "content": "Hello, there!",
                "format": "text",
            }
        }


class MessageInDB(MessageModel):
    timestamp: datetime
    format: str

    class Config:
        schema_extra = {
            "example": {
                "content": "Hello, there!",
                "sender": "alice",
                "receiver": "bob",
                "timestamp": "2021-07-15T10:00:00.000Z",
                "format": "text",
            }
        }


class conversation(BaseModel):
    sender: str
    receiver: str

    class Config:
        schema_extra = {
            "example": {
                "sender": "alice",
                "receiver": "bob",
            }
        }


class sendImage(BaseModel):
    receiver: str

    class Config:
        schema_extra = {
            "example": {
                "image": "image.png",
                "receiver": "bob",
            }
        }


class ImageData(BaseModel):
    sender: str
    receiver: str


class RoomModel(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    members: List[str]
    is_group: bool = Field(default=False)  # Thêm trường này
    created_at: datetime = Field(default_factory=datetime.now)


class RoomInDB(RoomModel):
    pass
