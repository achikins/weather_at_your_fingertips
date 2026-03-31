from fastapi import FastAPI
from database import engine
from models import Base
from routers import stations, weather
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# create tables
Base.metadata.create_all(bind=engine)

app.include_router(stations.router)
app.include_router(weather.router)

@app.get("/")
def root():
    return {"message": "API running"}