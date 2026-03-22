import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { australianCities } from "../../data/australianCities";
import { mockWeatherData, getAlertsForCity } from "../../data/mockWeatherData";
import LayerToggle from "./LayerToggle";
import CityPopup from "./CityPopup";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || "YOUR_MAPBOX_TOKEN";

// Colors for each layer value
const layerColorScale = {
  temperature: { low: "#3b82f6", mid: "#f59e0b", high: "#ef4444" },
  rainfall: { low: "#e2e8f0", mid: "#60a5fa", high: "#1d4ed8" },
  humidity: { low: "#fef3c7", mid: "#34d399", high: "#059669" },
  wind: { low: "#c4b5fd", mid: "#a78bfa", high: "#7c3aed" },
};

const getLayerValue = (cityId, layer) => {
  const monthly = mockWeatherData[cityId]?.monthly || [];
  if (!monthly.length) return 0;
  switch (layer) {
    case "temperature":
      return Math.round(
        monthly.reduce((s, m) => s + m.tempAvg, 0) / monthly.length,
      );
    case "rainfall":
      return Math.round(
        monthly.reduce((s, m) => s + m.rainfall, 0) / monthly.length,
      );
    case "humidity":
      return Math.round(
        monthly.reduce((s, m) => s + m.humidity, 0) / monthly.length,
      );
    case "wind":
      return Math.round(
        monthly.reduce((s, m) => s + m.windSpeed, 0) / monthly.length,
      );
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

const getMarkerColor = (value, layer) => {
  const ranges = {
    temperature: [8, 24],
    rainfall: [3, 380],
    humidity: [40, 80],
    wind: [11, 24],
  };
  const [min, max] = ranges[layer] || [0, 100];
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

  // Initialize map
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

  // Add/update city markers
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;

    // Remove old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    australianCities.forEach((city) => {
      const value = getLayerValue(city.id, activeLayer);
      const color = getMarkerColor(value, activeLayer);
      const unit = getLayerUnit(activeLayer);

      // Single element — only the dot, no overflow children.
      // Anchor "center" pins the exact centre of this 48x48 element to the coordinate.
      const el = document.createElement("div");
      el.className = "city-marker";
      el.style.cssText = `
        cursor: pointer;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: ${color}22;
        border: 2px solid ${color};
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        box-shadow: 0 0 16px ${color}44;
      `;

      const inner = document.createElement("div");
      inner.style.cssText = `
        font-size: 10px;
        font-weight: 700;
        color: white;
        text-align: center;
        line-height: 1.1;
        pointer-events: none;
      `;
      inner.textContent = `${value}${unit}`;

      const cityLabel = document.createElement("div");
      cityLabel.style.cssText = `
        font-size: 8px;
        font-weight: 600;
        color: rgba(255,255,255,0.7);
        text-align: center;
        pointer-events: none;
        margin-top: 1px;
      `;
      cityLabel.textContent = city.name;

      el.appendChild(inner);
      el.appendChild(cityLabel);
      const dot = el; // alias for hover handlers below

      el.addEventListener("mouseenter", () => {
        dot.style.transform = "scale(1.15)";
        dot.style.boxShadow = `0 0 24px ${color}66`;
      });
      el.addEventListener("mouseleave", () => {
        dot.style.transform = "scale(1)";
        dot.style.boxShadow = `0 0 16px ${color}44`;
      });

      el.addEventListener("click", () => {
        setSelectedCity(city);
        map.flyTo({
          center: city.coordinates,
          zoom: 6,
          duration: 1200,
          essential: true,
        });
      });

      const marker = new mapboxgl.Marker({ element: el, anchor: "center" })
        .setLngLat(city.coordinates)
        .addTo(map);

      markersRef.current.push(marker);
    });
  }, [mapLoaded, activeLayer]);

  const cityAlerts = selectedCity ? getAlertsForCity(selectedCity.id) : [];

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
          alerts={cityAlerts}
          onClose={() => setSelectedCity(null)}
        />
      )}

      {/* Legend */}
      <div className="absolute bottom-10 right-4 z-10 bg-[#0f1629]/85 backdrop-blur-md border border-white/10 rounded-xl px-3 py-2.5 text-xs">
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
        .mapboxgl-ctrl-bottom-right { bottom: 0; right: 0; }
        .mapboxgl-ctrl-attrib { background: rgba(15,22,41,0.7) !important; color: #94a3b8 !important; }
        .mapboxgl-ctrl-attrib a { color: #60a5fa !important; }
      `}</style>
    </div>
  );
}
