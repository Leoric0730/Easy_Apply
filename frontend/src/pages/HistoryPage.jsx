import { useState, useEffect } from "react";
import api from "../api/client";

export default function HistoryPage() {
  const [applications, setApplications] = useState([]);

  useEffect(() => {
    api
      .get("/applications/?status=submitted")
      .then((res) => setApplications(res.data.applications));
  }, []);

  return (
    <div>
      <h2>Application History</h2>
      {applications.length === 0 ? (
        <p>No submitted applications yet.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Company</th>
              <th>Platform</th>
              <th>Profile Used</th>
              <th>Applied At</th>
            </tr>
          </thead>
          <tbody>
            {applications.map((app) => (
              <tr key={app.id}>
                <td>{app.job_title}</td>
                <td>{app.company}</td>
                <td>{app.platform}</td>
                <td>{app.profile_label}</td>
                <td>{app.applied_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
