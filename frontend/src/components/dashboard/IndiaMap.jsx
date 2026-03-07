import { useState, useMemo, useCallback } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
} from "react-simple-maps";

const INDIA_TOPO =
  "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson";

/* Real lat/lng coordinates for Indian cities */
const CITY_COORDS = {
  Mumbai:             [72.8777, 19.0760],
  Delhi:              [77.1025, 28.7041],
  Bengaluru:          [77.5946, 12.9716],
  Bangalore:          [77.5946, 12.9716],
  Hyderabad:          [78.4867, 17.3850],
  Pune:               [73.8567, 18.5204],
  Chennai:            [80.2707, 13.0827],
  Jaipur:             [75.7873, 26.9124],
  Indore:             [75.8577, 22.7196],
  Lucknow:            [80.9462, 26.8467],
  Bhopal:             [77.4126, 23.2599],
  Surat:              [72.8311, 21.1702],
  Nagpur:             [79.0882, 21.1458],
  Patna:              [85.1376, 25.6093],
  Coimbatore:         [76.9558, 11.0168],
  Kochi:              [76.2673, 9.9312],
  Chandigarh:         [76.7794, 30.7333],
  Kolkata:            [88.3639, 22.5726],
  Ahmedabad:          [72.5714, 23.0225],
  Visakhapatnam:      [83.2185, 17.6868],
  Thiruvananthapuram: [76.9366, 8.5241],
  Noida:              [77.3910, 28.5355],
  Gurgaon:            [77.0266, 28.4595],
  Gurugram:           [77.0266, 28.4595],
  Vadodara:           [73.1812, 22.3072],
  Guwahati:           [91.7362, 26.1445],
  Mangalore:          [74.8560, 12.9141],
  Dehradun:           [78.0322, 30.3165],
  Bhubaneswar:        [85.8245, 20.2961],
  Ranchi:             [85.3096, 23.3441],
  Mysore:             [76.6394, 12.2958],
  Trivandrum:         [76.9366, 8.5241],
};

const DEFAULT_CENTER = [79, 22.5];
const DEFAULT_ZOOM = 1;
const ZOOMED_ZOOM = 3.5;

/* Smooth zoom/pan CSS transition for ZoomableGroup's inner <g> */
const ZOOM_TRANSITION_STYLE = `
  .rsm-zoomable-group {
    transition: transform 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
`;

function normalizeName(name) {
  return name.toLowerCase().replace(/[^a-z]/g, "");
}

function findCityCoords(cityName) {
  const norm = normalizeName(cityName);
  for (const [key, coords] of Object.entries(CITY_COORDS)) {
    if (normalizeName(key) === norm) return { name: key, coordinates: coords };
  }
  return null;
}

export default function IndiaMap({ cityData = [], selectedCity, onCitySelect }) {
  const [hoveredCity, setHoveredCity] = useState(null);
  const [position, setPosition] = useState({ coordinates: DEFAULT_CENTER, zoom: DEFAULT_ZOOM });

  const plottableCities = useMemo(
    () =>
      cityData
        .map((cd) => {
          const coords = findCityCoords(cd.city);
          if (!coords) return null;
          return { ...cd, ...coords, displayName: coords.name };
        })
        .filter(Boolean),
    [cityData]
  );

  const maxTotal = Math.max(...plottableCities.map((c) => c.total_jobs), 1);

  /* When user drags / scrolls, update position freely */
  const handleMoveEnd = useCallback((pos) => {
    setPosition(pos);
  }, []);

  /* Click a city → zoom to it; click again → zoom out */
  const handleCityClick = useCallback(
    (cityName) => {
      if (selectedCity === cityName) {
        onCitySelect(null);
        setPosition({ coordinates: DEFAULT_CENTER, zoom: DEFAULT_ZOOM });
      } else {
        onCitySelect(cityName);
        const coords = findCityCoords(cityName);
        if (coords) {
          setPosition({ coordinates: coords.coordinates, zoom: ZOOMED_ZOOM });
        }
      }
    },
    [selectedCity, onCitySelect]
  );

  /* Click background → deselect & reset view */
  const handleBgClick = useCallback(() => {
    if (selectedCity) {
      onCitySelect(null);
      setPosition({ coordinates: DEFAULT_CENTER, zoom: DEFAULT_ZOOM });
    }
  }, [selectedCity, onCitySelect]);

  return (
    <div
      className="w-full h-full relative overflow-hidden"
      style={{ cursor: selectedCity ? "zoom-out" : "grab" }}
    >
      {/* Inject smooth transition CSS */}
      <style>{ZOOM_TRANSITION_STYLE}</style>

      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ center: [79, 22.5], scale: 1200 }}
        width={600}
        height={700}
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          <filter id="cityGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="activeGlow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <ZoomableGroup
          center={position.coordinates}
          zoom={position.zoom}
          onMoveEnd={handleMoveEnd}
          minZoom={0.8}
          maxZoom={8}
          translateExtent={[
            [-100, -150],
            [700, 850],
          ]}
        >
          {/* State geometries */}
          <Geographies geography={INDIA_TOPO}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rpisvgId || geo.properties.ST_NM}
                  geography={geo}
                  fill="rgba(151,168,122,0.10)"
                  stroke="rgba(151,168,122,0.40)"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: "none", transition: "fill 0.3s ease" },
                    hover: {
                      fill: "rgba(151,168,122,0.22)",
                      stroke: "rgba(151,168,122,0.55)",
                      outline: "none",
                      transition: "fill 0.3s ease",
                    },
                    pressed: { outline: "none" },
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleBgClick();
                  }}
                />
              ))
            }
          </Geographies>

          {/* City markers */}
          {plottableCities.map((city) => {
            const isActive = selectedCity === city.displayName;
            const isHovered = hoveredCity === city.displayName;
            const sizeFactor = Math.max(0.4, Math.min(1, city.total_jobs / maxTotal));
            const baseR = 3.5 + sizeFactor * 4;
            const r = isActive ? baseR * 1.5 : isHovered ? baseR * 1.25 : baseR;

            return (
              <Marker
                key={city.displayName}
                coordinates={city.coordinates}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCityClick(city.displayName);
                }}
                onMouseEnter={() => setHoveredCity(city.displayName)}
                onMouseLeave={() => setHoveredCity(null)}
                style={{ cursor: "pointer" }}
              >
                {/* Pulse rings for active */}
                {isActive && (
                  <>
                    <circle r={r * 3} fill="none" stroke="#97A87A" strokeWidth={0.5} opacity={0.4}>
                      <animate attributeName="r" from={r * 1.5} to={r * 3.5} dur="1.6s" repeatCount="indefinite" />
                      <animate attributeName="opacity" from="0.5" to="0" dur="1.6s" repeatCount="indefinite" />
                    </circle>
                    <circle r={r * 2.2} fill="none" stroke="#97A87A" strokeWidth={0.3} opacity={0.25}>
                      <animate attributeName="r" from={r * 1.2} to={r * 2.6} dur="1.6s" repeatCount="indefinite" begin="0.4s" />
                      <animate attributeName="opacity" from="0.35" to="0" dur="1.6s" repeatCount="indefinite" begin="0.4s" />
                    </circle>
                  </>
                )}

                {/* Outer glow ring */}
                <circle
                  r={r * 2}
                  fill="rgba(151,168,122,0.10)"
                  filter={isActive ? "url(#activeGlow)" : undefined}
                  style={{ transition: "r 0.3s ease, fill 0.3s ease" }}
                />

                {/* Main dot */}
                <circle
                  r={r}
                  fill={
                    isActive
                      ? "#97A87A"
                      : isHovered
                      ? "rgba(151,168,122,0.90)"
                      : "rgba(151,168,122,0.65)"
                  }
                  stroke={isActive ? "#dad7cd" : "rgba(218,215,205,0.35)"}
                  strokeWidth={isActive ? 0.6 : 0.4}
                  filter={isActive || isHovered ? "url(#cityGlow)" : undefined}
                  style={{ transition: "r 0.3s ease, fill 0.3s ease, stroke 0.3s ease" }}
                />

                {/* Inner bright dot */}
                <circle
                  r={r * 0.3}
                  fill={isActive ? "#FFFFFF" : "#dad7cd"}
                  opacity={isActive ? 1 : 0.75}
                  style={{ transition: "r 0.3s ease" }}
                />

                {/* Label — always shown, large & readable */}
                <text
                  textAnchor="middle"
                  y={-r - 5}
                  fill={isActive ? "#FFFFFF" : isHovered ? "#FFFFFF" : "rgba(218,215,205,0.92)"}
                  fontSize={isActive ? 10 : isHovered ? 9 : 7.5}
                  fontWeight={isActive ? 700 : isHovered ? 600 : 500}
                  letterSpacing={0.4}
                  paintOrder="stroke"
                  stroke="rgba(18,20,18,0.9)"
                  strokeWidth={2.5}
                  strokeLinejoin="round"
                  style={{
                    pointerEvents: "none",
                    transition: "font-size 0.3s ease, fill 0.3s ease",
                  }}
                >
                  {city.displayName}
                </text>
              </Marker>
            );
          })}
        </ZoomableGroup>
      </ComposableMap>
    </div>
  );
}
