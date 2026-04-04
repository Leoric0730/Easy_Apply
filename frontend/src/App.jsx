import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import SearchPage from "./pages/SearchPage";
import BatchPage from "./pages/BatchPage";
import ReviewPage from "./pages/ReviewPage";
import HistoryPage from "./pages/HistoryPage";

const navStyle = {
  display: "flex",
  gap: 16,
  padding: "16px 24px",
  borderBottom: "1px solid #ddd",
  background: "#fafafa",
};

const linkStyle = ({ isActive }) => ({
  fontWeight: isActive ? "bold" : "normal",
  textDecoration: "none",
  color: isActive ? "#1a73e8" : "#333",
});

export default function App() {
  return (
    <BrowserRouter>
      <nav style={navStyle}>
        <NavLink to="/" style={linkStyle}>Search</NavLink>
        <NavLink to="/batch" style={linkStyle}>New Batch</NavLink>
        <NavLink to="/review" style={linkStyle}>Ready to Review</NavLink>
        <NavLink to="/history" style={linkStyle}>History</NavLink>
      </nav>
      <main style={{ padding: 24 }}>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/batch" element={<BatchPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
