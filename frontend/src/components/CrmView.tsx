'use strict';
'use client';

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  ShieldAlert, 
  RefreshCw, 
  Copy, 
  Check, 
  CheckCircle2, 
  Clock, 
  Phone,
  Search,
  ExternalLink
} from 'lucide-react';
import { Lead, HandoffTicket } from '@/types';
import { getLeads, getHandoffs } from '@/lib/api';

export function CrmView() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [handoffs, setHandoffs] = useState<HandoffTicket[]>([]);
  const [activeTab, setActiveTab] = useState<'leads' | 'handoffs'>('leads');
  const [isLoading, setIsLoading] = useState(true);
  const [copiedPhone, setCopiedPhone] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [leadsData, handoffsData] = await Promise.all([
        getLeads().catch(() => ({ leads: [] })),
        getHandoffs().catch(() => ({ handoffs: [] })),
      ]);
      setLeads(leadsData.leads || []);
      setHandoffs(handoffsData.handoffs || []);
    } catch (err) {
      console.error('Failed to load CRM data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCopyPhone = (phone: string) => {
    navigator.clipboard.writeText(phone);
    setCopiedPhone(phone);
    setTimeout(() => setCopiedPhone(null), 1500);
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-rose-50 text-rose-700 border border-rose-200">URGENT</span>;
      case 'high':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-orange-50 text-orange-700 border border-orange-200">HIGH</span>;
      case 'medium':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-50 text-amber-700 border border-amber-200">MEDIUM</span>;
      default:
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-600 border border-slate-200">LOW</span>;
    }
  };

  const filteredLeads = leads.filter(l => 
    (l.name && l.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    l.phone.includes(searchTerm) ||
    (l.needs_summary && l.needs_summary.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const filteredHandoffs = handoffs.filter(h => 
    h.ticket_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    h.reason.toLowerCase().includes(searchTerm.toLowerCase()) ||
    h.summary.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-y-auto">
      {/* Top Header */}
      <header className="px-6 py-4 border-b border-slate-200 bg-white shrink-0 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-base font-semibold text-slate-900 leading-tight">
              Quản trị CRM & Chuyển giao Bán hàng
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Theo dõi khách hàng tiềm năng có xác nhận Consent và các vé chuyển giao nhân viên
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={loadData}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium shadow-2xs transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Làm mới</span>
            </button>
          </div>
        </div>

        {/* Tab Switcher & Search Bar */}
        <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            <button
              type="button"
              onClick={() => setActiveTab('leads')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'leads'
                  ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users className="w-3.5 h-3.5 text-blue-600" />
              <span>Khách hàng tiềm năng (Leads)</span>
              <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-medium">
                {leads.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('handoffs')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'handoffs'
                  ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
              <span>Vé Handoff Nhân viên</span>
              <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-medium">
                {handoffs.length}
              </span>
            </button>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Tìm theo số điện thoại, tên, mã vé..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>
      </header>

      {/* Main Table View */}
      <div className="p-6">
        {activeTab === 'leads' ? (
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-medium">
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Khách hàng</th>
                    <th className="px-4 py-3">Số điện thoại</th>
                    <th className="px-4 py-3">Sản phẩm quan tâm</th>
                    <th className="px-4 py-3">Ngân sách</th>
                    <th className="px-4 py-3">Nhu cầu ghi nhận</th>
                    <th className="px-4 py-3">Đồng thuận (Consent)</th>
                    <th className="px-4 py-3">Thời điểm</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {isLoading && leads.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                        Đang tải danh sách Lead...
                      </td>
                    </tr>
                  ) : filteredLeads.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                        Chưa có lead nào trong hệ thống.
                      </td>
                    </tr>
                  ) : (
                    filteredLeads.map((l) => (
                      <tr key={l.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 font-mono text-slate-400">#{l.id}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">{l.name || 'Khách vãng lai'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200 font-medium">
                              {l.phone}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleCopyPhone(l.phone)}
                              className="text-slate-400 hover:text-slate-600 p-0.5"
                              title="Sao chép số"
                            >
                              {copiedPhone === l.phone ? (
                                <Check className="w-3.5 h-3.5 text-emerald-600" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-700">
                          {Array.isArray(l.product_skus) ? l.product_skus.join(', ') : (l.product_skus || '-')}
                        </td>
                        <td className="px-4 py-3 font-medium text-slate-800">
                          {l.budget_vnd ? `${Number(l.budget_vnd).toLocaleString('vi-VN')} đ` : '-'}
                        </td>
                        <td className="px-4 py-3 text-slate-600 max-w-xs truncate" title={l.needs_summary || ''}>
                          {l.needs_summary || '-'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Đã đồng thuận</span>
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-400 text-[11px]">
                          {l.created_at ? l.created_at.replace('T', ' ').slice(0, 19) : '-'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-medium">
                    <th className="px-4 py-3">Mã Vé</th>
                    <th className="px-4 py-3">Lý do chuyển</th>
                    <th className="px-4 py-3">Ưu tiên</th>
                    <th className="px-4 py-3">Tóm tắt ngữ cảnh</th>
                    <th className="px-4 py-3">Hành động đề xuất cho Sales</th>
                    <th className="px-4 py-3">Trạng thái</th>
                    <th className="px-4 py-3">Thời điểm</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {isLoading && handoffs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                        Đang tải danh sách vé Handoff...
                      </td>
                    </tr>
                  ) : filteredHandoffs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                        Chưa có vé chuyển giao nào.
                      </td>
                    </tr>
                  ) : (
                    filteredHandoffs.map((h) => (
                      <tr key={h.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 font-mono font-medium text-blue-600">
                          {h.ticket_id}
                        </td>
                        <td className="px-4 py-3 font-medium text-slate-900 capitalize">
                          {h.reason.replace(/_/g, ' ')}
                        </td>
                        <td className="px-4 py-3">
                          {getPriorityBadge(h.priority)}
                        </td>
                        <td className="px-4 py-3 text-slate-700 max-w-sm truncate" title={h.summary}>
                          {h.summary}
                        </td>
                        <td className="px-4 py-3 text-blue-700 font-medium">
                          {h.suggested_next_action || '-'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                            {h.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-400 text-[11px]">
                          {h.created_at ? h.created_at.replace('T', ' ').slice(0, 19) : '-'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
