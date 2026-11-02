"use client";

import React from "react";
import {
  LayoutDashboard,
  Package,
  Sliders,
  ShoppingBag,
  Users,
  CreditCard,
  Settings,
  ShieldCheck,
  Zap
} from "lucide-react";

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems = [
    { id: "dashboard", label: "Tổng quan", icon: LayoutDashboard },
    { id: "products", label: "Quản lý sản phẩm", icon: Package },
    { id: "pricing", label: "Quy tắc kê giá", icon: Sliders },
    { id: "orders", label: "Quản lý đơn hàng", icon: ShoppingBag },
    { id: "users", label: "Khách hàng", icon: Users },
    { id: "payments", label: "Nạp tiền & Thanh toán", icon: CreditCard },
    { id: "settings", label: "Cấu hình hệ thống", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-shark-navy border-r border-shark-border flex flex-col justify-between h-screen fixed left-0 top-0 z-30 select-none">
      <div>
        {/* Brand Header */}
        <div className="h-20 flex items-center px-6 gap-3 border-b border-shark-border/60 bg-gradient-to-r from-shark-navy to-shark-card">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-shark-blue to-shark-cyan flex items-center justify-center shadow-glow-cyan text-shark-dark font-extrabold text-xl">
            🦈
          </div>
          <div>
            <h1 className="font-black text-xl tracking-wider text-white flex items-center gap-1.5">
              SHARK<span className="text-shark-cyan glow-cyan-text">MMO</span>
            </h1>
            <p className="text-[11px] font-medium text-shark-muted">Admin Control Hub</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-shark-blue/20 to-shark-cyan/10 text-shark-cyan border border-shark-cyan/30 shadow-glow-cyan"
                    : "text-shark-muted hover:text-white hover:bg-shark-card/60"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "text-shark-cyan" : "text-shark-muted"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-shark-border/60 bg-shark-dark/40">
        <div className="bg-shark-card/50 rounded-xl p-3 border border-shark-border flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <div className="text-xs">
            <p className="text-white font-semibold">Hệ thống: Hoạt động</p>
            <p className="text-shark-muted text-[11px]">Canboso API v2.2 Connected</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
