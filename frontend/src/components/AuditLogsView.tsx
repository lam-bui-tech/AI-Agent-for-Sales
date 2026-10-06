'use strict';
'use client';

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  RefreshCw, 
  Search, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Copy, 
  Check, 
  X,
  Code
} from 'lucide-react';
import { AuditLog } from '@/types';
import { getAuditLogs } from '@/lib/api';

export function AuditLogsView() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [copiedType, setCopiedType] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await getAuditLogs();
      setLogs(data.audit_logs || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatJson = (val: string | any) => {
    if (!val) return '{}';
    if (typeof val === 'string') {
      try {
        return JSON.stringify(JSON.parse(val), null, 2);
      } catch {
        return val;
      }
    }
    return JSON.stringify(val, null, 2);
  };

  const handleCopy = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopiedType(type);
    setTimeout(() => setCopiedType(null), 1500);
  };

  const filteredLogs = logs.filter(l =>
    l.tool_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.input_payload && l.input_payload.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-y-auto">
      {/* Top Header */}
      <header className="px-6 py-4 border-b border-slate-200 bg-white shrink-0 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-base font-semibold text-slate-900 leading-tight">
              Nhật ký gọi Tool (Audit Logs Telemetry)
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Chứng minh Agent thực sự gọi tool lấy dữ liệu thời gian thực thay vì sinh số liệu từ trí nhớ
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

        {/* Search */}
        <div className="mt-4 flex items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Lọc theo tên Tool hoặc tham số (ví dụ: search_products)..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
          <span className="text-xs font-mono text-slate-500">
            Tổng cộng: <strong>{logs.length}</strong> lượt gọi
          </span>
        </div>
      </header>

      {/* Main Table */}
      <div className="p-6">
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-medium">
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Tên Tool</th>
                  <th className="px-4 py-3">Tham số đầu vào (Input)</th>
                  <th className="px-4 py-3">Thời gian xử lý</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Thời điểm</th>
                  <th className="px-4 py-3 text-right">Chi tiết</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading && logs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                      Đang tải nhật ký audit...
                    </td>
                  </tr>
                ) : filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                      Chưa có lượt gọi tool nào.
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((l) => {
                    const isSuccess = l.success === true || l.success === 1;
                    return (
                      <tr key={l.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 font-mono text-slate-400">#{l.id}</td>
                        <td className="px-4 py-3">
                          <span className="font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 text-[11px]">
                            {l.tool_name}
                          </span>
                        </td>
                        <td className="px-4 py-3 max-w-xs font-mono text-slate-600 truncate text-[11px]" title={l.input_payload}>
                          {l.input_payload}
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-700">
                          {l.execution_time_ms ? `${l.execution_time_ms.toFixed(1)} ms` : '<1 ms'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            isSuccess 
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}>
                            {isSuccess ? <CheckCircle2 className="w-2.5 h-2.5 text-emerald-600" /> : <XCircle className="w-2.5 h-2.5 text-rose-600" />}
                            <span>{isSuccess ? 'Success' : 'Failed'}</span>
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-400 text-[11px]">
                          {l.created_at ? l.created_at.replace('T', ' ').slice(0, 19) : '-'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            onClick={() => setSelectedLog(l)}
                            className="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                          >
                            Xem Payload
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
      </div>

      {/* Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-2xl w-full max-h-[85vh] flex flex-col shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-blue-600" />
                <h3 className="font-semibold text-sm text-slate-900">
                  Chi tiết Tool Call: <span className="font-mono text-blue-700">{selectedLog.tool_name}</span> #{selectedLog.id}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedLog(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-4 space-y-4 overflow-y-auto flex-1 font-mono text-xs">
              <div>
                <div className="flex items-center justify-between text-slate-500 font-sans font-medium mb-1.5">
                  <span>Input Payload:</span>
                  <button
                    type="button"
                    onClick={() => handleCopy(formatJson(selectedLog.input_payload), 'input')}
                    className="flex items-center gap-1 text-slate-500 hover:text-slate-900 px-1.5 py-0.5 rounded hover:bg-slate-100"
                  >
                    {copiedType === 'input' ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedType === 'input' ? 'Đã sao chép' : 'Sao chép'}</span>
                  </button>
                </div>
                <pre className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 overflow-x-auto max-h-48 leading-relaxed">
                  {formatJson(selectedLog.input_payload)}
                </pre>
              </div>

              <div>
                <div className="flex items-center justify-between text-slate-500 font-sans font-medium mb-1.5">
                  <span>Output Payload:</span>
                  <button
                    type="button"
                    onClick={() => handleCopy(formatJson(selectedLog.output_payload), 'output')}
                    className="flex items-center gap-1 text-slate-500 hover:text-slate-900 px-1.5 py-0.5 rounded hover:bg-slate-100"
                  >
                    {copiedType === 'output' ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedType === 'output' ? 'Đã sao chép' : 'Sao chép'}</span>
                  </button>
                </div>
                <pre className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 overflow-x-auto max-h-56 leading-relaxed">
                  {formatJson(selectedLog.output_payload)}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-slate-200 bg-slate-50/70 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedLog(null)}
                className="px-3 py-1.5 rounded-md bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-medium transition-colors"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
