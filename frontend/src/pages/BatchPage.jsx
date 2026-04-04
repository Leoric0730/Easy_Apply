import { useState, useEffect } from "react";
import api from "../api/client";

export default function BatchPage() {
  const [jobs, setJobs] = useState([]);
  const [selected, setSelected] = useState(new Set());

  useEffect(() => {
    api.get("/jobs/?status=new").then((res) => setJobs(res.data.jobs));
  }, []);

  const toggleSelect = (jobId) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(jobId) ? next.delete(jobId) : next.add(jobId);
      return next;
    });
  };

  const handleApply = async () => {
    const jobIds = Array.from(selected);
    await api.post("/applications/fill", {
      job_ids: jobIds,
      profile_id: 1,
    });
    alert(`Filling ${jobIds.length} applications`);
  };

  return (
    <div>
      <h2>New Batch</h2>
      {jobs.length === 0 ? (
        <p>No new jobs. Run a search first.</p>
      ) : (
        <>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th>Select</th>
                <th>Title</th>
                <th>Company</th>
                <th>Platform</th>
                <th>Location</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(job.id)}
                      onChange={() => toggleSelect(job.id)}
                    />
                  </td>
                  <td>{job.title}</td>
                  <td>{job.company}</td>
                  <td>{job.platform}</td>
                  <td>{job.location}</td>
                  <td>{job.match_score?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            onClick={handleApply}
            disabled={selected.size === 0}
            style={{ marginTop: 16, padding: "8px 24px" }}
          >
            Apply Selected ({selected.size})
          </button>
        </>
      )}
    </div>
  );
}
