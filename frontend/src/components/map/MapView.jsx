import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { australianCities } from "../../data/australianCities";
import { api } from "../../services/api";
import LayerToggle from "./LayerToggle";
import CityPopup from "./CityPopup";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || "YOUR_MAPBOX_TOKEN";

const layerColorScale = {
  temperature: { low: "#3b82f6", mid: "#f59e0b", high: "#ef4444" },
  rainfall: { low: "#e2e8f0", mid: "#60a5fa", high: "#1d4ed8" },
  humidity: { low: "#fef3c7", mid: "#34d399", high: "#059669" },
  wind: { low: "#c4b5fd", mid: "#a78bfa", high: "#7c3aed" },
};

const getLayerValue = (current, layer) => {
  if (!current) return 0;
  switch (layer) {
    case "temperature":
      return Math.round(current.temp ?? 0);
    case "rainfall":
      return Math.round(current.rainfall ?? 0);
    case "humidity":
      return Math.round(current.humidity ?? 0);
    case "wind":
      return Math.round(current.windSpeed ?? 0);
    default:
      return 0;
  }
};

const getLayerUnit = (layer) => {
  switch (layer) {
    case "temperature":
      return "°C";
    case "rainfall":
      return "mm";
    case "humidity":
      return "%";
    case "wind":
      return "km/h";
    default:
      return "";
  }
};

const LAYER_RANGES = {
  temperature: [8, 24],
  rainfall: [3, 380],
  humidity: [40, 80],
  wind: [11, 24],
}

const getMarkerColor = (value, layer) => {
  const [min, max] = LAYER_RANGES[layer] || [0, 100];
  const t = Math.min(1, Math.max(0, (value - min) / (max - min)));
  if (t < 0.5) {
    const a = layerColorScale[layer].low;
    const b = layerColorScale[layer].mid;
    return interpolateColor(a, b, t * 2);
  } else {
    const a = layerColorScale[layer].mid;
    const b = layerColorScale[layer].high;
    return interpolateColor(a, b, (t - 0.5) * 2);
  }
};

const hexToRgb = (hex) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return [r, g, b];
};

const interpolateColor = (hex1, hex2, t) => {
  const [r1, g1, b1] = hexToRgb(hex1);
  const [r2, g2, b2] = hexToRgb(hex2);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `rgb(${r},${g},${b})`;
};

export default function MapView() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const [activeLayer, setActiveLayer] = useState("temperature");
  const [selectedCity, setSelectedCity] = useState(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [cityAlerts, setCityAlerts] = useState([]);
  const [cityCurrentById, setCityCurrentById] = useState({});
  const [selectedCityWeather, setSelectedCityWeather] = useState(null);

  useEffect(() => {
    let mounted = true;
    Promise.all(
      australianCities.map(async (city) => {
        const data = await api.getCityCurrent(city.id);
        return [city.id, data.current || null];
      }),
    )
      .then((entries) => {
        if (!mounted) return;
        setCityCurrentById(Object.fromEntries(entries));
      })
      .catch(() => {
        if (!mounted) return;
        setCityCurrentById({});
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (mapRef.current) return;
    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [133.7751, -25.2744],
      zoom: 4,
      minZoom: 3,
      maxZoom: 12,
      attributionControl: false,
    });

    map.addControl(
      new mapboxgl.NavigationControl({ showCompass: false }),
      "bottom-right",
    );
    map.addControl(
      new mapboxgl.AttributionControl({ compact: true }),
      "bottom-left",
    );

    map.on("load", () => {
      setMapLoaded(true);
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;

    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    australianCities.forEach((city) => {
      const current = cityCurrentById[city.id];
      const value = getLayerValue(current, activeLayer);
      const color = getMarkerColor(value, activeLayer);
      const unit = getLayerUnit(activeLayer);

      // Outer el: owned by Mapbox GL (writes transform: translate here) — no transforms on this
      const dotEl = document.createElement("div");
      dotEl.style.cssText = `cursor: pointer;`;

      // Inner el: safe to scale/animate without conflicting with Mapbox's translate
      const dotInner = document.createElement("div");
      dotInner.style.cssText = `
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: ${color}18;
        border: 2.5px solid ${color};
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 14px ${color}55;
        transform-origin: center center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      `;

      const inner = document.createElement("div");
      inner.style.cssText = `
        font-size: 12px;
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        letter-spacing: -0.3px;
        pointer-events: none;
        text-shadow: 0 1px 4px rgba(0,0,0,0.9);
      `;
      inner.textContent = `${value}${unit}`;
      dotInner.appendChild(inner);
      dotEl.appendChild(dotInner);

      dotEl.addEventListener("mouseenter", () => {
        dotInner.style.transform = "scale(1.15)";
        dotInner.style.boxShadow = `0 0 24px ${color}77`;
      });
      dotEl.addEventListener("mouseleave", () => {
        dotInner.style.transform = "scale(1)";
        dotInner.style.boxShadow = `0 0 14px ${color}55`;
      });
      dotEl.addEventListener("click", () => {
        setSelectedCity(city);
        map.flyTo({ center: city.coordinates, zoom: 6, duration: 1200, essential: true });
      });

      const dotMarker = new mapboxgl.Marker({ element: dotEl, anchor: "center" })
        .setLngLat(city.coordinates)
        .addTo(map);
      markersRef.current.push(dotMarker);

      const labelEl = document.createElement("div");
      labelEl.style.cssText = `
        font-size: 10px;
        font-weight: 600;
        color: #e2e8f0;
        background: rgba(10,16,35,0.9);
        padding: 3px 9px;
        border-radius: 99px;
        white-space: nowrap;
        border: 1px solid rgba(255,255,255,0.13);
        pointer-events: none;
        letter-spacing: 0.2px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.5);
      `;
      labelEl.textContent = city.name;

      const labelMarker = new mapboxgl.Marker({ element: labelEl, anchor: "top", offset: [0, 28] })
        .setLngLat(city.coordinates)
        .addTo(map);
      markersRef.current.push(labelMarker);
    });
  }, [mapLoaded, activeLayer, cityCurrentById]);

  useEffect(() => {
    if (!selectedCity) {
      setCityAlerts([]);
      setSelectedCityWeather(null);
      return;
    }

    Promise.all([
      api.getCityAlerts(selectedCity.id),
      api.getCityWeather(selectedCity.id),
    ])
      .then(([alertsData, weatherData]) => {
        setCityAlerts(alertsData.alerts || []);
        const monthly = weatherData.monthly || [];
        const annualStats = monthly.length
          ? {
              avgTemp: Math.round(
                monthly.reduce((sum, row) => sum + (row.tempAvg ?? 0), 0) / monthly.length,
              ),
              totalRainfall: Math.round(
                monthly.reduce((sum, row) => sum + (row.rainfall ?? 0), 0),
              ),
              avgHumidity: Math.round(
                monthly.reduce((sum, row) => sum + (row.humidity ?? 0), 0) / monthly.length,
              ),
            }
          : null;

        setSelectedCityWeather({
          current: weatherData.current || null,
          annualStats,
        });
      })
      .catch(() => {
        setCityAlerts([]);
        setSelectedCityWeather(null);
      });
  }, [selectedCity]);

  return (
    <div className="relative w-full h-full">
      {/* Mapbox container */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* Layer toggle */}
      <LayerToggle activeLayer={activeLayer} onLayerChange={setActiveLayer} />

      {/* City popup */}
      {selectedCity && (
        <CityPopup
          city={selectedCity}
          current={selectedCityWeather?.current || cityCurrentById[selectedCity.id] || null}
          annualStats={selectedCityWeather?.annualStats || null}
          alerts={cityAlerts}
          onClose={() => setSelectedCity(null)}
        />
      )}

      {/* Legend */}
      <div className="absolute bottom-4 right-4 z-10 bg-[#0f1629]/85 backdrop-blur-md border border-white/10 rounded-xl px-3 py-2.5 text-xs">
        <p className="text-slate-400 font-medium mb-1.5 capitalize">
          {activeLayer === "wind" ? "Wind Speed" : activeLayer} Legend
        </p>
        <div className="flex items-center gap-2">
          <div
            className="h-2 w-24 rounded-full"
            style={{
              background: `linear-gradient(to right, ${layerColorScale[activeLayer].low}, ${layerColorScale[activeLayer].mid}, ${layerColorScale[activeLayer].high})`,
            }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 mt-1">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>

      {/* Map attribution padding fix */}
      <style>{`
        .mapboxgl-ctrl-bottom-left { bottom: 0; left: 0; }
        .mapboxgl-ctrl-bottom-right { bottom: 88px; right: 0; }
        .mapboxgl-ctrl-attrib { background: rgba(15,22,41,0.7) !important; color: #94a3b8 !important; }
        .mapboxgl-ctrl-attrib a { color: #60a5fa !important; }
      `}</style>
    </div>
  );
}
