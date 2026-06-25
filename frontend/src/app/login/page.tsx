"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { Shield, Zap } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ email: "", password: "", full_name: "", organization_name: "" });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = isLogin
        ? await auth.login(form.email, form.password)
        : await auth.register({ email: form.email, password: form.password, full_name: form.full_name, organization_name: form.organization_name });
      if (res && res.access_token) {
        localStorage.setItem("token", res.access_token);
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-900 to-primary-700">
      <div className="w-full max-w-md p-8 bg-white rounded-2xl shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Shield className="w-8 h-8 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Data Janitor</h1>
            <p className="text-sm text-gray-500">Clean CRM data automatically</p>
          </div>
        </div>

        {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" required className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input type="password" required minLength={8} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          {!isLogin && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input type="text" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Organization Name</label>
                <input type="text" required className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" value={form.organization_name} onChange={(e) => setForm({ ...form, organization_name: e.target.value })} />
              </div>
            </>
          )}
          <button type="submit" disabled={loading} className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition flex items-center justify-center gap-2">
            {loading ? "..." : <Zap className="w-4 h-4" />}
            {isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          {isLogin ? "New here?" : "Already have an account?"}{" "}
          <button className="text-primary-600 font-medium hover:underline" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? "Create account" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}
