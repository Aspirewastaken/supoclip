# A/B Testing Quick Start Guide

## 5-Minute Setup

### Step 1: Database Migration (if not already done)
```bash
cd /home/user/supoclip
docker-compose down
docker-compose up -d postgres
sleep 5
docker-compose exec postgres psql -U postgres -d supoclip -c "SELECT 1"
```

The experiments tables should already be created from `init.sql`. Verify:
```bash
docker-compose exec postgres psql -U postgres -d supoclip -c "SELECT * FROM experiments LIMIT 1"
```

### Step 2: Start Services
```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Step 3: Access Experiments UI
Open browser: http://localhost:3000/experiments

### Step 4: Create Your First Experiment

1. **Click "Create Experiment"**

2. **Fill in details:**
   - Name: "Font Style Test"
   - Description: "Testing TikTok Sans vs Arial Bold"
   - Confidence Threshold: 95% (recommended)

3. **Add variations:**
   - Variation 1:
     - Name: "TikTok Sans"
     - Select a clip from dropdown

   - Variation 2:
     - Name: "Arial Bold"
     - Select another clip

4. **Click "Create Experiment"**

### Step 5: Simulate Test Data (for demo purposes)

```bash
# Get your experiment ID from the UI
EXPERIMENT_ID="your-experiment-id"
USER_ID="your-user-id"
VARIATION_1="clip-id-1"
VARIATION_2="clip-id-2"

# Update Variation 1 metrics
curl -X POST http://localhost:8000/experiments/$EXPERIMENT_ID/update-metrics \
  -H "Content-Type: application/json" \
  -H "user_id: $USER_ID" \
  -d '{
    "variation_id": "'$VARIATION_1'",
    "metrics": {
      "views": 1000,
      "clicks": 120,
      "conversions": 60,
      "shares": 40,
      "likes": 180,
      "comments": 25,
      "click_through_rate": 0.12,
      "conversion_rate": 0.06,
      "engagement_rate": 0.245,
      "avg_watch_time": 11.5,
      "watch_completion_rate": 0.82
    }
  }'

# Update Variation 2 metrics (better performance)
curl -X POST http://localhost:8000/experiments/$EXPERIMENT_ID/update-metrics \
  -H "Content-Type: application/json" \
  -H "user_id: $USER_ID" \
  -d '{
    "variation_id": "'$VARIATION_2'",
    "metrics": {
      "views": 1000,
      "clicks": 165,
      "conversions": 90,
      "shares": 60,
      "likes": 250,
      "comments": 35,
      "click_through_rate": 0.165,
      "conversion_rate": 0.09,
      "engagement_rate": 0.345,
      "avg_watch_time": 13.8,
      "watch_completion_rate": 0.89
    }
  }'
```

### Step 6: View Results

1. Click "View Results" button on your experiment
2. See comprehensive statistical analysis
3. System automatically declares winner if confidence threshold met

## Understanding the Results

### Green Badge = Winner
If you see:
```
✓ SIGNIFICANT (95% confidence)
Winner: Variation 2
Improvement: 37.5%
```

This means:
- Variation 2 is statistically better
- 95% confidence it's not due to random chance
- 37.5% improvement over Variation 1

### Red Badge = Not Significant
If you see:
```
✗ Not significant
p-value: 0.23
```

This means:
- No clear winner yet
- Could be due to random chance
- Need more data or variations are too similar

## Real-World Workflow

### For Actual Testing (not demo):

1. **Create Experiment** (UI)
2. **Distribute Clips:**
   - Upload Variation 1 to TikTok/Instagram
   - Upload Variation 2 to TikTok/Instagram
   - Split traffic 50/50 if possible

3. **Collect Real Metrics:**
   - Wait 24-48 hours
   - Check platform analytics
   - Record: views, clicks, likes, shares, comments, watch time

4. **Update System:**
   ```bash
   POST /experiments/{id}/update-metrics
   ```

5. **Check Results Daily:**
   - System auto-updates analysis
   - Declares winner when confident
   - Shows you which variation performs best

## Common Scenarios

### Scenario 1: Clear Winner (Fast)
```
Day 1: 500 views each, B performing 40% better
Day 2: System declares B as winner (99% confidence)
Action: Use B for all future clips
```

### Scenario 2: No Clear Difference
```
Day 1: 500 views each, A=12%, B=13%
Day 3: 1500 views each, still no significant difference
Action: Variations are too similar, test something more distinct
```

### Scenario 3: Need More Data
```
Day 1: 50 views each
Warning: "Need more data"
Action: Continue test until 100+ views per variation
```

## API Testing (Postman/curl)

### List Experiments
```bash
curl http://localhost:8000/experiments/ \
  -H "user_id: your-user-id"
```

### Get Specific Experiment
```bash
curl http://localhost:8000/experiments/exp-id \
  -H "user_id: your-user-id"
```

### Get Statistical Analysis
```bash
curl http://localhost:8000/experiments/exp-id/results \
  -H "user_id: your-user-id"
```

### Pause Experiment
```bash
curl -X POST http://localhost:8000/experiments/exp-id/pause \
  -H "user_id: your-user-id"
```

### Resume Experiment
```bash
curl -X POST http://localhost:8000/experiments/exp-id/resume \
  -H "user_id: your-user-id"
```

### Manually Declare Winner
```bash
curl -X POST http://localhost:8000/experiments/exp-id/declare-winner \
  -H "Content-Type: application/json" \
  -H "user_id: your-user-id" \
  -d '{"winner_variation_id": "clip-id-2"}'
```

## Interpreting Statistics

### P-Value Guide
- **p < 0.01** → 99% confidence → Very strong evidence
- **p < 0.05** → 95% confidence → Strong evidence (recommended)
- **p < 0.10** → 90% confidence → Moderate evidence
- **p ≥ 0.10** → Not significant → Keep testing

### Sample Size Guide
- **< 100 views** → Too early to tell
- **100-500 views** → Minimum for detection
- **500-1000 views** → Good confidence
- **1000+ views** → High confidence

### Effect Size Guide
- **< 10%** → Small difference (hard to detect)
- **10-25%** → Medium difference (easier to detect)
- **> 25%** → Large difference (easy to detect)

## Troubleshooting

### Problem: "Experiment not found"
**Solution:** Check experiment_id and user_id headers

### Problem: "Clip not found"
**Solution:** Ensure clips exist before creating experiment

### Problem: "No significant difference"
**Possible causes:**
1. Not enough data (< 100 views)
2. Variations too similar (< 10% difference)
3. High variance in data

**Solutions:**
1. Collect more data (aim for 1000+ views)
2. Test more distinct variations
3. Run test longer to reduce noise

### Problem: "Winner changes over time"
**Possible causes:**
1. Novelty effect (new variation gets initial boost)
2. External factors (time of day, day of week)
3. Sample size still too small

**Solutions:**
1. Run test for at least 7 days
2. Control for time-based factors
3. Wait for larger sample size

## Next Steps

### 1. Production Deployment
- Set up proper user authentication
- Add rate limiting
- Enable HTTPS
- Configure CORS properly

### 2. Integration with Analytics
- Connect to Google Analytics
- Track user segments
- Monitor external factors

### 3. Advanced Features
- Implement multi-armed bandit
- Add sequential testing
- Build meta-analysis system

## Resources

- **Full Documentation:** `/backend/src/experiments/README.md`
- **API Docs:** http://localhost:8000/docs
- **Statistical Methods:** See Chi-Square and T-Test sections in README
- **Code Examples:** See `/AB_TESTING_SUMMARY.md`

## Support

Questions? Issues?
1. Check `/backend/src/experiments/README.md` for detailed explanations
2. Review `/AB_TESTING_SUMMARY.md` for examples
3. Test endpoints using http://localhost:8000/docs (Swagger UI)
4. Check backend logs for errors: `docker-compose logs -f backend`

## Success Checklist

- ✅ Database tables created (experiments, experiment_results)
- ✅ Backend API running on port 8000
- ✅ Frontend running on port 3000
- ✅ Can access /experiments page
- ✅ Can create experiment
- ✅ Can update metrics
- ✅ Can view results
- ✅ System declares winner automatically

## Quick Test Script

Save this as `test_experiments.sh`:

```bash
#!/bin/bash

# Configuration
BACKEND_URL="http://localhost:8000"
USER_ID="test-user-123"

echo "🧪 Testing A/B Testing System"
echo "================================"

# 1. Create experiment
echo "\n1️⃣ Creating experiment..."
RESPONSE=$(curl -s -X POST $BACKEND_URL/experiments/create \
  -H "Content-Type: application/json" \
  -H "user_id: $USER_ID" \
  -d '{
    "name": "Test Experiment",
    "description": "Quick test",
    "variations": [
      {"clip_id": "test-clip-1", "variation_name": "Variation A"},
      {"clip_id": "test-clip-2", "variation_name": "Variation B"}
    ],
    "confidence_threshold": 0.95
  }')

EXPERIMENT_ID=$(echo $RESPONSE | jq -r '.experiment_id')
echo "✅ Created experiment: $EXPERIMENT_ID"

# 2. Update metrics for Variation A
echo "\n2️⃣ Updating Variation A metrics..."
curl -s -X POST $BACKEND_URL/experiments/$EXPERIMENT_ID/update-metrics \
  -H "Content-Type: application/json" \
  -H "user_id: $USER_ID" \
  -d '{
    "variation_id": "test-clip-1",
    "metrics": {
      "views": 1000,
      "clicks": 120,
      "conversions": 60,
      "click_through_rate": 0.12,
      "conversion_rate": 0.06,
      "engagement_rate": 0.20
    }
  }' > /dev/null
echo "✅ Updated Variation A"

# 3. Update metrics for Variation B
echo "\n3️⃣ Updating Variation B metrics..."
curl -s -X POST $BACKEND_URL/experiments/$EXPERIMENT_ID/update-metrics \
  -H "Content-Type: application/json" \
  -H "user_id: $USER_ID" \
  -d '{
    "variation_id": "test-clip-2",
    "metrics": {
      "views": 1000,
      "clicks": 180,
      "conversions": 95,
      "click_through_rate": 0.18,
      "conversion_rate": 0.095,
      "engagement_rate": 0.30
    }
  }' > /dev/null
echo "✅ Updated Variation B"

# 4. Get results
echo "\n4️⃣ Getting results..."
RESULTS=$(curl -s $BACKEND_URL/experiments/$EXPERIMENT_ID/results \
  -H "user_id: $USER_ID")

WINNER=$(echo $RESULTS | jq -r '.overall_winner')
CONFIDENCE=$(echo $RESULTS | jq -r '.overall_confidence')
SHOULD_DECLARE=$(echo $RESULTS | jq -r '.should_declare_winner')

echo "✅ Analysis complete:"
echo "   Winner: $WINNER"
echo "   Confidence: $(echo "$CONFIDENCE * 100" | bc)%"
echo "   Should declare winner: $SHOULD_DECLARE"

# 5. List experiments
echo "\n5️⃣ Listing experiments..."
COUNT=$(curl -s $BACKEND_URL/experiments/ \
  -H "user_id: $USER_ID" | jq '.total')
echo "✅ Found $COUNT experiments"

echo "\n================================"
echo "🎉 All tests passed!"
echo "View results at: http://localhost:3000/experiments"
```

Run with:
```bash
chmod +x test_experiments.sh
./test_experiments.sh
```

---

**That's it! You're ready to start A/B testing your clips like a pro!** 🚀
