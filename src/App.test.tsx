import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const mockNews = vi.hoisted(() => {
  const latestArticle = {
    id: 10,
    source_name: "WHO Disease Outbreak News",
    source_key: "who_don",
    source_url: "https://www.who.int/example",
    headline_original: "United States public report",
    headline_en: "United States public report",
    summary: null,
    language: "en",
    translation_status: "not_needed",
    country_iso3: "USA",
    country_name: "United States",
    published_at: "2026-04-25T14:00:00Z",
    ingested_at: "2026-04-25T14:01:00Z",
    source_credibility: "high",
    credibility_label: "Highly Reliable" as const
  };
  return {
    latestArticle
  };
});

vi.mock("./data/adapters/countryNewsAdapter", () => ({
  getLatestCountryNews: vi.fn(async (iso3: string, _hours: number, limit: number) => ({
    iso3,
    connected: true,
    hours: 48,
    limit,
    articles: limit === 3 ? [mockNews.latestArticle] : [mockNews.latestArticle],
    empty_state: null
  }))
}));

describe("World dashboard news UI", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders hover news headline state for the hovered country", async () => {
    render(<App />);

    fireEvent.mouseEnter(screen.getByLabelText("USA map region"));

    expect(await screen.findByText("United States public report")).toBeInTheDocument();
    expect(screen.getByText(/WHO Disease Outbreak News/)).toBeInTheDocument();
  });

  it("renders selected-country latest news and replaces historical news", async () => {
    render(<App />);

    fireEvent.click(screen.getByLabelText("USA map region"));

    const sidebar = screen.getByLabelText("Selected country news");
    await waitFor(() => {
      expect(within(sidebar).getByText("United States public report")).toBeInTheDocument();
    });
    expect(within(sidebar).queryByText("Older United States public report")).not.toBeInTheDocument();
    expect(within(sidebar).queryByText("Historical")).not.toBeInTheDocument();
    expect(within(sidebar).getAllByText("Highly Reliable")).toHaveLength(1);
  });

  it("does not render synthetic simulation or unsupported metric copy", () => {
    render(<App />);

    const copy = document.body.textContent ?? "";
    expect(copy).not.toMatch(/fake|synthetic|Rt|R0|forecast|simulator|disease risk|risk score/i);
    expect(copy).not.toMatch(/country-risk|dropdown/i);
  });
});
