import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { getLatestCountryNews } from "../data/adapters/countryNewsAdapter";
import type { CountryLatestNewsResponse } from "../types/news";

interface DashboardContextValue {
  selectedCountryIso3: string | null;
  hoveredCountryIso3: string | null;
  selectedLatestNews: CountryLatestNewsResponse | null;
  hoverNews: CountryLatestNewsResponse | null;
  setSelectedCountryIso3: (iso3: string) => void;
  setHoveredCountryIso3: (iso3: string | null) => void;
}

const DashboardContext = createContext<DashboardContextValue | undefined>(undefined);

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [selectedCountryIso3, setSelectedCountryIso3] = useState<string | null>(null);
  const [hoveredCountryIso3, setHoveredCountryIso3] = useState<string | null>(null);
  const [selectedLatestNews, setSelectedLatestNews] = useState<CountryLatestNewsResponse | null>(null);
  const [hoverNews, setHoverNews] = useState<CountryLatestNewsResponse | null>(null);

  useEffect(() => {
    if (!hoveredCountryIso3) {
      setHoverNews(null);
      return;
    }

    let active = true;
    getLatestCountryNews(hoveredCountryIso3, 48, 3).then((response) => {
      if (active) {
        setHoverNews(response);
      }
    });
    return () => {
      active = false;
    };
  }, [hoveredCountryIso3]);

  useEffect(() => {
    if (!selectedCountryIso3) {
      setSelectedLatestNews(null);
      return;
    }

    let active = true;
    getLatestCountryNews(selectedCountryIso3, 48, 5).then((latest) => {
      if (active) {
        setSelectedLatestNews(latest);
      }
    });
    return () => {
      active = false;
    };
  }, [selectedCountryIso3]);

  const value = useMemo(
    () => ({
      selectedCountryIso3,
      hoveredCountryIso3,
      selectedLatestNews,
      hoverNews,
      setSelectedCountryIso3,
      setHoveredCountryIso3
    }),
    [hoverNews, hoveredCountryIso3, selectedCountryIso3, selectedLatestNews]
  );

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used inside DashboardProvider");
  }
  return context;
}
