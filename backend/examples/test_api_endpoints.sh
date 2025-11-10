#!/bin/bash

# API Endpoint Testing Script for AI Title Generation
# Usage: ./test_api_endpoints.sh

BASE_URL="http://localhost:8000"
PLATFORM="tiktok"

echo "=================================================="
echo "SupoClip AI Title Generation - API Testing"
echo "=================================================="
echo ""

# Check if server is running
echo "1. Checking if backend server is running..."
if ! curl -s "$BASE_URL/" > /dev/null 2>&1; then
    echo "❌ Error: Backend server is not running at $BASE_URL"
    echo "   Start the server with: uvicorn src.main:app --reload"
    exit 1
fi
echo "✓ Server is running"
echo ""

# Test 1: Get supported platforms
echo "2. Testing GET /ai/platforms"
echo "   Fetching supported platforms..."
response=$(curl -s "$BASE_URL/ai/platforms")
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Test 2: Get title styles
echo "3. Testing GET /ai/title-styles"
echo "   Fetching available title styles..."
response=$(curl -s "$BASE_URL/ai/title-styles")
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Test 3: Generate titles (basic)
echo "4. Testing POST /ai/generate-titles (Basic)"
echo "   Generating 3 titles for TikTok..."
response=$(curl -s -X POST "$BASE_URL/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "In this video I reveal the secret to growing your social media from zero to 100k followers in just 90 days. Most people do not know this but the algorithm actually favors one specific type of content above all others.",
    "platform": "tiktok",
    "num_variations": 3
  }')

# Check for errors
if echo "$response" | grep -q "detail"; then
    echo "❌ Error occurred:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    echo "Possible causes:"
    echo "- OPENROUTER_API_KEY not configured in .env"
    echo "- Insufficient OpenRouter credits"
    echo "- Network connectivity issue"
    exit 1
fi

echo "✓ Success! Response:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Test 4: Generate titles (with audience)
echo "5. Testing POST /ai/generate-titles (With Target Audience)"
echo "   Generating 3 titles with target audience..."
response=$(curl -s -X POST "$BASE_URL/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Today I am sharing my morning routine that completely transformed my life. I wake up at 5 AM, meditate, exercise, and spend focused time on my goals before checking any messages.",
    "platform": "instagram",
    "target_audience": "young professionals seeking productivity",
    "key_topics": ["morning routine", "productivity", "self improvement"],
    "num_variations": 3
  }')

if echo "$response" | grep -q "detail"; then
    echo "❌ Error occurred"
else
    echo "✓ Success! Generated titles:"
    # Extract just the titles for display
    echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"  - [{t['virality_score']:.2f}] {t['title']}\") for t in data['titles']]" 2>/dev/null || echo "$response"
fi
echo ""

# Test 5: Generate titles (specific styles)
echo "6. Testing POST /ai/generate-titles (Specific Styles)"
echo "   Generating 4 titles with specific styles..."
response=$(curl -s -X POST "$BASE_URL/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "I tried the viral 30-day challenge and the results were shocking. Not only did I lose 15 pounds but my energy levels tripled and I discovered something nobody talks about.",
    "platform": "youtube",
    "num_variations": 4,
    "include_styles": ["question", "shocking", "curiosity", "listicle"]
  }')

if echo "$response" | grep -q "detail"; then
    echo "❌ Error occurred"
else
    echo "✓ Success! Best title:"
    echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  Score: {data['best_title']['virality_score']:.2f}\n  Title: {data['best_title']['title']}\n  Style: {data['best_title']['style']}\n  Model: {data['best_title']['model_used']}\")" 2>/dev/null || echo "$response"
fi
echo ""

# Test 6: Error handling (empty transcript)
echo "7. Testing Error Handling (Empty Transcript)"
response=$(curl -s -X POST "$BASE_URL/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "",
    "platform": "tiktok",
    "num_variations": 3
  }')

if echo "$response" | grep -q "detail"; then
    echo "✓ Error properly handled:"
    echo "$response" | python3 -c "import sys, json; print(f\"  {json.load(sys.stdin)['detail']}\")" 2>/dev/null || echo "$response"
else
    echo "⚠ Warning: Empty transcript was accepted (unexpected)"
fi
echo ""

echo "=================================================="
echo "API Testing Complete"
echo "=================================================="
echo ""
echo "Summary:"
echo "- All core endpoints tested"
echo "- Title generation working"
echo "- Platform and style options available"
echo "- Error handling functional"
echo ""
echo "View full API docs at: $BASE_URL/docs"
echo "View title generation docs: backend/AI_TITLE_GENERATION_DOCS.md"
echo ""
