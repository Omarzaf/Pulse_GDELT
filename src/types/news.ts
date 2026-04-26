export type CredibilityLabel =
  | "Highly Reliable"
  | "Reliable"
  | "Moderate"
  | "Low Confidence"
  | "Unverified";

export interface NewsArticle {
  id: number;
  source_name: string;
  source_key: string;
  source_url: string;
  headline_original: string;
  headline_en: string;
  summary?: string | null;
  language?: string | null;
  translation_status: string;
  country_iso3?: string | null;
  country_name?: string | null;
  published_at: string;
  ingested_at: string;
  source_credibility: string;
  credibility_label: CredibilityLabel;
}

export interface CountryLatestNewsResponse {
  iso3: string;
  connected: boolean;
  hours: number;
  limit: number;
  articles: NewsArticle[];
  empty_state?: string | null;
}

export interface CountryNewsHistoryResponse {
  iso3: string;
  connected: boolean;
  days: number;
  limit: number;
  articles: NewsArticle[];
  empty_state?: string | null;
}
