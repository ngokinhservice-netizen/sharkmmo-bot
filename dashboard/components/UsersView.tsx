"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  Search,
  Lock,
  Unlock,
  PlusCircle,
  Shield,
  CreditCard,
  X
} from "lucide-react";
import { api } from "@/lib/api";
import { formatVnd } from "@/lib/utils";

interface UsersViewProps {
  onRefreshStats: () => void;
}

export const UsersView: React.FC<UsersViewProps> = ({ onRefreshStats }) => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editingUser, setEditingUser] = useState<any | null>(null);
  const [adjustAmount, setAdjustAmount] = useState<string>("");
  const [adjustReason, setAdjustReason] = useState<string>("");

  const loadUsers = async () => {
    try {
      setLoading(true);
      const res = await api.getUsers({ search: search || undefined });
      setUsers(res.users || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadUsers();
  };

  const handleToggleBan = async (u: any) => {
    const actionText = u.is_banned ? "mở khóa" : "khóa";
    if (!confirm(`Bạn có chắc muốn ${actionText} tài khoản @${u.username || u.telegram_id}?`)) return;
    try {
      await api.updateUser(u.id, { is_banned: !u.is_banned });
      await loadUsers();
      onRefreshStats();
    } catch (e: any) {
      alert(`Lỗi: ${e.message}`);
    }
  };

  const handleAdjustBalance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    const amount = parseFloat(adjustAmount);
    if (isNaN(amount) || amount === 0) {
      alert("Vui lòng nhập số tiền hợp lệ (dương để nạp, âm để trừ).");
      return;
    }
    try {
      await api.updateUser(editingUser.id, {
        balance_adjustment: amount,
        reason: adjustReason.trim()
      });
      setEditingUser(null);
      setAdjustAmount("");
      setAdjustReason("");
      await loadUsers();
      onRefreshStats();
      alert("Cập nhật số dư người dùng thành công!");
    } catch (e: any) {
      alert(`Lỗi: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-shark-cyan" />
            Quản lý Khách hàng & Thành viên
          </h2>
          <p className="text-xs text-shark-muted">
            Quản lý tài khoản Telegram người dùng, số dư ví nạp tiền và trạng thái hoạt động.
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-4 justify-between items-center bg-shark-card/40 p-4 rounded-2xl border border-shark-border">
        <form onSubmit={handleSearch} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-shark-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Tìm theo Telegram ID, username..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-shark-navy/80 border border-shark-border rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-shark-muted focus:outline-none focus:border-shark-cyan transition-all"
          />
        </form>
      </div>

      {/* Users Table */}
      <div className="rounded-2xl border border-shark-border bg-shark-card/40 overflow-hidden backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-shark-border bg-shark-navy/80 text-[11px] font-bold text-shark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Telegram ID</th>
                <th className="py-3.5 px-4">Tài khoản & Tên</th>
                <th className="py-3.5 px-4">Số dư ví</th>
                <th className="py-3.5 px-4">Tổng chi tiêu</th>
                <th className="py-3.5 px-4">Đơn hàng</th>
                <th className="py-3.5 px-4">Vai trò</th>
                <th className="py-3.5 px-4">Trạng thái</th>
                <th className="py-3.5 px-4">Ngày đăng ký</th>
                <th className="py-3.5 px-4 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-shark-border/60 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    Đang tải danh sách khách hàng...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    Chưa có khách hàng nào tương tác với bot.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-shark-card/60 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-shark-cyan text-xs">
                      {u.telegram_id}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-white">{u.first_name || ""} {u.last_name || ""}</div>
                      <div className="text-[11px] text-shark-muted">@{u.username || "Chưa đặt"}</div>
                    </td>

                    <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                      {formatVnd(u.balance)}
                    </td>

                    <td className="py-3.5 px-4 font-mono text-shark-text text-xs">
                      {formatVnd(u.total_spent)}
                    </td>

                    <td className="py-3.5 px-4 font-semibold text-white">
                      {u.total_orders} đơn
                    </td>

                    <td className="py-3.5 px-4">
                      {u.role === "admin" ? (
                        <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1 w-fit">
                          <Shield className="w-3 h-3" /> Admin
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded bg-shark-navy text-shark-muted border border-shark-border">
                          Khách hàng
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                          u.is_banned
                            ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
                            : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                        }`}
                      >
                        {u.is_banned ? "Bị khóa" : "Hoạt động"}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-shark-muted whitespace-nowrap">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString("vi-VN") : "N/A"}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => {
                            setEditingUser(u);
                            setAdjustAmount("");
                            setAdjustReason("");
                          }}
                          className="px-2.5 py-1 rounded-lg bg-shark-navy hover:bg-shark-cardHover border border-shark-border hover:border-shark-cyan text-xs font-semibold text-white flex items-center gap-1 transition-all"
                          title="Điều chỉnh số dư ví"
                        >
                          <CreditCard className="w-3.5 h-3.5 text-shark-cyan" />
                          <span>Ví</span>
                        </button>
                        <button
                          onClick={() => handleToggleBan(u)}
                          className={`p-1.5 rounded-lg border transition-colors ${
                            u.is_banned
                              ? "text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
                              : "text-rose-400 border-rose-500/30 hover:bg-rose-500/10"
                          }`}
                          title={u.is_banned ? "Mở khóa tài khoản" : "Khóa tài khoản"}
                        >
                          {u.is_banned ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Adjust Balance Modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleAdjustBalance}
            className="bg-shark-navy border border-shark-border rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl relative"
          >
            <div className="flex items-center justify-between pb-3 border-b border-shark-border">
              <div>
                <h3 className="font-bold text-white text-base">Điều chỉnh số dư ví khách</h3>
                <p className="text-xs text-shark-muted">
                  {editingUser.first_name} (Telegram: {editingUser.telegram_id})
                </p>
              </div>
              <button
                type="button"
                onClick={() => setEditingUser(null)}
                className="text-shark-muted hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 bg-shark-card rounded-xl border border-shark-border flex justify-between text-xs">
              <span className="text-shark-muted">Số dư hiện tại:</span>
              <span className="font-mono font-bold text-emerald-400">{formatVnd(editingUser.balance)}</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">
                Số tiền điều chỉnh (VND)
              </label>
              <input
                type="number"
                required
                placeholder="Ví dụ: +50000 hoặc -20000"
                value={adjustAmount}
                onChange={(e) => setAdjustAmount(e.target.value)}
                className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
              />
              <p className="text-[11px] text-shark-muted mt-1">
                Nhập số dương để nạp thêm, nhập số âm để trừ tiền.
              </p>
            </div>

            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">
                Lý do điều chỉnh (Audit Log)
              </label>
              <input
                type="text"
                placeholder="Ví dụ: Nạp tiền đối soát chuyển khoản ngân hàng"
                value={adjustReason}
                onChange={(e) => setAdjustReason(e.target.value)}
                className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-shark-border">
              <button
                type="button"
                onClick={() => setEditingUser(null)}
                className="px-4 py-2 rounded-xl text-sm font-semibold text-shark-muted hover:text-white"
              >
                Hủy
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-shark-blue to-shark-cyan text-shark-dark font-bold text-sm shadow-glow-cyan"
              >
                Xác nhận
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
