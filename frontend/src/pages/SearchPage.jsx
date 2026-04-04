import { useState } from "react";
import api from "../api/client";

const PLATFORMS = ["linkedin", "handshake", "boss_zhipin"];

export default function SearchPage() {
  const [selectedPlatforms, setSelectedPlatforms] = useState(["linkedin"]);
  const [keywords, setKeywords] = useState("");
  const [location, setLocation] = useState("");
  const [searching, setSearching] = useState(false);
  const [message, setMessage] = useState("");

  const togglePlatform = (platform) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  const handleSearch = async () => {
    setSearching(true);
    setMessage("");
    try {
      const res = await api.post("/jobs/search", {
        platforms: selectedPlatforms,
        keywords,
        location,
      });
      setMessage(`Search complete: ${res.data.jobs_found} jobs found`);
    } catch (err) {
      setMessage("Search failed: " + err.message);
    }
    setSearching(false);
  };

  return (
    <div>
      <h2>Search Configuration</h2>

      <div>
        <h3>Platforms</h3>
        {PLATFORMS.map((p) => (
          <label key={p} style={{ marginRight: 16 }}>
            <input
              type="checkbox"
              checked={selectedPlatforms.includes(p)}
              onChange={() => togglePlatform(p)}
            />
            {" "}{p}
          </label>
        ))}
      </div>

      <div style={{ marginTop: 16 }}>
        <input
          placeholder="Keywords (e.g. MLE, AI Engineer)"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          style={{ marginRight: 8, padding: 8, width: 250 }}
        />
        <input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          style={{ marginRight: 8, padding: 8, width: 200 }}
        />
      </div>

      <button
        onClick={handleSearch}
        disabled={searching || selectedPlatforms.length === 0}
        style={{ marginTop: 16, padding: "8px 24px" }}
      >
        {searching ? "Searching..." : "Search Now"}
      </button>

      {message && <p style={{ marginTop: 8 }}>{message}</p>}
    </div>
  );
}
