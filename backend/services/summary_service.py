from typing import Any

def calculate_annual_summary(monthly: list[dict[str, Any]]) -> dict[str, Any]:
    if not monthly:
        return {
            "avgTemp": None,
            "maxTemp": None,
            "minTemp": None,
            "totalRain": None,
            "avgHumidity": None,
            "avgWind": None,
        }

    temps_avg = [m.get("tempAvg") for m in monthly if m.get("tempAvg") is not None]
    temps_max = [m.get("tempMax") for m in monthly if m.get("tempMax") is not None]
    temps_min = [m.get("tempMin") for m in monthly if m.get("tempMin") is not None]
    rain = [m.get("rainfall") for m in monthly if m.get("rainfall") is not None]
    humidity = [m.get("humidity") for m in monthly if m.get("humidity") is not None]
    wind = [m.get("windSpeed") for m in monthly if m.get("windSpeed") is not None]

    def avg(values: list[float]) -> float | None:
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    return {
        "avgTemp": avg(temps_avg),
        "maxTemp": max(temps_max) if temps_max else None,
        "minTemp": min(temps_min) if temps_min else None,
        "totalRain": round(sum(rain), 2) if rain else None,
        "avgHumidity": avg(humidity),
        "avgWind": avg(wind),
    }
