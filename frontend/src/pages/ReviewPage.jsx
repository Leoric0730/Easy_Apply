import { useState, useEffect } from "react";
import api from "../api/client";

export default function ReviewPage() {
  const [applications, setApplications] = useState([]);

  useEffect(() => {
    api
      .get("/applications/?status=ready_to_review")
      .then((res) => setApplications(res.data.applications));
  }, []);

  return (
    <div>
      <h2>Ready to Review</h2>
      {applications.length === 0 ? (
        <p>No applications waiting for review.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Company</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {applications.map((app) => (
              <tr key={app.id}>
                <td>{app.job_title}</td>
                <td>{app.company}</td>
                <td>{app.status}</td>
                <td>
                  <a
                    href={app.browser_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open Browser
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
