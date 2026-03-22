from sqlalchemy import (
    Column, Integer, BigInteger, SmallInteger, String, Float, Date, Numeric,
    DateTime, Boolean, Text, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Station(Base):
    __tablename__ = "stations"

    station_id = Column(Integer, primary_key=True, index=True)
    station_name = Column(String(150), unique=True, nullable=False)
    state = Column(String(3), nullable=True)
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    elevation_m = Column(Numeric(6, 1), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    coverage_pct = Column(Numeric(5, 2), nullable=True)

    forecasts = relationship("Forecast", back_populates="station", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="station", cascade="all, delete-orphan")
    monthly_aggregates = relationship("MonthlyAggregate", back_populates="station", cascade="all, delete-orphan")
    daily_weather = relationship("DailyWeather", back_populates="station", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    alert_type = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationship back to Station
    station = relationship("Station", back_populates="alerts")


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        UniqueConstraint("station_id", "forecast_date", "horizon_days", name="uq_forecast"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    forecast_date = Column(Date, nullable=False)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    horizon_days = Column(SmallInteger, nullable=False)
    pred_max_temp_c = Column(Numeric(5, 2), nullable=True)
    pred_min_temp_c = Column(Numeric(5, 2), nullable=True)
    pred_rain_mm = Column(Numeric(7, 2), nullable=True)
    pred_humidity_pct = Column(Numeric(5, 2), nullable=True)
    pred_wind_speed_ms = Column(Numeric(5, 2), nullable=True)

    # Relationship back to Station
    station = relationship("Station", back_populates="forecasts")

class MonthlyAggregate(Base):
    __tablename__ = "monthly_aggregates"
    __table_args__ = (
        UniqueConstraint("station_id", "station_year", "station_month", name="uq_station_year_month"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    station_year = Column(Integer, nullable=False)
    station_month = Column(Integer, nullable=False)
    avg_max_temp_c = Column(Numeric(5, 2), nullable=True)
    avg_min_temp_c = Column(Numeric(5, 2), nullable=True)
    total_rain_mm = Column(Numeric(9, 2), nullable=True)
    avg_min_humidity_pct = Column(Numeric(5, 2), nullable=True)
    avg_max_humidity_pct = Column(Numeric(5, 2), nullable=True)
    avg_wind_speed_ms = Column(Numeric(6, 2), nullable=True)
    days_recorded = Column(Integer, nullable=True)

    # Relationship back to Station
    station = relationship("Station", back_populates="monthly_aggregates")

class DailyWeather(Base):
    __tablename__ = "daily_weather"
    __table_args__ = (
        UniqueConstraint("station_id", "obs_date", name="uq_station_obs_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    obs_date = Column(Date, nullable=False)
    rain_mm = Column(Numeric(7, 2), nullable=True)
    max_temp_c = Column(Numeric(5, 2), nullable=True)
    min_temp_c = Column(Numeric(5, 2), nullable=True)
    max_humidity_pct = Column(Numeric(5, 2), nullable=True)
    min_humidity_pct = Column(Numeric(5, 2), nullable=True)
    avg_wind_speed_mps = Column(Numeric(5, 2), nullable=True)

    # Relationship back to Station
    station = relationship("Station", back_populates="daily_weather")