'use strict';
'use client';

import React from 'react';
import { 
  MessageSquare, 
  Laptop, 
  Users, 
  Activity, 
  QrCode, 
  RotateCcw, 
  Layers, 
  ExternalLink,
  Radio
} from 'lucide-react';

export type NavTab = 'chat' | 'catalog' | 'crm' | 'audit';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  onOpenZalo: () => void;
  onResetChat: () => void;
}

export function Sidebar({ currentTab, onSelectTab, onOpenZalo, onResetChat }: SidebarProps) {
  const navItems = [
    { id: 'chat' as NavTab, label: 'Trò chuyện Copilot', icon: MessageSquare, badge: null },
    { id: 'catalog' as NavTab, label: 'Danh mục Laptop', icon: Laptop, badge: '15 SKU' },
    { id: 'crm' as NavTab, label: 'Quản trị Leads & Vé', icon: Users, badge: null },
    { id: 'audit' as NavTab, label: 'Nhật ký Audit Logs', icon: Activity, badge: null },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-sm text-slate-900 leading-tight">DemoTech</div>
            <div className="text-[11px] text-slate-500 font-medium">Sales Copilot</div>
          </div>
        </div>
        <span className="text-[10px] font-semibold tracking-wide uppercase px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
          v2.0
        </span>
      </div>

      {/* Main Navigation */}
      <div className="p-3 flex-1 flex flex-col gap-1 overflow-y-auto">
        <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Phân hệ làm việc
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-all ${
                isActive
                  ? 'bg-blue-50 text-blue-700 shadow-2xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                  isActive ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-500'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        <div className="mt-3 px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Kênh & Tích hợp
        </div>

        <button
          type="button"
          onClick={onOpenZalo}
          className="w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-all"
        >
          <div className="flex items-center gap-2.5">
            <QrCode className="w-4 h-4 text-slate-500" />
            <span>Đăng nhập Zalo QR</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-mono">Sync</span>
        </button>

        <a
          href="https://t.me/lamOpclw_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-all"
        >
          <div className="flex items-center gap-2.5">
            <ExternalLink className="w-4 h-4 text-slate-500" />
            <span>Telegram Bot</span>
          </div>
          <span className="text-[10px] text-blue-600 font-mono">@lamOpclw_bot</span>
        </a>
      </div>

      {/* Footer / System Health */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/50 space-y-2.5">
        <div className="p-2.5 rounded-md bg-white border border-slate-200 text-[11px] space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-slate-500 font-medium">Gateway:</span>
            <div className="flex items-center gap-1.5 font-medium text-emerald-700">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span>OpenClaw MCP</span>
            </div>
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>Agent: Mèo Con</span>
            <span>Port: 8088/8090</span>
          </div>
        </div>

        <button
          type="button"
          onClick={onResetChat}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 text-xs font-medium transition-colors shadow-2xs"
        >
          <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
          <span>Làm mới phiên chat</span>
        </button>
      </div>
    </aside>
  );
}
