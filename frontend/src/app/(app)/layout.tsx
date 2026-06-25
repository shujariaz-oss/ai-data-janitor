"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Shield, Link2, Settings, FileText, CreditCard, LogOut, Home } from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/connections", label: "Connections", icon: Link2 },
  { href: "/cleaning", label: "Cleaning Jobs", icon: Settings },
  { href: "/audit", label: "Audit Log", icon: FileText },
  { href: "/billing", label: "Billing", icon: CreditCard },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white border-r flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <Shield className="w-8 h-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900">Data Janitor</span>
        </div>
        <nav className="flex-1 px-4 space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                  active
                    ? "bg-primary-50 text-primary-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-4 py-2.5 w-full text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-lg transition"
          >
            <LogOut className="w-5 h-5" />
            Sign Out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
