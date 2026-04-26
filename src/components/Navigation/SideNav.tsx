const NAV_ITEMS = ["World Dashboard", "Sources", "Time Series"] as const;

export function SideNav() {
  return (
    <nav className="side-nav" aria-label="Primary">
      <div className="brand">Sentinel Atlas</div>
      <ul>
        {NAV_ITEMS.map((item, index) => (
          <li key={item}>
            <button className={index === 0 ? "nav-item active" : "nav-item"} type="button">
              {item}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export { NAV_ITEMS };
