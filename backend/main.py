from fastapi import FastAPI
from database import engine
from models import Base
from routers import stations, weather

app = FastAPI()

# create tables
Base.metadata.create_all(bind=engine)

app.include_router(stations.router)
app.include_router(weather.router)

@app.get("/")
def root():
    return {"message": "API running"}