'use strict';
'use client';

import React, { useState, useEffect } from 'react';
import { 
  Search, 
  RefreshCw, 
  MessageSquare, 
  Cpu, 
  HardDrive, 
  Monitor, 
  Weight, 
  CheckCircle2, 
  XCircle,
  SlidersHorizontal
} from 'lucide-react';
import { Product, InventoryItem } from '@/types';
import { getCatalog, getInventory, adjustInventory } from '@/lib/api';

interface CatalogViewProps {
  onAskAboutProduct: (prompt: string) => void;
}

export function CatalogView({ onAskAboutProduct }: CatalogViewProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [inventory, setInventory] = useState<Record<string, InventoryItem>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [updatingSku, setUpdatingSku] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [catData, invData] = await Promise.all([
        getCatalog(),
        getInventory().catch(() => ({ inventory: {} }))
      ]);
      setProducts(catData.products || []);
      setInventory(invData.inventory || {});
    } catch (err) {
      console.error('Failed to load catalog data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleStock = async (sku: string, currentQty: number) => {
    const newQty = currentQty > 0 ? 0 : 5;
    setUpdatingSku(sku);
    try {
      await adjustInventory(sku, newQty);
      setInventory(prev => ({
        ...prev,
        [sku]: {
          available: newQty > 0,
          quantity: newQty,
          updated_at: new Date().toISOString()
        }
      }));
    } catch (err) {
      console.error('Failed to adjust stock:', err);
    } finally {
      setUpdatingSku(null);
    }
  };

  const brands = ['all', ...Array.from(new Set(products.map(p => p.brand))).filter(Boolean)];

  const filteredProducts = products.filter(p => {
    const matchesSearch = 
      (p.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.sku || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.cpu || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.summary || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.brand || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesBrand = selectedBrand === 'all' || (p.brand || '').toLowerCase() === selectedBrand.toLowerCase();
    return matchesSearch && matchesBrand;
  });

  const inStockCount = products.filter(p => {
    const item = inventory[p.sku];
    return item && item.available && item.quantity > 0;
  }).length;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-y-auto">
      {/* Top Header */}
      <header className="px-6 py-4 border-b border-slate-200 bg-white shrink-0 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-base font-semibold text-slate-900 leading-tight">
              Danh mục Gói cước & Thiết bị ThueDo.net
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              3 gói phần mềm SaaS & 4 thiết bị chuyên dụng cho shop thuê trang phục
            </p>
          </div>

          {/* Stats Badges */}
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
              <span>Tổng cộng:</span>
              <strong className="font-mono">{products.length} SKU</strong>
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Sẵn sàng:</span>
              <strong className="font-mono">{inStockCount}</strong>
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
              <span>Tạm hết:</span>
              <strong className="font-mono">{products.length - inStockCount}</strong>
            </span>
            <button
              type="button"
              onClick={loadData}
              title="Làm mới dữ liệu"
              className="p-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Filters and Search Bar */}
        <div className="mt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Lọc theo tên gói/thiết bị, mã SKU, tính năng (ví dụ: Starter, Pro, Máy in, PKG-PRO)..."
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-slate-900 placeholder:text-slate-400"
            />
          </div>

          {/* Brand Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {brands.map(brand => (
              <button
                key={brand}
                type="button"
                onClick={() => setSelectedBrand(brand)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors capitalize ${
                  selectedBrand === brand
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {brand === 'all' ? 'Tất cả phân loại' : brand}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Grid Content */}
      <div className="p-6">
        {isLoading && products.length === 0 ? (
          <div className="text-center py-16 text-slate-400 text-xs">
            Đang tải dữ liệu danh mục ThueDo.net...
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-16 text-slate-400 text-xs">
            Không tìm thấy gói hoặc thiết bị nào khớp với từ khóa lọc.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProducts.map((p) => {
              const inv = inventory[p.sku] || { available: false, quantity: 0 };
              const isAvailable = inv.available && inv.quantity > 0;
              const isUpdating = updatingSku === p.sku;

              return (
                <div
                  key={p.sku}
                  className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:shadow-xs transition-shadow flex flex-col justify-between"
                >
                  <div>
                    {/* Card Top: SKU, Brand, Stock Badge */}
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                          {p.sku}
                        </span>
                        <span className="text-[10px] font-medium text-slate-500 uppercase">
                          {p.brand}
                        </span>
                      </div>

                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          isAvailable
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${isAvailable ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                        <span>
                          {isAvailable 
                            ? (p.sku.startsWith('PKG-') ? 'Kích hoạt ngay' : `Còn ${inv.quantity} máy/cuộn`) 
                            : 'Tạm hết'}
                        </span>
                      </span>
                    </div>

                    {/* Product Name */}
                    <h3 className="font-semibold text-sm text-slate-900 leading-snug line-clamp-1 mb-1">
                      {p.name}
                    </h3>

                    {/* Price */}
                    <div className="text-blue-600 font-semibold text-base mb-2">
                      {Number(p.price_vnd).toLocaleString('vi-VN')} đ
                    </div>

                    {/* Summary */}
                    <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-2 mb-3">
                      {p.summary}
                    </p>

                    {/* Specs Grid */}
                    <div className="grid grid-cols-2 gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-[11px] mb-3">
                      <div className="space-y-0.5">
                        <div className="text-slate-400 flex items-center gap-1">
                          <Cpu className="w-3 h-3 text-slate-400" />
                          <span>Quy mô</span>
                        </div>
                        <div className="font-medium text-slate-700 truncate" title={p.cpu || p.target_use}>
                          {p.cpu || p.target_use || 'Tiêu chuẩn'}
                        </div>
                      </div>

                      <div className="space-y-0.5">
                        <div className="text-slate-400 flex items-center gap-1">
                          <HardDrive className="w-3 h-3 text-slate-400" />
                          <span>Tài khoản / Thử</span>
                        </div>
                        <div className="font-medium text-slate-700 truncate">
                          {p.ram_gb && p.ram_gb > 0 ? `${p.ram_gb} tài khoản` : 'Dùng thử 15 ngày'}
                        </div>
                      </div>

                      <div className="space-y-0.5">
                        <div className="text-slate-400 flex items-center gap-1">
                          <Monitor className="w-3 h-3 text-slate-400" />
                          <span>Tính năng / QR</span>
                        </div>
                        <div className="font-medium text-slate-700 truncate" title={p.screen}>
                          {p.screen || 'Cloud / Web'}
                        </div>
                      </div>

                      <div className="space-y-0.5">
                        <div className="text-slate-400 flex items-center gap-1">
                          <Weight className="w-3 h-3 text-slate-400" />
                          <span>Nền tảng</span>
                        </div>
                        <div className="font-medium text-slate-700 truncate">
                          {p.os || (p.weight_kg ? `${p.weight_kg} kg` : 'Cloud Web/App')}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => onAskAboutProduct(`Tư vấn giúp mình ${p.name} (${p.sku}) với`)}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium transition-colors"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Hỏi tư vấn mục này</span>
                    </button>

                    <button
                      type="button"
                      disabled={isUpdating}
                      onClick={() => handleToggleStock(p.sku, inv.quantity)}
                      className={`px-2.5 py-1.5 rounded-md border text-xs font-medium transition-colors ${
                        isAvailable
                          ? 'border-rose-200 text-rose-700 hover:bg-rose-50'
                          : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                      }`}
                    >
                      {isUpdating ? '...' : isAvailable ? 'Hạ tồn (0)' : 'Nạp kho (5)'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
