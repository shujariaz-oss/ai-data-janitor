"use client";

import { useEffect, useState } from "react";
import { cleaning, billing, crm } from "@/lib/api";
import { Activity, CheckCircle, CreditCard, Database, AlertCircle } from "lucide-react";

export default function DashboardPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [connections, setConnections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([cleaning.jobs(), billing.usage(), crm.connections()])
      .then(([j, u, c]) => {
        setJobs(j || []);
        setUsage(u);
        setConnections(c || []);
      })
      .finally(() => setLoading(false));
  }, []);

  const latestJobs = jobs.slice(0, 5);
  const completedJobs = jobs.filter((j) => j.status === "completed").length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of your data cleaning activity</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard icon={Database} label="CRM Connections" value={connections.length} color="bg-blue-50 text-blue-600" />
        <StatCard icon={CheckCircle} label="Completed Jobs" value={completedJobs} color="bg-green-50 text-green-600" />
        <StatCard icon={Activity} label="Records Cleaned" value={usage?.current_month_records || 0} color="bg-purple-50 text-purple-600" />
        <StatCard icon={CreditCard} label="This Month Cost" value={`$${((usage?.current_month_cost_cents || 0) / 100).toFixed(2)}`} color="bg-orange-50 text-orange-600" />
      </div>

      <div className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Cleaning Jobs</h2>
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : latestJobs.length === 0 ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No cleaning jobs yet. Connect a CRM to get started.</p>
          </div>
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
                  <th className="text-left py-3 px-4 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {latestJobs.map((job) => (
                  <tr key={job.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusStyle(job.status)}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">{job.record_count}</td>
                    <td className="py-3 px-4">{job.processed_count}</td>
                    <td className="py-3 px-4">${(job.cost_cents / 100).toFixed(2)}</td>
                    <td className="py-3 px-4 capitalize">{job.trigger_type}</td>
                    <td className="py-3 px-4 text-gray-500">{new Date(job.created_at).toLocaleDateString()}</td>
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

function StatCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="bg-white rounded-xl border p-6 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}

function statusStyle(status: string) {
  switch (status) {
    case "completed": return "bg-green-100 text-green-700";
    case "running": return "bg-blue-100 text-blue-700";
    case "failed": return "bg-red-100 text-red-700";
    default: return "bg-gray-100 text-gray-700";
  }
}
