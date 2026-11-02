"use client";

import React, { useState, useEffect } from "react";
import {
  Settings,
  Shield,
  CreditCard,
  Bell,
  Save,
  Key,
  Globe,
  CheckCircle,
  Copy,
  Check
} from "lucide-react";
import { api } from "@/lib/api";

export const SettingsView: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Form states
  const [bankCode, setBankCode] = useState("MB");
  const [bankAccountNo, setBankAccountNo] = useState("");
  const [bankAccountName, setBankAccountName] = useState("");
  const [alertThreshold, setAlertThreshold] = useState("100000");
  const [defaultMarkup, setDefaultMarkup] = useState("20");
  const [defaultMarkupType, setDefaultMarkupType] = useState("percent");
  const [roundTo, setRoundTo] = useState("1000");
  const [autoSyncInterval, setAutoSyncInterval] = useState("15");

  // Read-only info
  const [botTokenStatus, setBotTokenStatus] = useState("");
  const [canbosoKeyStatus, setCanbosoKeyStatus] = useState("");

  const loadSettings = async () => {
    try {
      setLoading(true);
      const res = await api.getSettings();
      const cfg = res.config || {};
      setBankCode(cfg.bank_code || "MB");
      setBankAccountNo(cfg.bank_account_no || "");
      setBankAccountName(cfg.bank_account_name || "");
      setAlertThreshold(String(cfg.source_balance_alert_threshold || 100000));
      setDefaultMarkup(String(cfg.default_markup_value || 20));
      setDefaultMarkupType(cfg.default_markup_type || "percent");
      setRoundTo(String(cfg.default_round_to || 1000));
      setAutoSyncInterval(String(cfg.auto_sync_interval || 15));
      setBotTokenStatus(cfg.bot_token_status || "");
      setCanbosoKeyStatus(cfg.canboso_key_status || "");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await api.updateSettings({
        bank_code: bankCode.trim(),
        bank_account_no: bankAccountNo.trim(),
        bank_account_name: bankAccountName.trim(),
        source_balance_alert_threshold: parseFloat(alertThreshold) || 100000,
        default_markup_value: parseFloat(defaultMarkup) || 20,
        default_markup_type: defaultMarkupType,
        default_round_to: parseInt(roundTo) || 1000,
        auto_sync_interval: parseInt(autoSyncInterval) || 15
      });
      alert("Đã lưu cấu hình hệ thống thành công!");
    } catch (e: any) {
      alert(`Lỗi lưu cấu hình: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const copyUrl = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const domain = typeof window !== "undefined" ? window.location.origin : "https://your-domain.com";

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Settings className="w-6 h-6 text-shark-cyan" />
            Cấu hình Hệ thống SHARKMMO
          </h2>
          <p className="text-xs text-shark-muted">
            Quản lý tài khoản ngân hàng VietQR, ngưỡng cảnh báo và thông tin kết nối an toàn.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Bank & VietQR Config */}
        <div className="p-6 rounded-2xl bg-shark-card/40 border border-shark-border space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-shark-cyan" />
            Cấu hình Ngân hàng nhận thanh toán (VietQR)
          </h3>
          <p className="text-xs text-shark-muted">
            Hệ thống sẽ tạo mã QR động dẫn thẳng về tài khoản này với nội dung chuyển khoản tự động khớp lệnh.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">Mã ngân hàng (Bank Code)</label>
              <select
                value={bankCode}
                onChange={(e) => setBankCode(e.target.value)}
                className="w-full bg-shark-navy border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
              >
                <option value="MB">MBBank (Quân Đội)</option>
                <option value="VCB">Vietcombank</option>
                <option value="TCB">Techcombank</option>
                <option value="VPB">VPBank</option>
                <option value="ACB">ACB</option>
                <option value="BIDV">BIDV</option>
                <option value="CTG">VietinBank</option>
                <option value="TPB">TPBank</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">Số tài khoản ngân hàng</label>
              <input
                type="text"
                required
                placeholder="Ví dụ: 0988888888"
                value={bankAccountNo}
                onChange={(e) => setBankAccountNo(e.target.value)}
                className="w-full bg-shark-navy border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">Tên chủ tài khoản (In hoa không dấu)</label>
              <input
                type="text"
                required
                placeholder="Ví dụ: NGUYEN VAN A"
                value={bankAccountName}
                onChange={(e) => setBankAccountName(e.target.value)}
                className="w-full bg-shark-navy border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan uppercase"
              />
            </div>
          </div>
        </div>

        {/* Pricing & Sync Settings */}
        <div className="p-6 rounded-2xl bg-shark-card/40 border border-shark-border space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Bell className="w-5 h-5 text-shark-cyan" />
            Cấu hình Kho nguồn & Tỷ lệ Kê giá mặc định
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">
                Ngưỡng cảnh báo số dư kho thấp (VND)
              </label>
              <input
                type="number"
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(e.target.value)}
                className="w-full bg-shark-navy border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
              />
              <p className="text-[11px] text-shark-muted mt-1">Khi số dư Canboso thấp hơn mức này, bot sẽ gửi cảnh báo.</p>
            </div>

            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">
                Tỷ lệ kê giá mặc định (%)
              </label>
              <input
                type="number"
                value={defaultMarkup}
                onChange={(e) => setDefaultMarkup(e.target.value)}
                className="w-full bg-shark-navy border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
              />
              <p className="text-[11px] text-shark-muted mt-1">Áp dụng cho mọi sản phẩm khi chưa có quy tắc riêng.</p>
            </div>

            <div>
              <label className="text-xs font-semibold text-shark-text block mb-1">
                Chu kỳ tự động đồng bộ kho (Phút)
              </label>
              <input
                type="number"
                value={autoSyncInterval}
                onChange={(e) => setAutoSyncInterval(e.target.value)}
                className="w-full bg-shark-navy border border-shark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-shark-cyan"
              />
              <p className="text-[11px] text-shark-muted mt-1">Tự động tải lại giá nguồn và số lượng từ Canboso.</p>
            </div>
          </div>
        </div>

        {/* API Credentials Security Display */}
        <div className="p-6 rounded-2xl bg-shark-card/40 border border-shark-border space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Shield className="w-5 h-5 text-shark-cyan" />
            Bảo mật & Khóa API (.env)
          </h3>
          <p className="text-xs text-shark-muted">
            Theo tiêu chuẩn an toàn, các khóa bí mật được lưu trong biến môi trường và được che đi trong giao diện quản trị.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-shark-navy rounded-xl border border-shark-border flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-white">Canboso Buyer Key (x-buyer-key)</p>
                <p className="text-xs font-mono text-shark-muted mt-1">{canbosoKeyStatus || "(Chưa có)"}</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-semibold">
                <CheckCircle className="w-3.5 h-3.5" /> Bảo mật
              </span>
            </div>

            <div className="p-4 bg-shark-navy rounded-xl border border-shark-border flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-white">Telegram Bot Token</p>
                <p className="text-xs font-mono text-shark-muted mt-1">{botTokenStatus || "(Chưa có)"}</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-semibold">
                <CheckCircle className="w-3.5 h-3.5" /> Bảo mật
              </span>
            </div>
          </div>
        </div>

        {/* Webhook URLs */}
        <div className="p-6 rounded-2xl bg-shark-card/40 border border-shark-border space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Globe className="w-5 h-5 text-shark-cyan" />
            Đường dẫn Webhook Thanh toán tự động
          </h3>
          <p className="text-xs text-shark-muted">
            Cấu hình các Webhook URL này vào tài khoản SePay hoặc ứng dụng ngân hàng để nhận biến động số dư tự động.
          </p>

          <div className="space-y-3">
            <div className="p-3 bg-shark-navy rounded-xl border border-shark-border flex items-center justify-between text-xs font-mono">
              <div>
                <span className="text-shark-muted block text-[11px] font-sans">SePay Webhook URL:</span>
                <span className="text-shark-cyan font-bold">{domain}/api/v1/webhooks/sepay</span>
              </div>
              <button
                type="button"
                onClick={() => copyUrl(`${domain}/api/v1/webhooks/sepay`, "sepay")}
                className="text-shark-muted hover:text-white px-2 py-1 rounded border border-shark-border"
              >
                {copiedKey === "sepay" ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            <div className="p-3 bg-shark-navy rounded-xl border border-shark-border flex items-center justify-between text-xs font-mono">
              <div>
                <span className="text-shark-muted block text-[11px] font-sans">Generic Bank Webhook URL:</span>
                <span className="text-shark-cyan font-bold">{domain}/api/v1/webhooks/bank</span>
              </div>
              <button
                type="button"
                onClick={() => copyUrl(`${domain}/api/v1/webhooks/bank`, "bank")}
                className="text-shark-muted hover:text-white px-2 py-1 rounded border border-shark-border"
              >
                {copiedKey === "bank" ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-shark-blue to-shark-cyan text-shark-dark font-black text-sm shadow-glow-cyan flex items-center gap-2 hover:opacity-90 transition-all disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? "Đang lưu..." : "Lưu tất cả thay đổi"}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
