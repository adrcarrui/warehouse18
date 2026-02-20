import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import ItemsPage from "./pages/ItemsPage";
import UsersPage from "./pages/UsersPage";
import LocationsPage from "./pages/LocationsPage";
import StockContainersPage from "./pages/StockContainersPage";
import {MovementsPage} from "./pages/Movements/MovementsPage";
import RFIDMonitorPage from "./pages/RFIDMonitorPage";
import DashboardPage from "./pages/Dashboard";
import "./index.css"

/*
function Home() {
  return (
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <h2 style={{ marginTop: 0 }}>Warehouse18 UI</h2>
      <ul>
        <li><Link to="/items">Items</Link></li>
        <li><Link to="/users">Users</Link></li>
        <li><Link to="/locations">Locations</Link></li>
        <li><Link to="/stock-containers">StockContainers</Link></li>
        <li><Link to="/movements">Movements</Link></li>
        <li><Link to="/rfid-monitor">RFIDMonitor</Link></li>
        <li><Link to="/dashboard">Dashboard</Link></li>
      </ul>
    </div>
  );
}
  */

ReactDOM.createRoot(document.getElementById("root")!).render(
  //<React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/items" element={<ItemsPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/locations" element={<LocationsPage />} />
        <Route path="/stock-containers" element={<StockContainersPage />} />
        <Route path="/movements" element={<MovementsPage />} />
        <Route path="/rfid-monitor" element={<RFIDMonitorPage />} />
      </Routes>
    </BrowserRouter>
  //</React.StrictMode>
);
