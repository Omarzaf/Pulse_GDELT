import { afterEach, describe, expect, it, vi } from "vitest";

import {
  CONNECTED_LATEST_EMPTY_STATE,
  DISCONNECTED_EMPTY_STATE,
  getLatestCountryNews
} from "./countryNewsAdapter";

const article = {
  id: 1,
  source_name: "ReliefWeb",
  source_key: "reliefweb",
  source_url: "https://reliefweb.int/report/example",
  headline_original: "Original headline",
  headline_en: "Translated public report",
  summary: null,
  language: "en",
  translation_status: "not_needed",
  country_iso3: "USA",
  country_name: "United States",
  published_at: "2026-04-25T12:00:00Z",
  ingested_at: "2026-04-25T12:01:00Z",
  source_credibility: "high",
  credibility_label: "Highly Reliable" as const
};

describe("countryNewsAdapter", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("returns backend latest news when the API is configured", async () => {
    vi.stubEnv("VITE_SENTINEL_API_BASE_URL", "http://localhost:8000");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        iso3: "USA",
        connected: true,
        hours: 48,
        limit: 5,
        articles: [article],
        empty_state: null
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getLatestCountryNews("usa");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/countries/USA/news/latest?hours=48&limit=5"
    );
    expect(result.articles).toHaveLength(1);
    expect(result.articles[0].headline_en).toBe("Translated public report");
  });

  it("falls back when the backend is unavailable", async () => {
    vi.stubEnv("VITE_SENTINEL_API_BASE_URL", "http://localhost:8000");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const result = await getLatestCountryNews("USA");

    expect(result.connected).toBe(false);
    expect(result.empty_state).toBe(DISCONNECTED_EMPTY_STATE);
    expect(result.articles).toEqual([]);
  });

  it("preserves connected empty state from the backend", async () => {
    vi.stubEnv("VITE_SENTINEL_API_BASE_URL", "http://localhost:8000");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          iso3: "USA",
          connected: true,
          hours: 48,
          limit: 5,
          articles: [],
          empty_state: CONNECTED_LATEST_EMPTY_STATE
        })
      })
    );

    const result = await getLatestCountryNews("USA");

    expect(result.connected).toBe(true);
    expect(result.empty_state).toBe(CONNECTED_LATEST_EMPTY_STATE);
    expect(result.articles).toEqual([]);
  });
});
