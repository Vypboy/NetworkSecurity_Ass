from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Optional


class FriendRequestModel(BaseModel):
    receiver_id: str
    status: Optional[str] = Field(default="pending")


class FriendListModel(BaseModel):
    user_id: str
    friend_ids: List[str]


class AcceptFriendRequestModel(BaseModel):
    sender_id: str
    receiver_id: str


class RejectFriendRequestModel(BaseModel):
    sender_id: str
    receiver_id: str
