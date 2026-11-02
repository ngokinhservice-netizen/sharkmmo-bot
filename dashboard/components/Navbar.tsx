"use client";

import React from "react";
import { RefreshCw, Wallet, AlertTriangle, Shield, Bell } from "lucide-react";
import { formatVnd } from "@/lib/utils";

interface NavbarProps {
  sourceBalance?: {
    balance: number;
    formatted: string;
    is_low: boolean;
    usdt?: number;
  };
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  sourceBalance,
  onRefresh,
  isRefreshing
}) => {
  return (
    <header className="h-20 bg-shark-navy/80 backdrop-blur-md border-b border-shark-border px-8 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          Hệ thống Quản trị SHARKMMO
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-shark-blue/10 border border-shark-blue/30 text-shark-blue font-semibold">
            v2.0 PRO
          </span>
        </h2>
        <p className="text-xs text-shark-muted">Hệ sinh thái sản phẩm MMO tự động</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Source Balance Badge */}
        {sourceBalance && (
          <div
            className={`flex items-center gap-3 px-4 py-2 rounded-xl border text-sm font-semibold transition-all ${
              sourceBalance.is_low
                ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
                : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            }`}
          >
            <Wallet className="w-4 h-4" />
            <div>
              <span className="text-xs font-normal text-shark-muted block">Số dư kho Canboso:</span>
              <span>{sourceBalance.formatted || formatVnd(sourceBalance.balance)}</span>
              {sourceBalance.usdt ? (
                <span className="ml-2 text-xs font-normal text-shark-cyan">({sourceBalance.usdt} USDT)</span>
              ) : null}
            </div>
            {sourceBalance.is_low && (
              <span className="flex items-center gap-1 text-xs bg-rose-500 text-white px-2 py-0.5 rounded-full font-bold ml-1 animate-pulse">
                <AlertTriangle className="w-3 h-3" /> Nạp kho!
              </span>
            )}
          </div>
        )}

        {/* Sync Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-shark-card border border-shark-border hover:border-shark-cyan/40 text-shark-text text-sm font-medium hover:text-shark-cyan transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-shark-cyan" : ""}`} />
          <span>Làm mới</span>
        </button>

        {/* Admin Profile */}
        <div className="flex items-center gap-3 pl-3 border-l border-shark-border">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-shark-blue to-shark-cyan flex items-center justify-center text-shark-dark font-black text-sm">
            A
          </div>
          <div className="text-left hidden md:block">
            <p className="text-xs font-bold text-white">Super Admin</p>
            <p className="text-[11px] text-shark-muted">ID: 1336962312</p>
          </div>
        </div>
      </div>
    </header>
  );
};
