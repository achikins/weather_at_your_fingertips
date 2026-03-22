from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:password@db:5432/weather_at_your_fingertips_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)