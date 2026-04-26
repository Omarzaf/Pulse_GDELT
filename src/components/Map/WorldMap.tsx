import { useEffect, useState } from "react";

import { ATLAS_COUNTRIES } from "../../data/countries";
import { useDashboard } from "../../state/DashboardContext";

const API_BASE = import.meta.env.VITE_SENTINEL_API_BASE_URL ?? "";

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

export function WorldMap() {
  const [elevatedCountries, setElevatedCountries] = useState<Set<string>>(new Set());
  const {
    hoveredCountryIso3,
    hoverNews,
    selectedCountryIso3,
    setHoveredCountryIso3,
    setSelectedCountryIso3
  } = useDashboard();
  const hoveredCountry = ATLAS_COUNTRIES.find((country) => country.iso3 === hoveredCountryIso3);

  useEffect(() => {
    if (!API_BASE) {
      return;
    }

    let active = true;
    fetch(`${API_BASE}/api/countries/elevated?threshold=55`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
      .then((data: { elevated: Array<{ iso3: string }> }) => {
        if (active) {
          setElevatedCountries(new Set(data.elevated.map((country) => country.iso3)));
        }
      })
      .catch(() => {});

    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="map-panel" aria-label="World Dashboard">
      <svg className="world-map" viewBox="0 0 960 460" role="img" aria-label="Country map">
        <rect className="ocean" x="0" y="0" width="960" height="460" rx="0" />
        {ATLAS_COUNTRIES.map((country) => (
          <g key={country.iso3}>
            <rect
              aria-label={`${country.iso3} map region`}
              className={[
                "country",
                country.iso3 === selectedCountryIso3 ? "selected" : "",
                elevatedCountries.has(country.iso3) ? "pulse-alert" : ""
              ]
                .filter(Boolean)
                .join(" ")}
              height={country.height}
              onClick={() => setSelectedCountryIso3(country.iso3)}
              onFocus={() => setHoveredCountryIso3(country.iso3)}
              onMouseEnter={() => setHoveredCountryIso3(country.iso3)}
              onMouseLeave={() => setHoveredCountryIso3(null)}
              role="button"
              tabIndex={0}
              width={country.width}
              x={country.x}
              y={country.y}
            />
            <text className="country-label" x={country.x + country.width / 2} y={country.y + country.height / 2}>
              {country.iso3}
            </text>
          </g>
        ))}
      </svg>

      {hoveredCountry ? (
        <aside className="hover-news" aria-live="polite">
          <div className="hover-country">{hoveredCountry.name}</div>
          {hoverNews?.articles.length ? (
            <ul>
              {hoverNews.articles.slice(0, 3).map((article) => (
                <li key={article.id}>
                  <strong>{article.headline_en}</strong>
                  <span>
                    {article.source_name} · {formatTime(article.published_at)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p>{hoverNews?.empty_state ?? "No public news reports found in the last 48 hours."}</p>
          )}
        </aside>
      ) : null}
    </section>
  );
}
