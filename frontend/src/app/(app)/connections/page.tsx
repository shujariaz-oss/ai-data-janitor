"use client";

import { useEffect, useState } from "react";
import { crm } from "@/lib/api";
import { Link2, Plus, Check } from "lucide-react";

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);

  useEffect(() => {
    crm.connections().then((c) => {
      setConnections(c || []);
      setLoading(false);
    });
  }, []);

  const connect = async (type: string) => {
    setConnecting(type);
    try {
      const res = await crm.connect(type);
      if (res && res.auth_url) {
        window.location.href = res.auth_url;
      }
    } finally {
      setConnecting(null);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">CRM Connections</h1>
        <p className="text-gray-500 mt-1">Connect your Salesforce or HubSpot account</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CRMConnectCard
          type="salesforce"
          name="Salesforce"
          description="Connect to Salesforce CRM for Contact, Lead, and Account cleaning."
          connected={connections.some((c) => c.crm_type === "salesforce")}
          onConnect={() => connect("salesforce")}
          loading={connecting === "salesforce"}
        />
        <CRMConnectCard
          type="hubspot"
          name="HubSpot"
          description="Connect to HubSpot CRM for Contact and Company cleaning."
          connected={connections.some((c) => c.crm_type === "hubspot")}
          onConnect={() => connect("hubspot")}
          loading={connecting === "hubspot"}
        />
      </div>

      {connections.length > 0 && (
        <div className="bg-white rounded-xl border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Connections</h2>
          <div className="space-y-3">
            {connections.map((conn) => (
              <div key={conn.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Link2 className="w-5 h-5 text-primary-600" />
                  <div>
                    <p className="font-medium text-gray-900 capitalize">{conn.crm_type}</p>
                    <p className="text-sm text-gray-500">Status: {conn.status}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-500" />
                  <span className="text-sm text-green-600 font-medium">Connected</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function CRMConnectCard({ name, description, connected, onConnect, loading }: any) {
  return (
    <div className="bg-white rounded-xl border p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{name}</h3>
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        </div>
        {connected && (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
            <Check className="w-3.5 h-3.5" /> Connected
          </span>
        )}
      </div>
      <button
        onClick={onConnect}
        disabled={connected || loading}
        className={`w-full py-2.5 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
          connected
            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
            : "bg-primary-600 hover:bg-primary-700 text-white"
        }`}
      >
        {loading ? "Connecting..." : connected ? "Connected" : <><Plus className="w-4 h-4" /> Connect {name}</>}
      </button>
    </div>
  );
}
