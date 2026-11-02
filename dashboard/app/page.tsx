"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { DashboardView } from "@/components/DashboardView";
import { ProductsView } from "@/components/ProductsView";
import { PricingRulesView } from "@/components/PricingRulesView";
import { OrdersView } from "@/components/OrdersView";
import { UsersView } from "@/components/UsersView";
import { PaymentsView } from "@/components/PaymentsView";
import { SettingsView } from "@/components/SettingsView";
import { api } from "@/lib/api";

export default function Home() {
  const [currentTab, setCurrentTab] = useState("dashboard");
  const [stats, setStats] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const loadStats = async () => {
    try {
      setIsRefreshing(true);
      const res = await api.getStats();
      setStats(res);
    } catch (e) {
      console.error("Failed to load dashboard stats:", e);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadStats();
    // Auto refresh every 30s
    const timer = setInterval(loadStats, 30000);
    return () => clearInterval(timer);
  }, []);

  const handleManualSync = async () => {
    try {
      setIsSyncing(true);
      await api.syncProducts();
      await loadStats();
      alert("Đồng bộ kho sản phẩm từ Canboso thành công!");
    } catch (e: any) {
      alert(`Đồng bộ thất bại: ${e.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-shark-bg text-shark-text">
      {/* Fixed Sidebar */}
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

      {/* Main Content Area */}
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        <Navbar
          sourceBalance={stats?.overview?.source_balance}
          onRefresh={loadStats}
          isRefreshing={isRefreshing}
        />

        <main className="p-8 max-w-7xl mx-auto w-full">
          {currentTab === "dashboard" && (
            <DashboardView
              stats={stats}
              onNavigate={setCurrentTab}
              onSync={handleManualSync}
              isSyncing={isSyncing}
            />
          )}

          {currentTab === "products" && (
            <ProductsView onRefreshStats={loadStats} />
          )}

          {currentTab === "pricing" && (
            <PricingRulesView onRefreshStats={loadStats} />
          )}

          {currentTab === "orders" && (
            <OrdersView onRefreshStats={loadStats} />
          )}

          {currentTab === "users" && (
            <UsersView onRefreshStats={loadStats} />
          )}

          {currentTab === "payments" && (
            <PaymentsView onRefreshStats={loadStats} />
          )}

          {currentTab === "settings" && (
            <SettingsView />
          )}
        </main>
      </div>
    </div>
  );
}
