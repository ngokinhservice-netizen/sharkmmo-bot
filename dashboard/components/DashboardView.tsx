"use client";

import React from "react";
import {
  Users,
  ShoppingBag,
  TrendingUp,
  DollarSign,
  Wallet,
  CheckCircle,
  XCircle,
  AlertCircle,
  ArrowUpRight,
  RefreshCw
} from "lucide-react";
import { formatVnd } from "@/lib/utils";

interface DashboardViewProps {
  stats: any;
  onNavigate: (tab: string) => void;
  onSync: () => void;
  isSyncing: boolean;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  stats,
  onNavigate,
  onSync,
  isSyncing
}) => {
  const overview = stats?.overview || {};
  const chartData = stats?.chart_data || [];

  const cards = [
    {
      title: "Tổng khách hàng",
      value: overview.total_users || 0,
      sub: "Tài khoản Telegram đã kích hoạt",
      icon: Users,
      color: "from-blue-500/20 to-shark-blue/10",
      textColor: "text-shark-blue",
      borderColor: "border-shark-blue/30"
    },
    {
      title: "Doanh thu thực tế",
      value: formatVnd(overview.total_revenue || 0),
      sub: "Đơn hàng đã hoàn thành",
      icon: DollarSign,
      color: "from-emerald-500/20 to-teal-500/10",
      textColor: "text-emerald-400",
      borderColor: "border-emerald-500/30"
    },
    {
      title: "Lợi nhuận gộp",
      value: formatVnd(overview.total_profit || 0),
      sub: "Giá bán - Giá vốn nguồn",
      icon: TrendingUp,
      color: "from-cyan-500/20 to-shark-cyan/10",
      textColor: "text-shark-cyan",
      borderColor: "border-shark-cyan/30"
    },
    {
      title: "Đơn hàng thành công",
      value: `${overview.completed_orders || 0} / ${overview.total_orders || 0}`,
      sub: `Tỷ lệ thành công: ${
        overview.total_orders ? Math.round((overview.completed_orders / overview.total_orders) * 100) : 100
      }%`,
      icon: ShoppingBag,
      color: "from-indigo-500/20 to-purple-500/10",
      textColor: "text-indigo-400",
      borderColor: "border-indigo-500/30"
    },
    {
      title: "Số dư ví khách hàng",
      value: formatVnd(overview.total_customer_balance || 0),
      sub: "Tổng tiền khách đã nạp vào ví bot",
      icon: Wallet,
      color: "from-amber-500/20 to-orange-500/10",
      textColor: "text-amber-400",
      borderColor: "border-amber-500/30"
    },
    {
      title: "Số dư kho Canboso",
      value: overview.source_balance?.formatted || "0 VND",
      sub: overview.source_balance?.is_low ? "⚠️ Cần nạp thêm tiền vào kho Canboso!" : "🟢 Trạng thái kho: Ổn định",
      icon: Wallet,
      color: overview.source_balance?.is_low ? "from-rose-500/20 to-red-500/10" : "from-emerald-500/20 to-teal-500/10",
      textColor: overview.source_balance?.is_low ? "text-rose-400" : "text-emerald-400",
      borderColor: overview.source_balance?.is_low ? "border-rose-500/30" : "border-emerald-500/30"
    }
  ];

  // Calculate maximum revenue in chart for proportional bar rendering
  const maxBarValue = Math.max(...chartData.map((d: any) => Math.max(d.revenue, d.profit, 100000)), 100000);

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative rounded-2xl bg-gradient-to-r from-shark-navy via-shark-card to-shark-bg border border-shark-border p-6 shadow-glow-cyan overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-shark-cyan">
              Hệ sinh thái tự động hoá
            </span>
            <h2 className="text-2xl font-black text-white mt-1">
              Bảng điều khiển SHARK<span className="text-shark-cyan">MMO</span>
            </h2>
            <p className="text-sm text-shark-muted mt-1">
              Quản lý đồng bộ kho sản phẩm Canboso API, cơ chế kê giá tự động & thanh toán thông minh.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onSync}
              disabled={isSyncing}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-shark-blue to-shark-cyan text-shark-dark font-bold text-sm shadow-glow-cyan flex items-center gap-2 hover:opacity-90 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
              <span>Đồng bộ kho Canboso</span>
            </button>
            <button
              onClick={() => onNavigate("pricing")}
              className="px-5 py-2.5 rounded-xl bg-shark-card hover:bg-shark-cardHover border border-shark-border text-white font-semibold text-sm transition-all"
            >
              Cấu hình kê giá
            </button>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div
              key={i}
              className={`p-5 rounded-2xl bg-shark-card/60 backdrop-blur-sm border ${c.borderColor} hover:border-shark-cyan/40 transition-all duration-200 relative group`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-semibold text-shark-muted">{c.title}</p>
                  <h3 className="text-2xl font-black text-white mt-1.5">{c.value}</h3>
                  <p className="text-xs text-shark-muted mt-1">{c.sub}</p>
                </div>
                <div className={`p-3 rounded-xl bg-gradient-to-br ${c.color} border border-white/5`}>
                  <Icon className={`w-6 h-6 ${c.textColor}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Chart Section & Quick Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue & Profit Chart */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-shark-card/50 border border-shark-border">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-bold text-white text-base">Thống kê Doanh thu & Lợi nhuận (7 ngày gần nhất)</h3>
              <p className="text-xs text-shark-muted">Số liệu tính trên đơn hàng thành công thực tế</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-semibold">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-shark-blue" />
                <span className="text-shark-muted">Doanh thu</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-shark-cyan" />
                <span className="text-shark-muted">Lợi nhuận</span>
              </div>
            </div>
          </div>

          {/* Bar Chart Visualization */}
          <div className="h-64 flex items-end justify-between gap-3 pt-6 border-b border-shark-border/60">
            {chartData.map((d: any, idx: number) => {
              const revHeight = Math.max(12, Math.round((d.revenue / maxBarValue) * 200));
              const profitHeight = Math.max(8, Math.round((d.profit / maxBarValue) * 200));

              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2 group">
                  <div className="w-full flex items-end justify-center gap-1.5 h-52">
                    {/* Revenue Bar */}
                    <div
                      style={{ height: `${revHeight}px` }}
                      className="w-1/2 max-w-[20px] bg-gradient-to-t from-shark-blue/50 to-shark-blue rounded-t-md transition-all group-hover:brightness-125 relative"
                    >
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-shark-dark text-[10px] text-white px-2 py-0.5 rounded border border-shark-border whitespace-nowrap pointer-events-none transition-opacity">
                        {formatVnd(d.revenue)}
                      </div>
                    </div>
                    {/* Profit Bar */}
                    <div
                      style={{ height: `${profitHeight}px` }}
                      className="w-1/2 max-w-[20px] bg-gradient-to-t from-shark-cyan/50 to-shark-cyan rounded-t-md transition-all group-hover:brightness-125 relative"
                    >
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-shark-dark text-[10px] text-shark-cyan px-2 py-0.5 rounded border border-shark-border whitespace-nowrap pointer-events-none transition-opacity">
                        {formatVnd(d.profit)}
                      </div>
                    </div>
                  </div>
                  <span className="text-[11px] font-medium text-shark-muted">{d.date}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Quick Actions & System Health */}
        <div className="p-6 rounded-2xl bg-shark-card/50 border border-shark-border space-y-5">
          <h3 className="font-bold text-white text-base">Thao tác nhanh</h3>

          <div className="space-y-3">
            <button
              onClick={() => onNavigate("products")}
              className="w-full flex items-center justify-between p-3.5 rounded-xl bg-shark-navy/70 border border-shark-border hover:border-shark-cyan/50 transition-all text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-shark-cyan transition-colors">
                  Quản lý giá sản phẩm
                </p>
                <p className="text-xs text-shark-muted">Chỉnh sửa giá vốn & giá bán lẻ</p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-shark-muted group-hover:text-shark-cyan" />
            </button>

            <button
              onClick={() => onNavigate("pricing")}
              className="w-full flex items-center justify-between p-3.5 rounded-xl bg-shark-navy/70 border border-shark-border hover:border-shark-cyan/50 transition-all text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-shark-cyan transition-colors">
                  Cấu hình % Kê giá toàn shop
                </p>
                <p className="text-xs text-shark-muted">Tự động cộng lãi vào giá Canboso</p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-shark-muted group-hover:text-shark-cyan" />
            </button>

            <button
              onClick={() => onNavigate("payments")}
              className="w-full flex items-center justify-between p-3.5 rounded-xl bg-shark-navy/70 border border-shark-border hover:border-shark-cyan/50 transition-all text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-shark-cyan transition-colors">
                  Duyệt nạp tiền thủ công
                </p>
                <p className="text-xs text-shark-muted">
                  Đang có <b className="text-amber-400">{overview.pending_deposits || 0}</b> yêu cầu chờ duyệt
                </p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-shark-muted group-hover:text-shark-cyan" />
            </button>

            <button
              onClick={() => onNavigate("settings")}
              className="w-full flex items-center justify-between p-3.5 rounded-xl bg-shark-navy/70 border border-shark-border hover:border-shark-cyan/50 transition-all text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-shark-cyan transition-colors">
                  Cấu hình VietQR & Ngân hàng
                </p>
                <p className="text-xs text-shark-muted">Số tài khoản, ngân hàng nhận tiền</p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-shark-muted group-hover:text-shark-cyan" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
