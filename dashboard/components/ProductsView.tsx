"use client";

import React, { useState, useEffect } from "react";
import {
  Package,
  Search,
  RefreshCw,
  Edit2,
  Eye,
  EyeOff,
  Filter,
  Check,
  X,
  TrendingUp,
  Tag
} from "lucide-react";
import { api } from "@/lib/api";
import { formatVnd } from "@/lib/utils";

interface ProductsViewProps {
  onRefreshStats: () => void;
}

export const ProductsView: React.FC<ProductsViewProps> = ({ onRefreshStats }) => {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [editingProduct, setEditingProduct] = useState<any | null>(null);

  // Form states for modal
  const [customPrice, setCustomPrice] = useState<string>("");
  const [markupType, setMarkupType] = useState<string>("percent");
  const [markupValue, setMarkupValue] = useState<string>("");
  const [categoryInput, setCategoryInput] = useState<string>("");

  const loadProducts = async () => {
    try {
      setLoading(true);
      const res = await api.getProducts({
        category: selectedCategory === "ALL" ? undefined : selectedCategory,
        search: search || undefined
      });
      setProducts(res.products || []);
    } catch (e) {
      console.error("Error loading products:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [selectedCategory]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadProducts();
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      await api.syncProducts();
      await loadProducts();
      onRefreshStats();
      alert("Đồng bộ sản phẩm từ Canboso thành công!");
    } catch (e: any) {
      alert(`Đồng bộ thất bại: ${e.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleToggleActive = async (p: any) => {
    try {
      const newStatus = !p.is_active;
      await api.updateProduct(p.id, { is_active: newStatus });
      setProducts(products.map((item) => (item.id === p.id ? { ...item, is_active: newStatus } : item)));
    } catch (e: any) {
      alert(`Lỗi cập nhật trạng thái: ${e.message}`);
    }
  };

  const openEditModal = (p: any) => {
    setEditingProduct(p);
    setCustomPrice(p.custom_price ? String(p.custom_price) : "");
    setMarkupType(p.custom_markup_type || "percent");
    setMarkupValue(p.custom_markup_value ? String(p.custom_markup_value) : "");
    setCategoryInput(p.category || "");
  };

  const handleSaveProduct = async () => {
    if (!editingProduct) return;
    try {
      const payload: any = {
        category: categoryInput.trim(),
        custom_price: customPrice ? parseFloat(customPrice) : 0,
        custom_markup_type: markupValue ? markupType : "",
        custom_markup_value: markupValue ? parseFloat(markupValue) : 0
      };
      await api.updateProduct(editingProduct.id, payload);
      setEditingProduct(null);
      await loadProducts();
      onRefreshStats();
    } catch (e: any) {
      alert(`Lỗi cập nhật sản phẩm: ${e.message}`);
    }
  };

  // Extract unique categories
  const categories = ["ALL", ...Array.from(new Set(products.map((p) => p.category)))];

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-shark-cyan" />
            Quản lý Kho & Kê giá Sản phẩm
          </h2>
          <p className="text-xs text-shark-muted">
            Dữ liệu đồng bộ trực tiếp từ Canboso API. Cho phép đặt giá override riêng hoặc theo % markup.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-shark-card border border-shark-border hover:border-shark-cyan text-sm font-semibold text-white hover:text-shark-cyan transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? "animate-spin text-shark-cyan" : ""}`} />
            <span>Đồng bộ từ Canboso API</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-shark-card/40 p-4 rounded-2xl border border-shark-border">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-shark-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Tìm tên hoặc mã sản phẩm..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-shark-navy/80 border border-shark-border rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-shark-muted focus:outline-none focus:border-shark-cyan transition-all"
          />
        </form>

        {/* Category Pills */}
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? "bg-shark-blue text-white shadow-glow-blue"
                  : "bg-shark-navy/60 text-shark-muted hover:text-white border border-shark-border"
              }`}
            >
              {cat === "ALL" ? "Tất cả danh mục" : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Products Table */}
      <div className="rounded-2xl border border-shark-border bg-shark-card/40 overflow-hidden backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-shark-border bg-shark-navy/80 text-[11px] font-bold text-shark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Sản phẩm</th>
                <th className="py-3.5 px-4">Danh mục & Loại</th>
                <th className="py-3.5 px-4">Giá nguồn (Canboso)</th>
                <th className="py-3.5 px-4">Kê giá / Markup</th>
                <th className="py-3.5 px-4">Giá bán SHARKMMO</th>
                <th className="py-3.5 px-4">Lợi nhuận</th>
                <th className="py-3.5 px-4">Kho hàng</th>
                <th className="py-3.5 px-4">Trạng thái</th>
                <th className="py-3.5 px-4 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-shark-border/60 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-shark-cyan" />
                    Đang tải dữ liệu sản phẩm...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-shark-muted">
                    Không tìm thấy sản phẩm nào. Nhấn <b>Đồng bộ từ Canboso API</b> để nạp sản phẩm!
                  </td>
                </tr>
              ) : (
                products.map((p) => {
                  const profit = p.calculated_price - p.source_price;
                  const profitPercent = p.source_price > 0 ? Math.round((profit / p.source_price) * 100) : 0;

                  return (
                    <tr key={p.id} className="hover:bg-shark-card/60 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-white max-w-xs truncate">{p.name}</div>
                        <div className="text-[11px] text-shark-muted font-mono">{p.product_id}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="text-xs px-2.5 py-1 rounded-lg bg-shark-navy border border-shark-border text-shark-text inline-block">
                          {p.category}
                        </span>
                        <div className="text-[11px] text-shark-muted mt-1 uppercase font-mono">{p.product_type}</div>
                      </td>

                      <td className="py-3.5 px-4 font-mono font-semibold text-slate-300">
                        {formatVnd(p.source_price)}
                      </td>

                      <td className="py-3.5 px-4">
                        {p.custom_price ? (
                          <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                            Giá cố định: {formatVnd(p.custom_price)}
                          </span>
                        ) : p.custom_markup_value ? (
                          <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                            +{p.custom_markup_value}
                            {p.custom_markup_type === "percent" ? "%" : "đ"}
                          </span>
                        ) : (
                          <span className="text-xs text-shark-muted">Quy tắc tự động</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 font-bold text-shark-cyan font-mono text-base">
                        {formatVnd(p.calculated_price)}
                      </td>

                      <td className="py-3.5 px-4 font-mono text-emerald-400 font-semibold text-xs">
                        +{formatVnd(profit)}
                        <span className="text-[10px] text-shark-muted ml-1">({profitPercent}%)</span>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="text-xs text-white">
                          Còn: <b>{p.available_qty !== null ? p.available_qty : "Sẵn có"}</b>
                        </div>
                        <div className="text-[11px] text-shark-muted">Đã bán: {p.sold_qty}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <button
                          onClick={() => handleToggleActive(p)}
                          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all ${
                            p.is_active
                              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                              : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                          }`}
                        >
                          {p.is_active ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                          <span>{p.is_active ? "Đang hiện" : "Đã ẩn"}</span>
                        </button>
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => openEditModal(p)}
                          className="px-3 py-1.5 rounded-xl bg-shark-navy hover:bg-shark-cardHover border border-shark-border hover:border-shark-cyan text-xs font-semibold text-white flex items-center gap-1.5 ml-auto transition-all"
                        >
                          <Edit2 className="w-3.5 h-3.5 text-shark-cyan" />
                          <span>Kê giá</span>
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

      {/* Edit Pricing Modal */}
      {editingProduct && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-shark-navy border border-shark-border rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-shark-border">
              <div>
                <h3 className="font-bold text-white text-base">Cấu hình giá bán sản phẩm</h3>
                <p className="text-xs text-shark-muted">{editingProduct.name}</p>
              </div>
              <button
                onClick={() => setEditingProduct(null)}
                className="text-shark-muted hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Source Price Readonly */}
              <div className="p-3 bg-shark-card rounded-xl border border-shark-border flex items-center justify-between text-sm">
                <span className="text-shark-muted">Giá vốn nguồn Canboso:</span>
                <span className="font-mono font-bold text-white">{formatVnd(editingProduct.source_price)}</span>
              </div>

              {/* Option A: Direct Override Price */}
              <div>
                <label className="text-xs font-semibold text-shark-text block mb-1">
                  Cách 1: Nhập giá bán trực tiếp (Ưu tiên cao nhất)
                </label>
                <input
                  type="number"
                  placeholder="Ví dụ: 89000 (Để trống nếu dùng % markup)"
                  value={customPrice}
                  onChange={(e) => setCustomPrice(e.target.value)}
                  className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
                />
              </div>

              {/* Option B: Custom Markup */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-shark-text block mb-1">
                    Cách 2: Loại kê giá
                  </label>
                  <select
                    value={markupType}
                    onChange={(e) => setMarkupType(e.target.value)}
                    className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
                  >
                    <option value="percent">Phần trăm (%)</option>
                    <option value="fixed">Số tiền cố định (VND)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-shark-text block mb-1">
                    Giá trị kê thêm
                  </label>
                  <input
                    type="number"
                    placeholder="Ví dụ: 25 (% hoặc đ)"
                    value={markupValue}
                    onChange={(e) => setMarkupValue(e.target.value)}
                    className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
                  />
                </div>
              </div>

              {/* Category selector */}
              <div>
                <label className="text-xs font-semibold text-shark-text block mb-1">
                  Danh mục hiển thị trong bot
                </label>
                <input
                  type="text"
                  placeholder="Ví dụ: 🤖 AI & Đồ họa"
                  value={categoryInput}
                  onChange={(e) => setCategoryInput(e.target.value)}
                  className="w-full bg-shark-card border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-shark-border">
              <button
                onClick={() => setEditingProduct(null)}
                className="px-4 py-2 rounded-xl text-sm font-semibold text-shark-muted hover:text-white transition-colors"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleSaveProduct}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-shark-blue to-shark-cyan text-shark-dark font-bold text-sm shadow-glow-cyan hover:opacity-90 transition-all"
              >
                Lưu thay đổi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
