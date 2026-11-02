"use client";

import React, { useState, useEffect } from "react";
import {
  CreditCard,
  CheckCircle,
  XCircle,
  Clock,
  Check,
  X,
  QrCode,
  DollarSign
} from "lucide-react";
import { api } from "@/lib/api";
import { formatVnd } from "@/lib/utils";

interface PaymentsViewProps {
  onRefreshStats: () => void;
}

export const PaymentsView: React.FC<PaymentsViewProps> = ({ onRefreshStats }) => {
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const loadPayments = async () => {
    try {
      setLoading(true);
      const res = await api.getPayments({
        status: statusFilter === "ALL" ? undefined : statusFilter
      });
      setPayments(res.transactions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, [statusFilter]);

  const handleApprove = async (id: number, code: string, amount: number) => {
    if (!confirm(`Xác nhận duyệt nạp ${formatVnd(amount)} cho giao dịch ${code}? Tiền sẽ được cộng ngay vào ví khách!`)) return;
    try {
      await api.approvePayment(id);
      await loadPayments();
      onRefreshStats();
      alert(`Đã duyệt nạp tiền ${code} thành công.`);
    } catch (e: any) {
      alert(`Lỗi duyệt: ${e.message}`);
    }
  };

  const handleReject = async (id: number, code: string) => {
    if (!confirm(`Từ chối giao dịch nạp tiền ${code}?`)) return;
    try {
      await api.rejectPayment(id);
      await loadPayments();
      onRefreshStats();
      alert(`Đã từ chối giao dịch ${code}.`);
    } catch (e: any) {
      alert(`Lỗi từ chối: ${e.message}`);
    }
  };

  const statuses = [
    { id: "ALL", label: "Tất cả giao dịch" },
    { id: "pending", label: "Chờ duyệt / xử lý" },
    { id: "completed", label: "Đã hoàn thành" },
    { id: "rejected", label: "Bị từ chối" }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-shark-cyan" />
            Nạp tiền & Thanh toán Ngân hàng
          </h2>
          <p className="text-xs text-shark-muted">
            Quản lý các lệnh nạp tiền qua mã VietQR, giao dịch đối soát tự động từ SePay Webhook hoặc duyệt thủ công.
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto bg-shark-card/40 p-4 rounded-2xl border border-shark-border">
        {statuses.map((s) => (
          <button
            key={s.id}
            onClick={() => setStatusFilter(s.id)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              statusFilter === s.id
                ? "bg-shark-blue text-white shadow-glow-blue"
                : "bg-shark-navy/60 text-shark-muted hover:text-white border border-shark-border"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-shark-border bg-shark-card/40 overflow-hidden backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-shark-border bg-shark-navy/80 text-[11px] font-bold text-shark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Mã giao dịch</th>
                <th className="py-3.5 px-4">Khách hàng</th>
                <th className="py-3.5 px-4">Số tiền nạp</th>
                <th className="py-3.5 px-4">Phương thức</th>
                <th className="py-3.5 px-4">Nội dung CK</th>
                <th className="py-3.5 px-4">Trạng thái</th>
                <th className="py-3.5 px-4">Xác nhận bởi</th>
                <th className="py-3.5 px-4">Thời gian</th>
                <th className="py-3.5 px-4 text-right">Duyệt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-shark-border/60 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    Đang tải danh sách giao dịch nạp tiền...
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    Không có giao dịch nào phù hợp.
                  </td>
                </tr>
              ) : (
                payments.map((tx) => {
                  let statusBadge = (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
                      <CheckCircle className="w-3 h-3" /> Thành công
                    </span>
                  );
                  if (tx.status === "pending") {
                    statusBadge = (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit">
                        <Clock className="w-3 h-3" /> Chờ duyệt
                      </span>
                    );
                  } else if (tx.status === "rejected") {
                    statusBadge = (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 w-fit">
                        <XCircle className="w-3 h-3" /> Từ chối
                      </span>
                    );
                  }

                  return (
                    <tr key={tx.id} className="hover:bg-shark-card/60 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-white text-xs">
                        {tx.transaction_code}
                      </td>

                      <td className="py-3.5 px-4 font-mono text-shark-cyan font-bold text-xs">
                        {tx.telegram_id}
                      </td>

                      <td className="py-3.5 px-4 font-mono font-bold text-emerald-400 text-sm">
                        +{formatVnd(tx.amount)}
                      </td>

                      <td className="py-3.5 px-4 text-xs font-semibold text-slate-300 uppercase">
                        {tx.payment_method} ({tx.bank_code})
                      </td>

                      <td className="py-3.5 px-4 font-mono text-xs text-white max-w-xs truncate">
                        <code className="bg-shark-navy px-2 py-0.5 rounded border border-shark-border">
                          {tx.transfer_content}
                        </code>
                      </td>

                      <td className="py-3.5 px-4">{statusBadge}</td>

                      <td className="py-3.5 px-4 text-xs text-shark-muted">
                        {tx.confirmed_by || "—"}
                      </td>

                      <td className="py-3.5 px-4 text-xs text-shark-muted whitespace-nowrap">
                        {tx.created_at ? new Date(tx.created_at).toLocaleString("vi-VN") : "N/A"}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        {tx.status === "pending" ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleApprove(tx.id, tx.transaction_code, tx.amount)}
                              className="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 text-xs font-bold transition-all flex items-center gap-1"
                              title="Duyệt nạp tiền"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Duyệt</span>
                            </button>
                            <button
                              onClick={() => handleReject(tx.id, tx.transaction_code)}
                              className="px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30 text-xs font-bold transition-all flex items-center gap-1"
                              title="Từ chối"
                            >
                              <X className="w-3.5 h-3.5" />
                              <span>Hủy</span>
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-shark-muted">Đã xong</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
