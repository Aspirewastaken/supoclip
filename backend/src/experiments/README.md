# A/B Testing System for SupoClip

## Overview

SupoClip's A/B testing system allows users to scientifically compare different clip variations (e.g., different fonts, cuts, transitions) and determine which performs best based on statistical significance.

## Architecture

### Components

1. **Database Tables** (`init.sql`)
   - `experiments`: Stores experiment metadata
   - `experiment_results`: Tracks metrics for each variation

2. **Statistical Engine** (`ab_testing.py`)
   - Chi-square tests for proportion metrics (CTR, conversion rate, engagement)
   - Welch's t-tests for continuous metrics (watch time, completion rate)
   - Bayesian probability calculations
   - Sample size and power analysis

3. **API Endpoints** (`api/routes/experiments.py`)
   - `POST /experiments/create` - Create new experiment
   - `GET /experiments/` - List all experiments
   - `GET /experiments/{id}` - Get experiment details
   - `GET /experiments/{id}/results` - Get statistical analysis
   - `POST /experiments/{id}/declare-winner` - Manually declare winner
   - `POST /experiments/{id}/update-metrics` - Update variation metrics
   - `POST /experiments/{id}/pause` - Pause experiment
   - `POST /experiments/{id}/resume` - Resume experiment

4. **Frontend UI** (`frontend/src/app/experiments/page.tsx`)
   - Experiment creation wizard
   - Real-time results dashboard
   - Statistical significance visualization
   - Winner declaration interface

## Statistical Methods

### 1. Chi-Square Test for Proportions

**Used for:** Click-through rate (CTR), conversion rate, engagement rate

**Null Hypothesis (H0):** No difference between variations
**Alternative Hypothesis (H1):** Significant difference exists

**Formula:**
```
χ² = Σ((Observed - Expected)² / Expected)
```

**Decision Rule:**
- If p-value < 0.05 (significance level): Reject H0, declare significant difference
- If p-value ≥ 0.05: Fail to reject H0, no significant difference

**Example:**
```
Variation A: 150 clicks / 1000 views = 15% CTR
Variation B: 180 clicks / 1000 views = 18% CTR

Chi-square test determines if 18% vs 15% is statistically significant
or could be due to random chance.
```

### 2. Welch's T-Test for Continuous Metrics

**Used for:** Average watch time, watch completion rate

**Why Welch's T-Test?**
- Doesn't assume equal variances between groups
- More robust than Student's t-test for real-world data

**Formula:**
```
t = (mean_A - mean_B) / sqrt(variance_A/n_A + variance_B/n_B)

df = (s_A²/n_A + s_B²/n_B)² / ((s_A²/n_A)²/(n_A-1) + (s_B²/n_B)²/(n_B-1))
```

**Example:**
```
Variation A: Avg watch time = 12.5s (n=1000)
Variation B: Avg watch time = 14.2s (n=1000)

T-test determines if 14.2s vs 12.5s is statistically significant.
```

### 3. Bayesian Probability

**Purpose:** Calculate probability that each variation is the best

**Method:** Monte Carlo simulation with Beta distribution
- For each variation, model success rate as Beta(successes + 1, failures + 1)
- Run 10,000 simulations
- Count how often each variation wins
- Probability = wins / total_simulations

**Example:**
```
Variation A: 150/1000 conversions
Variation B: 180/1000 conversions

Bayesian analysis might show:
- A has 25% probability of being best
- B has 75% probability of being best
```

### 4. Sample Size Calculation

**Purpose:** Determine how many views are needed to detect a meaningful difference

**Formula:**
```
n = (Z_α√(2p̄(1-p̄)) + Z_β√(p₁(1-p₁) + p₂(1-p₂)))² / (p₁ - p₂)²

Where:
- Z_α = 1.96 (for 95% confidence, two-tailed)
- Z_β = 0.84 (for 80% power)
- p̄ = (p₁ + p₂) / 2 (pooled proportion)
- p₁ = baseline rate
- p₂ = expected rate after improvement
```

**Example:**
```
Baseline CTR: 10%
Minimum Detectable Effect: 20% (i.e., 12% CTR)
Power: 80%
Significance: 5%

Required sample size: ~2,345 views per variation
```

## Workflow

### 1. Create Experiment

```bash
POST /experiments/create
{
  "name": "Font Style Test",
  "description": "Testing TikTok Sans vs Arial Bold",
  "variations": [
    {"clip_id": "clip-uuid-1", "variation_name": "TikTok Sans"},
    {"clip_id": "clip-uuid-2", "variation_name": "Arial Bold"}
  ],
  "confidence_threshold": 0.95
}
```

### 2. Collect Data

Users distribute traffic between variations and record metrics:
- Views (required for statistical power)
- Clicks
- Conversions
- Likes, comments, shares
- Watch time
- Completion rate

### 3. Update Metrics

```bash
POST /experiments/{id}/update-metrics
{
  "variation_id": "clip-uuid-1",
  "metrics": {
    "views": 1000,
    "clicks": 150,
    "conversions": 75,
    "likes": 200,
    "shares": 50,
    "avg_watch_time": 12.5,
    "watch_completion_rate": 0.85
  }
}
```

### 4. Analyze Results

```bash
GET /experiments/{id}/results
```

Returns:
- Variation metrics
- Statistical test results (chi-square, t-test)
- Bayesian probabilities
- Overall winner recommendation
- Confidence level
- Sample size adequacy

### 5. Declare Winner

**Automatic:** System auto-declares winner when:
- Minimum sample size reached (100+ views per variation)
- Overall confidence ≥ threshold (default 95%)
- Winner is significant in ≥2 metrics
- Status is "running"

**Manual:** User can manually declare winner:
```bash
POST /experiments/{id}/declare-winner
{
  "winner_variation_id": "clip-uuid-2"
}
```

## Confidence Levels

### 90% Confidence (p < 0.10)
- **Less strict**
- Faster decisions
- Higher risk of false positives (10% chance)
- Good for: Quick tests, low-risk decisions

### 95% Confidence (p < 0.05) - RECOMMENDED
- **Industry standard**
- Balanced approach
- 5% chance of false positive
- Good for: Most A/B tests

### 99% Confidence (p < 0.01)
- **Very strict**
- Requires more data
- Only 1% chance of false positive
- Good for: Critical decisions, large investments

## Key Metrics Explained

### Click-Through Rate (CTR)
```
CTR = (Clicks / Views) × 100%
```
Measures how compelling the clip is (drives action).

### Conversion Rate
```
Conversion Rate = (Conversions / Views) × 100%
```
Measures ultimate goal achievement (purchase, signup, etc.).

### Engagement Rate
```
Engagement Rate = ((Likes + Comments + Shares) / Views) × 100%
```
Measures audience interaction and interest.

### Watch Completion Rate
```
Completion Rate = (Average Watch Time / Clip Duration) × 100%
```
Measures content retention and quality.

## Best Practices

### 1. Run Experiments Long Enough
- **Minimum:** 100 views per variation
- **Recommended:** 1000+ views per variation
- **Avoid:** Stopping too early (leads to false positives)

### 2. Test One Variable at a Time
- ✅ Good: Test font style (TikTok Sans vs Arial)
- ❌ Bad: Test font + music + cuts all at once

### 3. Ensure Random Traffic Split
- Split traffic 50/50 (or evenly across variations)
- Don't bias traffic toward one variation
- Use random assignment

### 4. Consider External Factors
- Time of day
- Day of week
- Seasonal trends
- Platform algorithm changes

### 5. Use Appropriate Confidence Threshold
- Start with 95% (recommended)
- Only increase to 99% for critical decisions
- Avoid decreasing below 90%

### 6. Monitor Multiple Metrics
Don't rely on just one metric:
- ✅ Winner in CTR, conversion, AND engagement
- ❌ Winner in CTR only (might sacrifice other metrics)

## Example Use Cases

### 1. Font Style Testing
**Hypothesis:** Bold fonts increase engagement

**Variations:**
- A: TikTok Sans Regular
- B: Arial Bold
- C: Impact

**Primary Metric:** Engagement rate
**Secondary Metrics:** CTR, completion rate

### 2. Video Length Testing
**Hypothesis:** Shorter clips retain attention better

**Variations:**
- A: Full segment (45 seconds)
- B: Trimmed version (30 seconds)

**Primary Metric:** Watch completion rate
**Secondary Metrics:** Shares, likes

### 3. Hook Testing
**Hypothesis:** Question-based hooks drive more clicks

**Variations:**
- A: Statement hook ("This changed everything")
- B: Question hook ("Want to know the secret?")

**Primary Metric:** Click-through rate
**Secondary Metrics:** Watch time, conversions

### 4. Transition Effects Testing
**Hypothesis:** Smooth transitions reduce drop-off

**Variations:**
- A: No transitions
- B: Fade transitions
- C: Swipe transitions

**Primary Metric:** Watch completion rate
**Secondary Metrics:** Engagement rate

## Interpreting Results

### Scenario 1: Clear Winner
```
Variation A: 10% CTR, 5% conversion (p=0.001)
Variation B: 15% CTR, 8% conversion (p=0.001)

Result: B is significantly better (99.9% confidence)
Action: Declare B as winner, use for all future clips
```

### Scenario 2: No Significant Difference
```
Variation A: 12% CTR (p=0.45)
Variation B: 13% CTR (p=0.45)

Result: No statistical difference (55% confidence)
Action: Continue test or choose based on other factors
```

### Scenario 3: Insufficient Data
```
Variation A: 50 views, 10 clicks
Variation B: 50 views, 12 clicks

Result: Sample size too small
Action: Continue collecting data until minimum threshold
```

### Scenario 4: Mixed Results
```
Variation A: Higher CTR but lower conversion
Variation B: Lower CTR but higher conversion

Result: Trade-off between metrics
Action: Prioritize based on business goals
```

## Troubleshooting

### Problem: P-values always >0.05
**Causes:**
- Sample size too small
- Variations too similar
- High variance in data

**Solutions:**
- Collect more data
- Test more distinct variations
- Run test longer

### Problem: Different metrics give different winners
**Causes:**
- Trade-offs between metrics
- User segments behave differently

**Solutions:**
- Define primary metric before test
- Consider weighted scoring
- Segment analysis by user type

### Problem: Winner changes over time
**Causes:**
- Novelty effect
- External factors changed
- Algorithm changes

**Solutions:**
- Run test longer for stability
- Control for time-based factors
- Retest periodically

## API Response Examples

### Create Experiment Response
```json
{
  "experiment_id": "exp-550e8400-e29b-41d4-a716-446655440000",
  "message": "Experiment created successfully",
  "variations": [
    {
      "variation_id": "clip-uuid-1",
      "clip_id": "clip-uuid-1",
      "variation_name": "TikTok Sans"
    },
    {
      "variation_id": "clip-uuid-2",
      "clip_id": "clip-uuid-2",
      "variation_name": "Arial Bold"
    }
  ]
}
```

### Analysis Response
```json
{
  "experiment_id": "exp-550e8400-e29b-41d4-a716-446655440000",
  "experiment_name": "Font Style Test",
  "status": "running",
  "variations": [
    {
      "variation_id": "clip-uuid-1",
      "variation_name": "TikTok Sans",
      "metrics": {
        "views": 1000,
        "clicks": 150,
        "conversions": 75,
        "click_through_rate": 0.15,
        "conversion_rate": 0.075,
        "engagement_rate": 0.25
      }
    },
    {
      "variation_id": "clip-uuid-2",
      "variation_name": "Arial Bold",
      "metrics": {
        "views": 1000,
        "clicks": 180,
        "conversions": 95,
        "click_through_rate": 0.18,
        "conversion_rate": 0.095,
        "engagement_rate": 0.30
      }
    }
  ],
  "statistical_tests": [
    {
      "metric_name": "Click-Through Rate",
      "p_value": 0.023,
      "is_significant": true,
      "confidence_level": 0.977,
      "winner_variation_id": "clip-uuid-2",
      "winner_improvement": 20.0,
      "test_type": "chi_square",
      "message": "Click-Through Rate: A=15.00%, B=18.00%, p=0.0230, SIGNIFICANT"
    }
  ],
  "overall_winner": "clip-uuid-2",
  "overall_confidence": 0.96,
  "recommendation": "Declare clip-uuid-2 as winner (confidence: 96.0%)",
  "should_declare_winner": true,
  "min_sample_size_reached": true
}
```

## Mathematical Background

### Type I Error (False Positive)
- **Definition:** Declaring a winner when no real difference exists
- **Rate:** α (significance level, typically 0.05)
- **Example:** Claiming B is better when A and B are actually equal

### Type II Error (False Negative)
- **Definition:** Failing to detect a real difference
- **Rate:** β (typically 0.20 for 80% power)
- **Example:** Claiming no difference when B is actually better

### Statistical Power
```
Power = 1 - β = Probability of detecting real difference
```
- 80% power = 80% chance of finding real difference if it exists
- Higher power requires larger sample size

### Effect Size
```
Effect Size = (Rate_B - Rate_A) / Rate_A
```
- Small: 5-10% improvement
- Medium: 10-25% improvement
- Large: 25%+ improvement

Larger effect sizes are easier to detect (require less data).

## References

- **Chi-Square Test:** Pearson, K. (1900). "On the criterion that a given system of deviations..."
- **Welch's T-Test:** Welch, B. L. (1947). "The generalization of 'Student's' problem..."
- **Bayesian A/B Testing:** Chris Stucchio, VWO Blog
- **Sample Size:** "Statistical Power Analysis" by Jacob Cohen

## Support

For questions or issues:
- GitHub Issues: https://github.com/yourusername/supoclip/issues
- Documentation: https://supoclip.com/docs/ab-testing
- Email: support@supoclip.com
