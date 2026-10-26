#!/bin/bash
# ==============================================================================
# Script tự động dọn dẹp Cache thuật toán CapCut (videoAlg & Temp) trên macOS
# Tương thích macOS Sonoma, Ventura, Monterey (Chip M1/M2/M3/M4 & Intel)
# ==============================================================================

echo "================================================================"
echo "    QUÉT VÀ XÓA CACHE VIDEO RENDER CAPCUT TRÊN MACOS (videoAlg) "
echo "================================================================"
echo ""

# Các đường dẫn phổ biến của CapCut trên macOS
CAPCUT_DIRS=(
  "$HOME/Movies/CapCut/User Data/Projects"
  "$HOME/Library/Containers/com.lemon.cuteditor/Data/Movies/CapCut/User Data/Projects"
  "$HOME/Library/Application Support/CapCut/User Data/Projects"
)

FOUND=0

for PROJECTS_DIR in "${CAPCUT_DIRS[@]}"; do
  if [ -d "$PROJECTS_DIR" ]; then
    FOUND=1
    echo "🔍 Tìm thấy thư mục dự án CapCut tại:"
    echo "   $PROJECTS_DIR"
    echo ""
    echo "🧹 Đang quét và xóa cache 'videoAlg' & 'draft_content_temp'..."
    
    # Xóa các thư mục videoAlg (chứa video uncompressed upscale làm nặng GB)
    find "$PROJECTS_DIR" -type d -name "videoAlg" -exec rm -rf {} + 2>/dev/null
    find "$PROJECTS_DIR" -type d -name "draft_content_temp" -exec rm -rf {} + 2>/dev/null
    find "$PROJECTS_DIR" -type d -name "Cache" -exec rm -rf {} + 2>/dev/null
    find "$PROJECTS_DIR" -type d -name "proxy" -exec rm -rf {} + 2>/dev/null
    
    echo "✅ Đã dọn dẹp sạch sẽ các tệp cache phình to ổ cứng trong thư mục này!"
    echo ""
  fi
done

# Dọn dẹp thêm cache toàn cục của ứng dụng CapCut trên macOS nếu có
GLOBAL_CACHE="$HOME/Library/Caches/com.lemon.cuteditor"
if [ -d "$GLOBAL_CACHE" ]; then
  echo "🧹 Đang dọn dẹp App Cache tại: $GLOBAL_CACHE"
  rm -rf "$GLOBAL_CACHE"/* 2>/dev/null
  echo "✅ Đã dọn dẹp cache toàn cục!"
fi

if [ $FOUND -eq 0 ]; then
  echo "⚠️ Không tìm thấy thư mục CapCut mặc định. Nếu bạn cài đặt ở thư mục tùy chỉnh, hãy kiểm tra lại đường dẫn."
fi

echo ""
echo "🎉 HOÀN TẤT! Đã giải phóng dung lượng ổ cứng trên máy Mac của bạn."
