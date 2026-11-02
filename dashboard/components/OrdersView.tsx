"use client";

import React, { useState, useEffect } from "react";
import {
  ShoppingBag,
  Search,
  Eye,
  RotateCcw,
  CheckCircle,
  XCircle,
  Clock,
  Key,
  Copy,
  Check,
  X
} from "lucide-react";
import { api } from "@/lib/api";
import { formatVnd } from "@/lib/utils";

interface OrdersViewProps {
  onRefreshStats: () => void;
}

export const OrdersView: React.FC<OrdersViewProps> = ({ onRefreshStats }) => {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [viewingOrder, setViewingOrder] = useState<any | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const res = await api.getOrders({
        status: statusFilter === "ALL" ? undefined : statusFilter,
        search: search || undefined
      });
      setOrders(res.orders || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadOrders();
  };

  const handleRefund = async (orderId: number, code: string) => {
    if (!confirm(`Bạn có chắc muốn hoàn tiền cho đơn ${code}? Số tiền bán sẽ được cộng lại vào ví người dùng.`)) return;
    try {
      await api.refundOrder(orderId);
      await loadOrders();
      onRefreshStats();
      alert(`Đã hoàn tiền đơn hàng ${code} thành công.`);
    } catch (e: any) {
      alert(`Lỗi hoàn tiền: ${e.message}`);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const statuses = [
    { id: "ALL", label: "Tất cả đơn" },
    { id: "completed", label: "Thành công" },
    { id: "processing", label: "Đang xử lý" },
    { id: "failed", label: "Thất bại" },
    { id: "refunded", label: "Đã hoàn tiền" }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShoppingBag className="w-6 h-6 text-shark-cyan" />
            Quản lý Đơn hàng & Thông tin bàn giao
          </h2>
          <p className="text-xs text-shark-muted">
            Theo dõi đơn hàng tự động, tài khoản đã cấp cho khách và đối soát với mã nguồn Canboso.
          </p>
        </div>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-shark-card/40 p-4 rounded-2xl border border-shark-border">
        <form onSubmit={handleSearch} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-shark-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Tìm theo mã đơn (SHARK-...) hoặc tên SP..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-shark-navy/80 border border-shark-border rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-shark-muted focus:outline-none focus:border-shark-cyan transition-all"
          />
        </form>

        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
          {statuses.map((s) => (
            <button
              key={s.id}
              onClick={() => setStatusFilter(s.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                statusFilter === s.id
                  ? "bg-shark-blue text-white shadow-glow-blue"
                  : "bg-shark-navy/60 text-shark-muted hover:text-white border border-shark-border"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Orders Table */}
      <div className="rounded-2xl border border-shark-border bg-shark-card/40 overflow-hidden backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-shark-border bg-shark-navy/80 text-[11px] font-bold text-shark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Mã đơn hàng</th>
                <th className="py-3.5 px-4">Khách hàng</th>
                <th className="py-3.5 px-4">Sản phẩm & SL</th>
                <th className="py-3.5 px-4">Giá bán</th>
                <th className="py-3.5 px-4">Giá vốn nguồn</th>
                <th className="py-3.5 px-4">Lợi nhuận</th>
                <th className="py-3.5 px-4">Trạng thái</th>
                <th className="py-3.5 px-4">Thời gian</th>
                <th className="py-3.5 px-4 text-right">Chi tiết</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-shark-border/60 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    Đang tải đơn hàng...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    Không có đơn hàng nào phù hợp với bộ lọc.
                  </td>
                </tr>
              ) : (
                orders.map((o) => {
                  let statusBadge = (
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
                      <CheckCircle className="w-3 h-3" /> Thành công
                    </span>
                  );
                  if (o.status === "failed") {
                    statusBadge = (
                      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 w-fit">
                        <XCircle className="w-3 h-3" /> Thất bại
                      </span>
                    );
                  } else if (o.status === "processing") {
                    statusBadge = (
                      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit">
                        <Clock className="w-3 h-3" /> Đang xử lý
                      </span>
                    );
                  } else if (o.status === "refunded") {
                    statusBadge = (
                      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center gap-1 w-fit">
                        <RotateCcw className="w-3 h-3" /> Đã hoàn tiền
                      </span>
                    );
                  }

                  return (
                    <tr key={o.id} className="hover:bg-shark-card/60 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-white text-xs">
                        {o.order_code}
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="text-xs px-2 py-0.5 rounded bg-shark-navy border border-shark-border text-shark-cyan font-mono">
                          {o.telegram_id}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white max-w-xs truncate">{o.product_name}</div>
                        <div className="text-[11px] text-shark-muted">Số lượng: <b>x{o.quantity}</b></div>
                      </td>

                      <td className="py-3.5 px-4 font-mono font-bold text-white">
                        {formatVnd(o.sell_price)}
                      </td>

                      <td className="py-3.5 px-4 font-mono text-shark-muted text-xs">
                        {formatVnd(o.source_price * o.quantity)}
                      </td>

                      <td className="py-3.5 px-4 font-mono font-bold text-emerald-400 text-xs">
                        +{formatVnd(o.profit)}
                      </td>

                      <td className="py-3.5 px-4">{statusBadge}</td>

                      <td className="py-3.5 px-4 text-xs text-shark-muted whitespace-nowrap">
                        {o.created_at ? new Date(o.created_at).toLocaleString("vi-VN") : "N/A"}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => setViewingOrder(o)}
                          className="px-3 py-1.5 rounded-xl bg-shark-navy hover:bg-shark-cardHover border border-shark-border hover:border-shark-cyan text-xs font-semibold text-white flex items-center gap-1.5 ml-auto transition-all"
                        >
                          <Eye className="w-3.5 h-3.5 text-shark-cyan" />
                          <span>Chi tiết</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Order Detail Modal */}
      {viewingOrder && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-shark-navy border border-shark-border rounded-2xl w-full max-w-xl p-6 space-y-5 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-shark-border">
              <div>
                <h3 className="font-bold text-white text-base">Chi tiết đơn hàng {viewingOrder.order_code}</h3>
                <p className="text-xs text-shark-muted">
                  Canboso Order Code: <span className="font-mono text-shark-cyan">{viewingOrder.canboso_order_code || "N/A"}</span>
                </p>
              </div>
              <button
                onClick={() => setViewingOrder(null)}
                className="text-shark-muted hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Product Info */}
              <div className="p-3 bg-shark-card rounded-xl border border-shark-border text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-shark-muted">Sản phẩm:</span>
                  <span className="text-white font-bold">{viewingOrder.product_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-shark-muted">Số lượng:</span>
                  <span className="text-white font-bold">{viewingOrder.quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-shark-muted">Khách hàng Telegram ID:</span>
                  <span className="font-mono text-shark-cyan font-bold">{viewingOrder.telegram_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-shark-muted">Tổng tiền bán:</span>
                  <span className="font-mono text-emerald-400 font-bold">{formatVnd(viewingOrder.sell_price)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-shark-muted">Lợi nhuận đơn này:</span>
                  <span className="font-mono text-shark-cyan font-bold">{formatVnd(viewingOrder.profit)}</span>
                </div>
              </div>

              {/* Delivery accounts */}
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Key className="w-4 h-4 text-shark-cyan" />
                  Dữ liệu bàn giao (Tài khoản / Thông tin):
                </h4>
                {viewingOrder.delivery_data && viewingOrder.delivery_data.length > 0 ? (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {viewingOrder.delivery_data.map((acc: any, i: number) => (
                      <div key={i} className="p-3 bg-shark-dark rounded-xl border border-shark-border/80 font-mono text-xs space-y-1">
                        <div className="text-[11px] text-shark-muted font-bold mb-1">Tài khoản #{i + 1}</div>
                        {acc.user && (
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">User: <b className="text-white">{acc.user}</b></span>
                            <button
                              onClick={() => copyToClipboard(acc.user, `u_${i}`)}
                              className="text-shark-muted hover:text-shark-cyan p-0.5"
                            >
                              {copiedKey === `u_${i}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            </button>
                          </div>
                        )}
                        {acc.password && (
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Pass: <b className="text-amber-300">{acc.password}</b></span>
                            <button
                              onClick={() => copyToClipboard(acc.password, `p_${i}`)}
                              className="text-shark-muted hover:text-shark-cyan p-0.5"
                            >
                              {copiedKey === `p_${i}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            </button>
                          </div>
                        )}
                        {acc.verifyEmail && <div className="text-slate-400">Mail xác nhận: {acc.verifyEmail}</div>}
                        {acc.expiryText && <div className="text-slate-400">Hạn dùng: {acc.expiryText}</div>}
                        {acc.otherInfo && <div className="text-slate-400">Ghi chú: {acc.otherInfo}</div>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-shark-dark/50 rounded-xl text-center text-xs text-shark-muted">
                    {viewingOrder.error_message ? (
                      <span className="text-rose-400">Lỗi giao hàng: {viewingOrder.error_message}</span>
                    ) : (
                      "Không có dữ liệu bàn giao dạng tài khoản (Gói nâng cấp/slot trực tiếp)."
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-shark-border">
              {viewingOrder.status === "completed" && (
                <button
                  onClick={() => handleRefund(viewingOrder.id, viewingOrder.order_code)}
                  className="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 text-xs font-semibold transition-all flex items-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Hoàn tiền vào ví khách</span>
                </button>
              )}
              <button
                onClick={() => setViewingOrder(null)}
                className="px-5 py-2 rounded-xl bg-shark-card hover:bg-shark-cardHover text-white text-xs font-semibold ml-auto"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
