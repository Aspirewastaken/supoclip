#!/bin/bash
# SupoClip Font Downloader
# Downloads recommended open-source fonts for caption and title generation

set -e  # Exit on error

cd "$(dirname "$0")"

echo "📥 SupoClip Font Downloader"
echo "============================"
echo ""
echo "This script will download 5 high-quality open-source fonts:"
echo "  1. Montserrat Bold (Proxima Nova alternative)"
echo "  2. Inter Bold (best for readability)"
echo "  3. Poppins Bold (friendly, social media)"
echo "  4. Roboto Bold (universal)"
echo "  5. Open Sans Bold (maximum legibility)"
echo ""

# Check for wget
if ! command -v wget &> /dev/null; then
    echo "❌ Error: wget is required but not installed."
    echo "Install it with: sudo apt-get install wget  # Ubuntu/Debian"
    echo "               brew install wget            # macOS"
    exit 1
fi

# Check for unzip (needed for Roboto)
if ! command -v unzip &> /dev/null; then
    echo "❌ Error: unzip is required but not installed."
    echo "Install it with: sudo apt-get install unzip  # Ubuntu/Debian"
    exit 1
fi

# Function to download with retry
download_with_retry() {
    local url=$1
    local output=$2
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if wget -q --show-progress --timeout=30 "$url" -O "$output"; then
            return 0
        else
            echo "⚠️  Attempt $attempt failed, retrying..."
            attempt=$((attempt + 1))
            sleep 2
        fi
    done

    echo "❌ Failed to download after $max_attempts attempts"
    return 1
}

# Track successes
success_count=0
total_count=5

# 1. Montserrat Bold
echo ""
echo "[1/5] Downloading Montserrat Bold..."
if download_with_retry \
    "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf" \
    "Montserrat-Bold.ttf"; then
    echo "✅ Montserrat Bold downloaded"
    success_count=$((success_count + 1))
else
    echo "⚠️  Montserrat Bold failed - skipping"
fi

# 2. Inter Bold
echo ""
echo "[2/5] Downloading Inter Bold..."
if download_with_retry \
    "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.ttf" \
    "Inter-Bold.ttf"; then
    echo "✅ Inter Bold downloaded"
    success_count=$((success_count + 1))
else
    echo "⚠️  Inter Bold failed - skipping"
fi

# 3. Poppins Bold
echo ""
echo "[3/5] Downloading Poppins Bold..."
if download_with_retry \
    "https://github.com/itfoundry/Poppins/raw/master/products/Poppins-Bold.ttf" \
    "Poppins-Bold.ttf"; then
    echo "✅ Poppins Bold downloaded"
    success_count=$((success_count + 1))
else
    echo "⚠️  Poppins Bold failed - skipping"
fi

# 4. Roboto Bold
echo ""
echo "[4/5] Downloading Roboto Bold..."
if download_with_retry \
    "https://github.com/google/roboto/releases/download/v2.138/roboto-unhinted.zip" \
    "roboto-temp.zip"; then
    if unzip -q -o roboto-temp.zip "Roboto-Bold.ttf" 2>/dev/null; then
        rm roboto-temp.zip
        echo "✅ Roboto Bold downloaded"
        success_count=$((success_count + 1))
    else
        echo "⚠️  Roboto Bold extraction failed - skipping"
        rm -f roboto-temp.zip
    fi
else
    echo "⚠️  Roboto Bold failed - skipping"
    rm -f roboto-temp.zip
fi

# 5. Open Sans Bold
echo ""
echo "[5/5] Downloading Open Sans Bold..."
if download_with_retry \
    "https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf" \
    "OpenSans-Bold.ttf"; then
    echo "✅ Open Sans Bold downloaded"
    success_count=$((success_count + 1))
else
    echo "⚠️  Open Sans Bold failed - skipping"
fi

# Summary
echo ""
echo "============================"
echo "✅ Download complete: $success_count/$total_count fonts"
echo ""
echo "📋 Available fonts in $(pwd):"
ls -1 *.ttf | sed 's/^/  - /'

echo ""
if [ $success_count -eq $total_count ]; then
    echo "🎉 All fonts downloaded successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Restart the backend: docker-compose restart backend"
    echo "  2. List fonts via API: curl http://localhost:8000/fonts"
    echo "  3. Use in requests with 'font_family' parameter"
else
    echo "⚠️  Some fonts failed to download. You can:"
    echo "  1. Re-run this script to retry"
    echo "  2. Manually download from URLs in README.md"
    echo "  3. Use the fonts that were successfully downloaded"
fi

echo ""
echo "For more information, see: backend/fonts/README.md"
