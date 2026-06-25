"use client";

import { useEffect, useState } from "react";
import { billing } from "@/lib/api";
import { CreditCard, DollarSign, Gift, Zap } from "lucide-react";

export default function BillingPage() {
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    billing.usage()
      .then((u) => setUsage(u))
      .finally(() => setLoading(false));
  }, []);

  const openPortal = async () => {
    try {
      const res = await billing.portal();
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (e) {
      alert("Failed to open billing portal. Make sure you have an active subscription.");
    }
  };

  if (loading) return <p className="text-gray-500">Loading billing data...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Billing & Usage</h1>
        <p className="text-gray-500 mt-1">Track your cleaning usage and manage billing</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border p-6 flex items-center gap-4">
          <div className="p-3 bg-blue-50 rounded-lg text-blue-600">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{usage?.current_month_records || 0}</p>
            <p className="text-sm text-gray-500">Records Cleaned This Month</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border p-6 flex items-center gap-4">
          <div className="p-3 bg-green-50 rounded-lg text-green-600">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">${((usage?.current_month_cost_cents || 0) / 100).toFixed(2)}</p>
            <p className="text-sm text-gray-500">Current Month Cost</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border p-6 flex items-center gap-4">
          <div className="p-3 bg-purple-50 rounded-lg text-purple-600">
            <Gift className="w-6 h-6" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{usage?.free_remaining || 0}</p>
            <p className="text-sm text-gray-500">Free Records Remaining</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Pricing</h2>
        <p className="text-gray-600 mb-6">
          You pay only for what you use. No monthly fees, no hidden costs.
        </p>
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold text-primary-600">${((usage?.unit_price_cents || 2) / 100).toFixed(2)}</span>
          <span className="text-gray-500">per record cleaned</span>
        </div>
        <div className="mt-6 flex gap-3">
          <button
            onClick={openPortal}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition"
          >
            <CreditCard className="w-4 h-4" />
            Manage Billing
          </button>
        </div>
      </div>
    </div>
  );
}
