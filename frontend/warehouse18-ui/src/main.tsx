import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import ItemsPage from "./pages/ItemsPage";

function Home() {
  return (
    <div style={{ padding: 16, fontFamily: "system-ui" }}>
      <h2 style={{ marginTop: 0 }}>Warehouse18 UI</h2>
      <ul>
        <li><Link to="/items">Items</Link></li>
      </ul>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  //<React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/items" element={<ItemsPage />} />
      </Routes>
    </BrowserRouter>
  //</React.StrictMode>
);
