from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel
from sqlmodel import Field, SQLModel
from sqlalchemy.sql import func
from enum import StrEnum
from sqlalchemy import Column, DateTime


class PostVideoModel(SQLModel):
    """Модель для загрузки данных о новом видео"""
    duration: Annotated[timedelta, Field(gt=0)] | None
    camera_number: Annotated[int, Field(gt=0)] | None
    location: str
    video_path: str
    start_time: datetime | None


class Videos(PostVideoModel, table=True):
    """Модель видео в базе данных"""
    id: int | None = Field(default=None, primary_key=True)
    status: str = "new"
    created_at:datetime = Field(sa_column=Column(DateTime(), server_default=func.now()))

class StatusEnum(StrEnum):
    """Перечисление возможных статусов видео"""
    NEW = "new"
    TRANSCODED = "transcoded"
    RECOGNIZED = "recognized"

class StatusQuery(BaseModel):
    """Модель запроса на обновлоение статуса"""
    status: StatusEnum

class FilterVideoParams(BaseModel):
    """Модель параметров фильтрации видео"""
    camera_number: list[int] | None = None
    location: list[str] | None = None
    status: list[str] | None = None
    start_time_to: datetime | None = None
    start_time_from: datetime | None = None

