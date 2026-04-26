import { WorldMap } from "./components/Map/WorldMap";
import { SideNav } from "./components/Navigation/SideNav";
import { CountryNewsSidebar } from "./components/News/CountryNewsSidebar";
import { DashboardProvider } from "./state/DashboardContext";
import "./styles.css";

export default function App() {
  return (
    <DashboardProvider>
      <div className="app-shell">
        <SideNav />
        <main className="dashboard">
          <WorldMap />
          <CountryNewsSidebar />
        </main>
      </div>
    </DashboardProvider>
  );
}
