#!/bin/bash
cd "$(dirname "$0")"

echo "============================================"
echo "   AFFILIATE DASHBOARD - 10 Kênh x 4 Nền Tảng"
echo "============================================"
echo ""

# Tìm Python 3
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "[LỖI] Không tìm thấy Python3 trên máy Mac!"
    exit 1
fi

echo "[OK] Sử dụng Python: $($PYTHON_BIN --version)"
echo "Đang khởi động Dashboard trên http://localhost:5001 ..."
echo "LƯU Ý: Cổng 5001 được dùng để tránh xung đột với AirPlay Receiver của macOS (cổng 5000)."
echo "Nhấn Ctrl+C để tắt server."
echo ""

$PYTHON_BIN app.py --port 5001
