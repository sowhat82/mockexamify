#!/bin/bash
# Quick script to get your Streamlit app URL for bookmarking

echo "🚀 MockExamify - Get Your App URL"
echo "=================================="
echo ""

# Check if running in Codespaces
if [ -n "$CODESPACE_NAME" ]; then
    APP_URL="https://${CODESPACE_NAME}-8501.app.github.dev"
    echo "✅ Your Codespace App URL:"
    echo ""
    echo "   $APP_URL"
    echo ""
    echo "📌 Bookmark this URL in your mobile Chrome browser!"
    echo ""
    echo "💡 This URL opens the app directly in Chrome, not in Codespaces."
    echo ""
else
    echo "ℹ️  Not running in Codespaces"
    echo ""
    echo "Your local URLs:"
    echo "   Local:    http://localhost:8501"
    echo "   Network:  http://$(hostname -I | awk '{print $1}'):8501"
    echo ""
fi

echo "🔗 To open now:"
echo "   1. Copy the URL above"
echo "   2. Paste in Chrome on your mobile"
echo "   3. Bookmark it for quick access!"
echo ""
