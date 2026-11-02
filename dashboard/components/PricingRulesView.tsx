"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  Plus,
  Trash2,
  Edit2,
  CheckCircle,
  HelpCircle,
  Zap,
  ArrowRight
} from "lucide-react";
import { api } from "@/lib/api";
import { formatVnd } from "@/lib/utils";

interface PricingRulesViewProps {
  onRefreshStats: () => void;
}

export const PricingRulesView: React.FC<PricingRulesViewProps> = ({ onRefreshStats }) => {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [ruleType, setRuleType] = useState<string>("category");
  const [targetName, setTargetName] = useState<string>("");
  const [markupType, setMarkupType] = useState<string>("percent");
  const [markupValue, setMarkupValue] = useState<string>("20");
  const [roundTo, setRoundTo] = useState<string>("1000");
  const [minPrice, setMinPrice] = useState<string>("");
  const [priority, setPriority] = useState<string>("1");

  const loadRules = async () => {
    try {
      setLoading(true);
      const res = await api.getPricingRules();
      setRules(res.rules || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleOpenCreate = () => {
    setEditingId(null);
    setRuleType("category");
    setTargetName("");
    setMarkupType("percent");
    setMarkupValue("20");
    setRoundTo("1000");
    setMinPrice("");
    setPriority("2");
    setShowModal(true);
  };

  const handleSaveRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        rule_type: ruleType,
        target_name: ruleType === "global" ? "ALL" : targetName.trim(),
        markup_type: markupType,
        markup_value: parseFloat(markupValue) || 0,
        round_to: parseInt(roundTo) || 1000,
        min_price: minPrice ? parseFloat(minPrice) : null,
        priority: parseInt(priority) || 1,
        is_active: true
      };

      if (editingId) {
        await api.updatePricingRule(editingId, payload);
      } else {
        await api.createPricingRule(payload);
      }

      setShowModal(false);
      await loadRules();
      onRefreshStats();
      alert("Đã lưu quy tắc và tự động cập nhật lại giá toàn bộ sản phẩm!");
    } catch (e: any) {
      alert(`Lỗi: ${e.message}`);
    }
  };

  const handleDeleteRule = async (id: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa quy tắc này?")) return;
    try {
      await api.deletePricingRule(id);
      await loadRules();
      onRefreshStats();
    } catch (e: any) {
      alert(`Lỗi xóa: ${e.message}`);
    }
  };

  const handleApplyAll = async () => {
    try {
      setApplying(true);
      const res = await api.reapplyAllPricing();
      onRefreshStats();
      alert(`Đã tính toán lại giá bán cho ${res.updated_products} sản phẩm thành công!`);
    } catch (e: any) {
      alert(`Lỗi: ${e.message}`);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-6 h-6 text-shark-cyan" />
            Hệ thống Kê giá Tự động (Pricing Engine)
          </h2>
          <p className="text-xs text-shark-muted">
            Tự động cộng thêm tỷ lệ lợi nhuận khi giá nguồn Canboso thay đổi. Bảo vệ biên lợi nhuận tuyệt đối.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleApplyAll}
            disabled={applying}
            className="px-4 py-2.5 rounded-xl bg-shark-card hover:bg-shark-cardHover border border-shark-border text-xs font-semibold text-white transition-all flex items-center gap-2"
          >
            <Zap className={`w-4 h-4 text-shark-cyan ${applying ? "animate-spin" : ""}`} />
            <span>Áp dụng lại toàn shop</span>
          </button>
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-shark-blue to-shark-cyan text-shark-dark font-bold text-xs shadow-glow-cyan flex items-center gap-1.5 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Thêm quy tắc mới</span>
          </button>
        </div>
      </div>

      {/* Pricing Formula Card */}
      <div className="p-5 rounded-2xl bg-shark-navy border border-shark-border/80 text-xs">
        <h3 className="font-bold text-white mb-2 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-shark-cyan" />
          Nguyên tắc tính giá bán lẻ SHARKMMO
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-shark-muted">
          <div className="p-3 bg-shark-card/40 rounded-xl border border-shark-border">
            <p className="font-semibold text-white mb-1">1. Thứ tự ưu tiên</p>
            <p>Giá nhập riêng của sản phẩm &gt; Quy tắc theo Danh mục &gt; Quy tắc Toàn hệ thống (Global) &gt; Mặc định.</p>
          </div>
          <div className="p-3 bg-shark-card/40 rounded-xl border border-shark-border">
            <p className="font-semibold text-white mb-1">2. Công thức kê giá</p>
            <p className="font-mono text-shark-cyan">Giá = Giá nguồn × (1 + %/100)</p>
            <p className="font-mono text-shark-blue">hoặc Giá = Giá nguồn + Số tiền</p>
          </div>
          <div className="p-3 bg-shark-card/40 rounded-xl border border-shark-border">
            <p className="font-semibold text-white mb-1">3. Tự động làm tròn</p>
            <p>Tự động làm tròn lên theo bội số cấu hình (mặc định 1.000 VND) để giá bán luôn đẹp mắt.</p>
          </div>
        </div>
      </div>

      {/* Rules Table */}
      <div className="rounded-2xl border border-shark-border bg-shark-card/40 overflow-hidden backdrop-blur-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-shark-border bg-shark-navy/80 text-[11px] font-bold text-shark-muted uppercase tracking-wider">
              <th className="py-3.5 px-4">Loại quy tắc</th>
              <th className="py-3.5 px-4">Mục tiêu áp dụng</th>
              <th className="py-3.5 px-4">Tỷ lệ kê thêm (Markup)</th>
              <th className="py-3.5 px-4">Làm tròn</th>
              <th className="py-3.5 px-4">Giá tối thiểu</th>
              <th className="py-3.5 px-4">Độ ưu tiên</th>
              <th className="py-3.5 px-4 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-shark-border/60 text-sm">
            {loading ? (
              <tr>
                <td colSpan={7} className="py-10 text-center text-shark-muted">
                  Đang tải quy tắc kê giá...
                </td>
              </tr>
            ) : rules.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-10 text-center text-shark-muted">
                  Chưa có quy tắc nào. Nhấn <b>Thêm quy tắc mới</b> để cấu hình!
                </td>
              </tr>
            ) : (
              rules.map((r) => (
                <tr key={r.id} className="hover:bg-shark-card/60 transition-colors">
                  <td className="py-3.5 px-4">
                    <span
                      className={`text-xs px-2.5 py-1 rounded-lg font-semibold border ${
                        r.rule_type === "global"
                          ? "bg-blue-500/10 border-blue-500/30 text-blue-400"
                          : "bg-purple-500/10 border-purple-500/30 text-purple-400"
                      }`}
                    >
                      {r.rule_type === "global" ? "Toàn hệ thống (Global)" : "Theo danh mục"}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 font-bold text-white">
                    {r.target_name === "ALL" ? "Tất cả sản phẩm" : r.target_name}
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="font-mono font-bold text-shark-cyan text-base">
                      +{r.markup_value}
                      {r.markup_type === "percent" ? "%" : " VND"}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 font-mono text-xs text-shark-muted">
                    Làm tròn {r.round_to.toLocaleString()}đ
                  </td>

                  <td className="py-3.5 px-4 font-mono text-xs text-shark-text">
                    {r.min_price ? formatVnd(r.min_price) : "Không giới hạn"}
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="text-xs px-2 py-0.5 rounded bg-shark-navy border border-shark-border text-shark-muted">
                      Priority: {r.priority}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => handleDeleteRule(r.id)}
                      className="p-1.5 rounded-lg text-rose-400 hover:bg-rose-500/20 transition-colors"
                      title="Xóa quy tắc"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Add/Edit Rule */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleSaveRule}
            className="bg-shark-navy border border-shark-border rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl"
          >
            <h3 className="font-bold text-white text-base">Thêm quy tắc kê giá mới</h3>

            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">Loại quy tắc</label>
              <select
                value={ruleType}
                onChange={(e) => setRuleType(e.target.value)}
                className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-shark-cyan"
              >
                <option value="category">Áp dụng theo Danh mục cụ thể</option>
                <option value="global">Toàn hệ thống (Tất cả sản phẩm)</option>
              </select>
            </div>

            {ruleType === "category" && (
              <div>
                <label className="text-xs font-semibold text-shark-text block mb-1">
                  Tên danh mục áp dụng
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: 🤖 AI & Đồ họa"
                  value={targetName}
                  onChange={(e) => setTargetName(e.target.value)}
                  className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-shark-cyan"
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-shark-text block mb-1">Cách tính kê giá</label>
                <select
                  value={markupType}
                  onChange={(e) => setMarkupType(e.target.value)}
                  className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-shark-cyan"
                >
                  <option value="percent">Cộng theo % (Ví dụ: +25%)</option>
                  <option value="fixed">Cộng tiền cố định (Ví dụ: +15,000đ)</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-shark-text block mb-1">Giá trị kê thêm</label>
                <input
                  type="number"
                  required
                  value={markupValue}
                  onChange={(e) => setMarkupValue(e.target.value)}
                  className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-shark-cyan"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-shark-text block mb-1">Bước làm tròn giá (VND)</label>
                <select
                  value={roundTo}
                  onChange={(e) => setRoundTo(e.target.value)}
                  className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-shark-cyan"
                >
                  <option value="1000">1.000 VND (Mặc định)</option>
                  <option value="500">500 VND</option>
                  <option value="5000">5.000 VND</option>
                  <option value="1">Không làm tròn</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-shark-text block mb-1">Giá bán tối thiểu (VND)</label>
                <input
                  type="number"
                  placeholder="Ví dụ: 10000"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-shark-cyan"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-shark-border">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 rounded-xl text-sm font-semibold text-shark-muted hover:text-white"
              >
                Hủy
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-shark-blue to-shark-cyan text-shark-dark font-bold text-sm shadow-glow-cyan"
              >
                Lưu quy tắc
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
