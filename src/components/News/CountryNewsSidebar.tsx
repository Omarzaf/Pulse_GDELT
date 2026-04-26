import { countryNameForIso3 } from "../../data/countries";
import { useDashboard } from "../../state/DashboardContext";
import type { NewsArticle } from "../../types/news";
import { SocialPulsePanel } from "../SocialPulse/SocialPulsePanel";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

function NewsList({ articles }: { articles: NewsArticle[] }) {
  return (
    <ul className="news-list">
      {articles.map((article) => (
        <li className="news-item" key={article.id}>
          <a href={article.source_url} rel="noreferrer" target="_blank">
            {article.headline_en}
          </a>
          <div className="news-meta">
            <span>{article.source_name}</span>
            <span>{formatDate(article.published_at)}</span>
            <span>{article.credibility_label}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function CountryNewsSidebar() {
  const { selectedCountryIso3, selectedLatestNews } = useDashboard();
  const countryName = countryNameForIso3(selectedCountryIso3);

  return (
    <aside className="country-news-sidebar" aria-label="Selected country news">
      <header>
        <span>Selected Country</span>
        <h2>{countryName}</h2>
      </header>

      <section>
        <h3>Latest 48h</h3>
        {selectedLatestNews?.articles.length ? (
          <NewsList articles={selectedLatestNews.articles} />
        ) : (
          <p className="empty-state">
            {selectedLatestNews?.empty_state ??
              (selectedCountryIso3 ? "No public news reports found in the last 48 hours." : "No country selected.")}
          </p>
        )}
      </section>

      {selectedCountryIso3 ? <SocialPulsePanel iso3={selectedCountryIso3} /> : null}
    </aside>
  );
}
