from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, HTTPException
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select, col
from settings import settings
from models import VideoModel, PostVideoModel, FilterVideoParams, StatusQuery

def create_db():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield
app = FastAPI(lifespan=lifespan)

postgres_url = (f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:"
              f"{settings.postgres_port}/{settings.postgres_db}")
engine = create_engine(postgres_url, echo=True)\


@app.post("/videos", response_model=VideoModel)
def post_video(video: PostVideoModel):
    video_row = VideoModel(**video.model_dump())
    with Session(engine) as session:
        session.add(video_row)
        session.commit()
        session.refresh(video_row)
        return video_row

@app.get("/videos", response_model=list[VideoModel])
def get_videos(filter_query: Annotated[FilterVideoParams, Query()]):
    with Session(engine) as session:
        sql_query = select(VideoModel)
        if filter_query.camera_number:
            sql_query = sql_query.where(col(VideoModel.camera_number).in_(filter_query.camera_number))
        if filter_query.location:
            sql_query = sql_query.where(col(VideoModel.location).in_(filter_query.location))
        if filter_query.status:
            sql_query = sql_query.where(col(VideoModel.status).in_(filter_query.status))
        if filter_query.start_time_from:
            sql_query = sql_query.where(VideoModel.created_at >= filter_query.start_time_from)
        if filter_query.start_time_to:
            sql_query = sql_query.where(VideoModel.created_at >= filter_query.start_time_to)
        videos = session.exec(sql_query).all()
        if not videos:
            raise HTTPException(status_code=404, detail="No videos were found")
        return videos

@app.get("/videos/{video_id}", response_model=VideoModel)
def get_video(video_id: int):
    with Session(engine) as session:
        video = session.exec(select(VideoModel).where(VideoModel.id == video_id)).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return video


@app.patch("/videos/{video_id}/status")
def change_status(video_id: int, status: StatusQuery):
    with Session(engine) as session:
        video = session.exec(select(VideoModel).where(VideoModel.id == video_id)).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        video.status = str(status.status)
        session.add(video)
        session.commit()
        session.refresh(video)
    return video




