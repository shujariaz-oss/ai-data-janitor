"use client";

import { useEffect, useState } from "react";
import { audit } from "@/lib/api";
import { FileText, RotateCcw, ChevronLeft, ChevronRight } from "lucide-react";

export default function AuditPage() {
  const [changes, setChanges] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [loading, setLoading] = useState(true);
  const [rollingBack, setRollingBack] = useState<string | null>(null);

  useEffect(() => {
    loadChanges();
  }, [page]);

  const loadChanges = () => {
    setLoading(true);
    audit.changes(page).then((res) => {
      setChanges(res?.items || []);
      setTotal(res?.total || 0);
      setLoading(false);
    });
  };

  const rollback = async (changeId: string) => {
    if (!confirm("Are you sure you want to rollback this change?")) return;
    setRollingBack(changeId);
    try {
      await audit.rollback(changeId);
      loadChanges();
    } finally {
      setRollingBack(null);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
        <p className="text-gray-500 mt-1">Review every change made by the AI Data Janitor</p>
      </div>

      <div className="bg-white rounded-xl border p-6">
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : changes.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No changes recorded yet.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="text-left py-3 px-4 font-medium">Action</th>
                    <th className="text-left py-3 px-4 font-medium">Field</th>
                    <th className="text-left py-3 px-4 font-medium">Old Value</th>
                    <th className="text-left py-3 px-4 font-medium">New Value</th>
                    <th className="text-left py-3 px-4 font-medium">Confidence</th>
                    <th className="text-left py-3 px-4 font-medium">Date</th>
                    <th className="text-left py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {changes.map((change) => (
                    <tr key={change.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${actionStyle(change.action)}`}>
                          {change.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-gray-900">{change.field_name}</td>
                      <td className="py-3 px-4 text-gray-500 max-w-xs truncate">{change.old_value || "—"}</td>
                      <td className="py-3 px-4 text-gray-900 max-w-xs truncate">{change.new_value || "—"}</td>
                      <td className="py-3 px-4">{change.confidence ? `${(change.confidence * 100).toFixed(1)}%` : "—"}</td>
                      <td className="py-3 px-4 text-gray-500">{new Date(change.created_at).toLocaleString()}</td>
                      <td className="py-3 px-4">
                        {!change.rolled_back ? (
                          <button
                            onClick={() => rollback(change.id)}
                            disabled={rollingBack === change.id}
                            className="inline-flex items-center gap-1.5 text-sm text-red-600 hover:text-red-700 font-medium transition"
                          >
                            <RotateCcw className="w-4 h-4" />
                            {rollingBack === change.id ? "Rolling back..." : "Rollback"}
                          </button>
                        ) : (
                          <span className="text-xs text-gray-400">Rolled back</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-gray-500">
                Showing {changes.length} of {total} changes
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm font-medium text-gray-700">
                  Page {page} of {totalPages || 1}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function actionStyle(action: string) {
  switch (action) {
    case "normalize": return "bg-blue-100 text-blue-700";
    case "enrich": return "bg-purple-100 text-purple-700";
    case "dedup": return "bg-yellow-100 text-yellow-700";
    case "merge": return "bg-orange-100 text-orange-700";
    default: return "bg-gray-100 text-gray-700";
  }
}
