from datetime import datetime, timedelta
from time import strptime

import pytest
from fastapi.testclient import TestClient
from httpx import Client
from sqlalchemy import create_engine, StaticPool
from sqlmodel import SQLModel, Session, select

from main import app, get_session
from models import Videos


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_post_video(client: TestClient, session: Session):
    response = client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                                 "start_time": "2024-01-15T10:30:00",
                                                 "duration": "PT1H",
                                                 "camera_number": 1,
                                                 "location": "Entrance"
                                                })
    data = response.json()
    assert response.status_code == 200
    assert data['duration'] == "PT1H"
    assert data["id"] == 1
    assert data['status'] == "new"
    assert data['camera_number'] == 1
    assert data['location'] == "Entrance"
    assert data['video_path'] == "/storage/camera1/2024-01-15_10-30-00.mp4"
    assert data['start_time'] == "2024-01-15T10:30:00"
    assert datetime.fromisoformat(data['created_at'])


    row = session.exec(select(Videos).where(Videos.id == 1)).first()

    assert row.id == 1
    assert row.status == "new"
    assert row.duration == timedelta(hours=1)
    assert row.camera_number == 1
    assert row.location == "Entrance"
    assert row.video_path == "/storage/camera1/2024-01-15_10-30-00.mp4"
    assert row.start_time == datetime(2024, 1, 15, 10, 30)


    response = client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                                 "start_time": "2024-01-15T10:30:00",
                                                 "duration": "PT1H",
                                                 "camera_number": -1,
                                                 "location": "Entrance"
                                                })
    data = response.json()
    assert response.status_code == 422
    assert data['detail'][0]['msg'] == 'Input should be greater than 0'

    response = client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                                 "start_time": "2024-01-15T10:30:00",
                                                 "duration": "PT1H",
                                                 "camera_number": 1,
                                                })
    data = response.json()
    assert response.status_code == 422
    assert data['detail'][0]['msg'] == 'Field required'


    response = client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                                 "start_time": "2024-01-15T10:30:00",
                                                 "duration": "-1 day, 14:00:00",
                                                 "camera_number": 1,
                                                 "location": "Entrance"
                                                })
    data = response.json()
    assert response.status_code == 422
    assert data['detail'][0]['msg'] == 'Input should be greater than 0 seconds'

def test_get_video(client: Client):
    response = client.get("/videos/1")
    data = response.json()
    assert response.status_code == 404
    assert data["detail"] == "Video not found"


    client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                  "start_time": "2024-01-15T10:30:00",
                                  "duration": "PT1H",
                                  "camera_number": 1,
                                  "location": "Entrance"
                                  })
    response = client.get("/videos/1")
    data = response.json()
    assert response.status_code == 200
    assert data['duration'] == "PT1H"
    assert data["id"] == 1
    assert data['status'] == "new"
    assert data['camera_number'] == 1
    assert data['location'] == "Entrance"
    assert data['video_path'] == "/storage/camera1/2024-01-15_10-30-00.mp4"
    assert data['start_time'] == "2024-01-15T10:30:00"
    assert datetime.fromisoformat(data['created_at'])


def test_change_status(client: Client, session: Session):
    response = client.patch("/videos/1/status/", json={ "status": "new"
                                                })
    assert response.status_code == 404


    client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                  "start_time": "2024-01-15T10:30:00",
                                  "duration": "PT1H",
                                  "camera_number": 1,
                                  "location": "Entrance"
                                  })

    for status in ["new", "recognized", "transcoded"]:
        response = client.patch("/videos/1/status/", json={"status": status
                                            })
        assert response.status_code == 200
        data = response.json()
        assert response.status_code == 200
        assert data['duration'] == "PT1H"
        assert data["id"] == 1
        assert data['status'] == status
        assert data['camera_number'] == 1
        assert data['location'] == "Entrance"
        assert data['video_path'] == "/storage/camera1/2024-01-15_10-30-00.mp4"
        assert data['start_time'] == "2024-01-15T10:30:00"
        assert datetime.fromisoformat(data['created_at'])

        row = session.exec(select(Videos).where(Videos.id == 1)).first()

        assert row.id == 1
        assert row.status == status
        assert row.duration == timedelta(hours=1)
        assert row.camera_number == 1
        assert row.location == "Entrance"
        assert row.video_path == "/storage/camera1/2024-01-15_10-30-00.mp4"
        assert row.start_time == datetime(2024, 1, 15, 10, 30)

def test_get_videos(client: Client):
    response = client.get("/videos")
    assert response.status_code == 404

    client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                  "start_time": "2024-01-15T10:30:00",
                                  "duration": "PT1H",
                                  "camera_number": 1,
                                  "location": "Entrance"
                                  })

    client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                  "start_time": "2024-02-15T10:30:00",
                                  "duration": "PT1H",
                                  "camera_number": 1,
                                  "location": "Exit"
                                  })

    client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                  "start_time": "2024-02-15T10:30:00",
                                  "duration": "PT1H",
                                  "camera_number": 2,
                                  "location": "Entrance"
                                  })

    client.post("/videos/", json={"video_path": "/storage/camera1/2024-01-15_10-30-00.mp4",
                                  "start_time": "2024-03-15T10:30:00",
                                  "duration": "PT1H",
                                  "camera_number": 2,
                                  "location": "Entrance"
                                  })

    response = client.get("/videos")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 4

    response = client.get("/videos", params={"location":"Entrance"})
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 3

    response = client.get("/videos", params={"camera_number": 2})
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2

    response = client.get("/videos", params={"start_time_from": "2024-02-15T10:30:00"})
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 3

    response = client.get("/videos", params={"start_time_to": "2024-02-15T10:30:00"})
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
