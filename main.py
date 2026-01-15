from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, HTTPException, Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select, col
from settings import settings
from models import Videos, PostVideoModel, FilterVideoParams, StatusQuery

def create_db():
    """Функция создает таблицу videos при запуске API. Если таблица существует, то не создаает"""
    SQLModel.metadata.create_all(engine) # функция тут малость не к месту, но как-то странно создавать отдельный
                                         # файл ради двух строк кода

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: создать базу данных и запуститься"""
    create_db()
    yield
app = FastAPI(lifespan=lifespan)

postgres_url = (f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:"
              f"{settings.postgres_port}/{settings.postgres_db}") # Строка для подключения к бд по данным из настроек
engine = create_engine(postgres_url, echo=True)

def get_session():
    """Генератор сессий, чтобы получать сессию как зависимость"""
    with Session(engine) as session:
        yield session
@app.post("/videos", response_model=Videos)
def post_video(*, session: Session = Depends(get_session), video: PostVideoModel):
    """Ручка для создания записей о видео"""
    video_row = Videos(**video.model_dump()) # Все что нужно для создания записи в таблице или известно,
    session.add(video_row) # или задано по умолчанию
    session.commit()
    session.refresh(video_row)
    return video_row

@app.get("/videos", response_model=list[Videos])
def get_videos(*, session: Session = Depends(get_session), filter_query: Annotated[FilterVideoParams, Query()]):
    """Ручка для получения отфильтрофванного списка видео"""
    sql_query = select(Videos)
    if filter_query.camera_number:
        sql_query = sql_query.where(col(Videos.camera_number).in_(filter_query.camera_number))
    if filter_query.location:
        sql_query = sql_query.where(col(Videos.location).in_(filter_query.location))
    if filter_query.status:
        sql_query = sql_query.where(col(Videos.status).in_(filter_query.status))
    if filter_query.start_time_from:
        sql_query = sql_query.where(Videos.created_at >= filter_query.start_time_from)
    if filter_query.start_time_to:
        sql_query = sql_query.where(Videos.created_at >= filter_query.start_time_to)
    videos = session.exec(sql_query).all()
    if not videos:
        raise HTTPException(status_code=404, detail="No videos were found")
    return videos #В задании не сказано, какую информацию отдавать, поэтому отдаем все, что есть

@app.get("/videos/{video_id}", response_model=Videos)
def get_video(*, session: Session = Depends(get_session), video_id: int):
    """Ручка для получения одиночго видео по id"""
    video = session.exec(select(Videos).where(Videos.id == video_id)).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@app.patch("/videos/{video_id}/status")
def change_status(*, session: Session = Depends(get_session), video_id: int, status: StatusQuery):
    """Ручка для обновления статуса видео"""
    video = session.exec(select(Videos).where(Videos.id == video_id)).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    video.status = str(status.status)
    session.add(video)
    session.commit()
    session.refresh(video)
    return video




