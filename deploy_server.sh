#!/bin/bash
set -e
echo "=================================================="
echo "🚀 [ThueDo.net] Bắt đầu cập nhật hệ thống lên server"
echo "=================================================="

# Bung nén gói cập nhật
if [ -f "update_code.tar.gz" ]; then
    echo "📦 Đang bung nén update_code.tar.gz..."
    tar -xzvf update_code.tar.gz
fi

# Khởi động lại Docker containers
echo "🔄 Khởi động lại Docker services..."
docker compose down && docker compose up -d

echo ""
echo "=================================================="
echo "✅ Cập nhật thành công!"
echo "🤖 Telegram Bot: @pmthuedo_bot đã sẵn sàng"
echo "🧠 AI Model: Dion AI balanced (Gemini 3.7 Flash)"
echo "🌐 API Webhook: https://assistant-sales.lab.dion.vn/"
echo "=================================================="
