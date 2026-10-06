'use strict';
'use client';

import React, { useState, useEffect } from 'react';
import { 
  QrCode, 
  RefreshCw, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  Smartphone,
  ShieldCheck
} from 'lucide-react';
import { getZaloInfo, triggerZaloLogin, getZaloStatus, getApiBase } from '@/lib/api';

interface ZaloModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ZaloModal({ isOpen, onClose }: ZaloModalProps) {
  const [qrUrl, setQrUrl] = useState<string>('');
  const [status, setStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchQr = async () => {
    setIsLoading(true);
    try {
      const base = getApiBase();
      const timestamp = new Date().getTime();
      setQrUrl(`${base}/api/zalo/qr.png?t=${timestamp}`);
      const st = await getZaloStatus();
      setStatus(st);
    } catch (err) {
      console.error('Failed to load Zalo status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshQr = async () => {
    setIsLoading(true);
    try {
      await triggerZaloLogin(true);
      setTimeout(() => {
        fetchQr();
      }, 1500);
    } catch (err) {
      console.error('Failed to trigger Zalo login:', err);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchQr();
      const interval = setInterval(() => {
        getZaloStatus().then(st => setStatus(st)).catch(() => {});
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isConnected = status && (status.status === 'connected' || status.connected === true);

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <QrCode className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-slate-900">Liên kết tài khoản Zalo</h3>
              <p className="text-[11px] text-slate-500">Đăng nhập tài khoản tư vấn Zalo Personal qua OpenClaw</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 flex flex-col items-center text-center space-y-4">
          {isConnected ? (
            <div className="py-8 space-y-3">
              <div className="w-12 h-12 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h4 className="font-semibold text-sm text-slate-900">Zalo đã kết nối thành công!</h4>
              <p className="text-xs text-slate-500 max-w-xs">
                Agent Mèo Con hiện đã sẵn sàng nhận tin nhắn và tự động tư vấn khách hàng trên Zalo Personal.
              </p>
            </div>
          ) : (
            <>
              <div className="relative p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                {qrUrl ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={qrUrl}
                    alt="Mã QR Zalo"
                    className="w-52 h-52 object-contain rounded-lg"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-52 h-52 flex items-center justify-center text-slate-400 text-xs">
                    Đang tải mã QR...
                  </div>
                )}
                {isLoading && (
                  <div className="absolute inset-0 bg-white/80 backdrop-blur-2xs rounded-xl flex items-center justify-center">
                    <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
                  </div>
                )}
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-center gap-1.5 text-xs font-medium text-slate-800">
                  <Smartphone className="w-4 h-4 text-slate-500" />
                  <span>Dùng ứng dụng Zalo trên điện thoại quét mã QR</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Mở Zalo &gt; Chọn biểu tượng QR góc trên cùng bên phải &gt; Quét mã trên màn hình
                </p>
              </div>

              {/* Status info */}
              <div className="w-full p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-left text-xs flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                  <span className="text-slate-600">Trạng thái kết nối:</span>
                </div>
                <span className="font-medium text-slate-900 font-mono text-[11px]">
                  {status ? (status.message || status.status || 'Chờ quét') : 'Đang kiểm tra...'}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-slate-200 bg-slate-50/70 flex items-center justify-between">
          <button
            type="button"
            onClick={handleRefreshQr}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium shadow-2xs transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Tạo mới mã QR</span>
          </button>

          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-2xs transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}
