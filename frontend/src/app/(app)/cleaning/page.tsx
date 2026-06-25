"use client";

import { useEffect, useState } from "react";
import { cleaning, crm } from "@/lib/api";
import { Play, Settings, CheckCircle, XCircle, Clock } from "lucide-react";

export default function CleaningPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [connections, setConnections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    Promise.all([cleaning.jobs(), crm.connections()])
      .then(([j, c]) => {
        setJobs(j || []);
        setConnections(c || []);
      })
      .finally(() => setLoading(false));
  };

  const triggerJob = async (connectionId: string) => {
    setTriggering(true);
    try {
      await crm.trigger(connectionId);
      setTimeout(loadData, 2000);
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cleaning Jobs</h1>
          <p className="text-gray-500 mt-1">Monitor and manage data cleaning operations</p>
        </div>
      </div>

      {connections.length > 0 && (
        <div className="bg-white rounded-xl border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Trigger Cleaning</h2>
          <div className="flex gap-3">
            {connections.map((conn) => (
              <button
                key={conn.id}
                onClick={() => triggerJob(conn.id)}
                disabled={triggering}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition"
              >
                <Play className="w-4 h-4" />
                Run {conn.crm_type}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">All Jobs</h2>
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : jobs.length === 0 ? (
          <p className="text-gray-500">No jobs found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-gray-500">
                  <th className="text-left py-3 px-4 font-medium">Status</th>
                  <th className="text-left py-3 px-4 font-medium">Records</th>
                  <th className="text-left py-3 px-4 font-medium">Processed</th>
                  <th className="text-left py-3 px-4 font-medium">Cost</th>
                  <th className="text-left py-3 px-4 font-medium">Trigger</th>
                  <th className="text-left py-3 px-4 font-medium">Started</th>
                  <th className="text-left py-3 px-4 font-medium">Completed</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusStyle(job.status)}`}>
                        {statusIcon(job.status)}
                        {job.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">{job.record_count}</td>
                    <td className="py-3 px-4">{job.processed_count}</td>
                    <td className="py-3 px-4">${(job.cost_cents / 100).toFixed(2)}</td>
                    <td className="py-3 px-4 capitalize">{job.trigger_type}</td>
                    <td className="py-3 px-4 text-gray-500">{job.started_at ? new Date(job.started_at).toLocaleString() : "—"}</td>
                    <td className="py-3 px-4 text-gray-500">{job.completed_at ? new Date(job.completed_at).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function statusStyle(status: string) {
  switch (status) {
    case "completed": return "bg-green-100 text-green-700";
    case "running": return "bg-blue-100 text-blue-700";
    case "failed": return "bg-red-100 text-red-700";
    case "pending": return "bg-yellow-100 text-yellow-700";
    default: return "bg-gray-100 text-gray-700";
  }
}

function statusIcon(status: string) {
  const className = "w-3.5 h-3.5";
  switch (status) {
    case "completed": return <CheckCircle className={className} />;
    case "failed": return <XCircle className={className} />;
    case "running": return <Clock className={className} />;
    default: return null;
  }
}
