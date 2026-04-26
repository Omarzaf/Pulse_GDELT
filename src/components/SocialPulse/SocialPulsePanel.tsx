import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_SENTINEL_API_BASE_URL ?? "";

type SignalKey = "reddit" | "wikipedia" | "trends" | "news";

interface SignalHistory {
  date: string;
  social_pulse: number | null;
  reddit: number | null;
  wikipedia: number | null;
  trends: number | null;
  news: number | null;
  level: string;
  signals_elevated: number;
}

interface EvidenceItem {
  title: string;
  url: string;
  source: string;
  sentiment_score?: number;
}

interface PulseData {
  iso3: string;
  latest: {
    social_pulse_score: number;
    pulse_level: string;
    signals_elevated: number;
    reddit_score: number | null;
    wikipedia_score: number | null;
    trends_fear_score: number | null;
    news_sentiment_score: number | null;
    computed_at: string;
  };
  evidence: EvidenceItem[];
  history: SignalHistory[];
}

const LEVEL_COLOR: Record<string, string> = {
  low: "#2e7d5e",
  moderate: "#f5a623",
  elevated: "#e07b20",
  high: "#d0392b"
};

const SIGNAL_COLORS: Record<SignalKey, string> = {
  reddit: "#ff6314",
  wikipedia: "#3366cc",
  trends: "#2e7d5e",
  news: "#9b59b6"
};

const SIGNAL_LABELS: Record<SignalKey, string> = {
  reddit: "Reddit Fear",
  wikipedia: "Wikipedia Spike",
  trends: "Search Fear",
  news: "News Sentiment"
};

function score(value: number | null): number {
  return value ?? 0;
}

function MultiSignalChart({ history, windowSize }: { history: SignalHistory[]; windowSize: 7 | 30 }) {
  const data = windowSize === 7 ? history.slice(-7) : history.slice(-30);
  if (!data.length) {
    return <p className="empty-state">No history yet.</p>;
  }

  const width = 300;
  const height = 90;
  const signals: SignalKey[] = ["reddit", "wikipedia", "trends", "news"];
  const baselineSource = history.slice(-30);
  const averagePulse =
    baselineSource.reduce((total, item) => total + score(item.social_pulse), 0) /
    Math.max(baselineSource.length, 1);
  const averageY = height - (averagePulse / 100) * height;

  const buildPath = (key: SignalKey) => {
    const points = data.map((item, index) => {
      const x = (index / Math.max(data.length - 1, 1)) * width;
      const y = height - (score(item[key]) / 100) * height;
      return `${x},${y}`;
    });
    return `M ${points.join(" L ")}`;
  };

  return (
    <div className="pulse-chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} className="pulse-chart" role="img" aria-label="Social Pulse signals">
        <line
          x1="0"
          y1={averageY}
          x2={width}
          y2={averageY}
          stroke="#b0c4bb"
          strokeWidth="1"
          strokeDasharray="4 3"
        />
        {signals.map((key) => (
          <path
            key={key}
            d={buildPath(key)}
            fill="none"
            stroke={SIGNAL_COLORS[key]}
            strokeWidth="1.5"
            opacity="0.85"
          />
        ))}
      </svg>
      <div className="pulse-legend">
        {signals.map((key) => (
          <span key={key} className="pulse-legend-item">
            <span className="pulse-legend-dot" style={{ background: SIGNAL_COLORS[key] }} />
            {SIGNAL_LABELS[key]}
          </span>
        ))}
      </div>
    </div>
  );
}

function EvidenceDrawer({ items }: { items: EvidenceItem[] }) {
  const [open, setOpen] = useState(false);

  if (!items.length) {
    return null;
  }

  return (
    <div className="evidence-drawer">
      <button className="evidence-toggle" onClick={() => setOpen((value) => !value)} type="button">
        {open ? "Hide" : "Show"} contributing signals ({items.length})
      </button>
      {open ? (
        <ul className="evidence-list">
          {items.map((item, index) => (
            <li key={`${item.url}-${index}`} className="evidence-item">
              <a href={item.url} target="_blank" rel="noreferrer" className="evidence-title">
                {item.title}
              </a>
              <span className="evidence-source">{item.source}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function SocialPulsePanel({ iso3 }: { iso3: string }) {
  const [data, setData] = useState<PulseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [windowSize, setWindowSize] = useState<7 | 30>(30);

  useEffect(() => {
    if (!iso3 || !API_BASE) {
      return;
    }

    let active = true;
    setLoading(true);
    fetch(`${API_BASE}/api/countries/${iso3}/social-pulse?days=30`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
      .then((payload: PulseData) => {
        if (active) {
          setData(payload);
        }
      })
      .catch(() => {
        if (active) {
          setData(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [iso3]);

  if (!API_BASE) {
    return null;
  }

  const levelColor = data ? (LEVEL_COLOR[data.latest.pulse_level] ?? "#65756f") : "#65756f";

  return (
    <div className="social-pulse-panel">
      <div className="pulse-header">
        <span className="pulse-section-label">Social Pulse</span>
        <div className="pulse-window-toggle">
          <button
            className={`toggle-btn ${windowSize === 7 ? "active" : ""}`}
            onClick={() => setWindowSize(7)}
            type="button"
          >
            7d
          </button>
          <button
            className={`toggle-btn ${windowSize === 30 ? "active" : ""}`}
            onClick={() => setWindowSize(30)}
            type="button"
          >
            30d
          </button>
        </div>
      </div>

      {loading ? <p className="empty-state">Analyzing public signals...</p> : null}

      {!loading && data ? (
        <>
          <div className="pulse-score-row">
            <span className="pulse-score-value" style={{ color: levelColor }}>
              {Math.round(data.latest.social_pulse_score)}
            </span>
            <div className="pulse-score-meta">
              <span className="pulse-level-badge" style={{ background: levelColor }}>
                {data.latest.pulse_level.toUpperCase()}
              </span>
              <span className="pulse-signals-count">{data.latest.signals_elevated}/4 signals elevated</span>
            </div>
          </div>

          <MultiSignalChart history={data.history} windowSize={windowSize} />

          <div className="pulse-chips">
            {[
              { key: "reddit" as const, label: "Reddit", value: data.latest.reddit_score },
              { key: "wikipedia" as const, label: "Wiki", value: data.latest.wikipedia_score },
              { key: "trends" as const, label: "Search", value: data.latest.trends_fear_score },
              { key: "news" as const, label: "News", value: data.latest.news_sentiment_score }
            ].map(({ key, label, value }) => (
              <span key={key} className="pulse-chip">
                <span className="pulse-chip-dot" style={{ background: SIGNAL_COLORS[key] }} />
                {label}: <strong>{value != null ? Math.round(value) : "-"}</strong>
              </span>
            ))}
          </div>

          <EvidenceDrawer items={data.evidence} />

          <p className="pulse-updated">
            Updated {new Date(data.latest.computed_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
          </p>
        </>
      ) : null}

      {!loading && !data ? <p className="empty-state">Social pulse data unavailable.</p> : null}
    </div>
  );
}
