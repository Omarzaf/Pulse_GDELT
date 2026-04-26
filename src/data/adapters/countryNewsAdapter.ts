import type { CountryLatestNewsResponse, CountryNewsHistoryResponse } from "../../types/news";

const DISCONNECTED_EMPTY_STATE = "No news feed connected yet.";
const CONNECTED_LATEST_EMPTY_STATE = "No public news reports found in the last 48 hours.";

function apiBaseUrl(): string | null {
  const configured = import.meta.env.VITE_SENTINEL_API_BASE_URL as string | undefined;
  return configured ? configured.replace(/\/$/, "") : null;
}

function fallbackLatest(iso3: string, hours: number, limit: number): CountryLatestNewsResponse {
  return {
    iso3,
    connected: false,
    hours,
    limit,
    articles: [],
    empty_state: DISCONNECTED_EMPTY_STATE
  };
}

function fallbackHistory(iso3: string, days: number, limit: number): CountryNewsHistoryResponse {
  return {
    iso3,
    connected: false,
    days,
    limit,
    articles: [],
    empty_state: DISCONNECTED_EMPTY_STATE
  };
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`News API request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getLatestCountryNews(
  iso3: string,
  hours = 48,
  limit = 5
): Promise<CountryLatestNewsResponse> {
  const baseUrl = apiBaseUrl();
  const countryIso3 = iso3.toUpperCase();
  if (!baseUrl) {
    return fallbackLatest(countryIso3, hours, limit);
  }

  try {
    const params = new URLSearchParams({ hours: String(hours), limit: String(limit) });
    const result = await fetchJson<CountryLatestNewsResponse>(
      `${baseUrl}/api/countries/${countryIso3}/news/latest?${params.toString()}`
    );
    return {
      ...result,
      empty_state:
        result.empty_state ??
        (result.connected && result.articles.length === 0 ? CONNECTED_LATEST_EMPTY_STATE : null)
    };
  } catch {
    return fallbackLatest(countryIso3, hours, limit);
  }
}

export async function getCountryNewsHistory(
  iso3: string,
  days = 30,
  limit = 50
): Promise<CountryNewsHistoryResponse> {
  const baseUrl = apiBaseUrl();
  const countryIso3 = iso3.toUpperCase();
  if (!baseUrl) {
    return fallbackHistory(countryIso3, days, limit);
  }

  try {
    const params = new URLSearchParams({ days: String(days), limit: String(limit) });
    return fetchJson<CountryNewsHistoryResponse>(
      `${baseUrl}/api/countries/${countryIso3}/news/history?${params.toString()}`
    );
  } catch {
    return fallbackHistory(countryIso3, days, limit);
  }
}

export { CONNECTED_LATEST_EMPTY_STATE, DISCONNECTED_EMPTY_STATE };
