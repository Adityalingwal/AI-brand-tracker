# AI Brand Tracker

This Actor tracks your brand's visibility across AI platforms (ChatGPT, Claude, Gemini). Provide your brand name and industry category — the Actor generates realistic search queries, queries multiple AI platforms simultaneously, and analyzes which brands get mentioned, recommended, and cited. Know exactly where you stand against competitors in AI-powered search results.

## Main Features

- 🤖 **Multi-Platform Analysis** — Queries ChatGPT (GPT-4o), Claude (Sonnet 4), and Gemini (2.5 Flash) simultaneously
- 🎯 **Smart Prompt Generation** — AI generates diverse, realistic search queries for your category
- 📊 **Brand Mention Extraction** — Detects mentions with count, rank, context, and recommendation status
- 🔗 **Citation Discovery** — Identifies URLs cited in AI responses
- 🏆 **Competitive Leaderboards** — Compare visibility scores and citation share across all brands
- 📈 **Platform Breakdown** — See which AI platforms favor which brands

---

## How to Use

**Step 1: Provide Your Brand and Category**

Enter your brand name, industry category, and optionally competitors to compare against:

```json
{
  "category": "CRM software",
  "yourBrand": "Salesforce",
  "competitors": ["HubSpot", "Pipedrive", "Zoho"]
}
```

**Step 2: Select AI Platforms**

Choose which AI platforms to analyze (you must provide API keys for each):

```json
{
  "platforms": ["chatgpt", "claude", "gemini"]
}
```

**Step 3: The Actor Generates Search Prompts**

The Actor uses AI to generate diverse, realistic search queries that people might ask when researching your category — covering recommendations, comparisons, features, pricing, and use cases.

**Step 4: All Platforms are Queried in Parallel**

The Actor sends each prompt to all selected AI platforms simultaneously, collecting their responses efficiently.

**Step 5: Responses are Analyzed**

For each response, the Actor extracts:

- Brand mentions (with count, rank, and context)
- Whether brands are explicitly recommended
- URLs/citations included in responses
- Winner/loser determination per prompt

**Step 6: Metrics are Calculated**

Visibility scores, citation shares, and competitive rankings are computed for each brand across all platforms.

**Step 7: You Receive Comprehensive Results**

The final output includes detailed prompt-by-prompt results, brand summaries, competitive leaderboards, and run metadata.

---

## 📥 Input Parameters

| Parameter            | Type    | Required    | Description                                          | Default |
| -------------------- | ------- | ----------- | ---------------------------------------------------- | ------- |
| `category`           | String  | ✅ Yes      | Industry/niche to analyze (e.g., "CRM software")     | —       |
| `yourBrand`          | String  | ✅ Yes      | Your brand name to track                             | —       |
| `competitors`        | Array   | No          | Competitor brands to compare against (max 10)        | `[]`    |
| `platforms`          | Array   | ✅ Yes      | AI platforms to query: `chatgpt`, `claude`, `gemini` | —       |
| `promptCount`        | Integer | No          | Number of prompts to generate (1-15)                 | `5`     |
| `customPrompts`      | Array   | No          | Your own prompts to include (max 20)                 | `[]`    |
| `openaiApiKey`       | String  | Conditional | Required if using ChatGPT                            | —       |
| `anthropicApiKey`    | String  | Conditional | Required if using Claude                             | —       |
| `googleApiKey`       | String  | Conditional | Required if using Gemini                             | —       |
| `proxyConfiguration` | Object  | No          | Apify Proxy settings                                 | Enabled |

### Example: Minimum Required Input

```json
{
  "category": "CRM software",
  "yourBrand": "Salesforce",
  "platforms": ["chatgpt"],
  "openaiApiKey": "sk-..."
}
```

### Example: Full Configuration

```json
{
  "category": "Email marketing platforms",
  "yourBrand": "Mailchimp",
  "competitors": ["Klaviyo", "ConvertKit", "Brevo", "ActiveCampaign"],
  "platforms": ["chatgpt", "claude", "gemini"],
  "promptCount": 10,
  "customPrompts": [
    "What's the best email marketing tool for e-commerce?",
    "Which email platform has the best automation features?"
  ],
  "openaiApiKey": "sk-...",
  "anthropicApiKey": "sk-ant-...",
  "googleApiKey": "AIza..."
}
```

---

## 📤 Output Format

Results are stored in the Apify Dataset. You can download as JSON, CSV, or Excel.

### 1. `prompt_result` (One per prompt × platform)

Raw data for each prompt and platform combination.

```json
{
  "type": "prompt_result",
  "promptId": "chatgpt_prompt_001",
  "promptText": "What are the best CRM tools for startups?",
  "platform": "chatgpt",
  "platformModel": "gpt-4o",
  "rawResponse": "For startups looking for CRM solutions, here are some top recommendations...",
  "mentions": [
    {
      "brand": "HubSpot",
      "count": 3,
      "rank": 1,
      "context": "HubSpot offers a generous free tier that's perfect for startups...",
      "isRecommended": true
    },
    {
      "brand": "Salesforce",
      "count": 2,
      "rank": 2,
      "context": "Salesforce is a powerful option for startups planning to scale...",
      "isRecommended": true
    }
  ],
  "citations": ["https://www.g2.com/categories/crm"],
  "promptWinner": "HubSpot",
  "promptLoser": "Pipedrive",
  "yourBrandMentioned": true,
  "yourBrandRank": 2,
  "competitorsMentioned": ["HubSpot", "Pipedrive"],
  "competitorsMissed": ["Zoho"]
}
```

### 2. `brand_summary` (One per brand)

Aggregated metrics for each tracked brand.

```json
{
  "type": "brand_summary",
  "brand": "Salesforce",
  "overallMetrics": {
    "visibilityScore": 72.5,
    "citationShare": 28.5,
    "totalMentions": 47,
    "totalPromptsAnalyzed": 20,
    "promptsWithMention": 15,
    "promptsMissed": 5
  },
  "platformBreakdown": {
    "chatgpt": {
      "visibilityScore": 80.0,
      "citationShare": 32.0,
      "mentions": 18,
      "promptsWithMention": 8
    },
    "claude": {
      "visibilityScore": 70.0,
      "citationShare": 25.0,
      "mentions": 14,
      "promptsWithMention": 7
    },
    "gemini": {
      "visibilityScore": 67.5,
      "citationShare": 28.5,
      "mentions": 15,
      "promptsWithMention": 5
    }
  },
  "competitivePosition": {
    "rank": 2,
    "totalBrands": 4,
    "promptsWon": 5,
    "promptsLost": 3,
    "promptsTied": 7
  },
  "topContexts": [
    "Salesforce is a powerful option for startups planning to scale...",
    "For enterprise features, Salesforce leads the market...",
    "Salesforce offers robust customization options..."
  ]
}
```

### 3. `leaderboard` (One per run)

Overall rankings across all brands.

```json
{
  "type": "leaderboard",
  "rankings": [
    {
      "rank": 1,
      "brand": "HubSpot",
      "visibilityScore": 85.0,
      "citationShare": 35.2,
      "totalMentions": 58,
      "promptsWon": 12
    },
    {
      "rank": 2,
      "brand": "Salesforce",
      "visibilityScore": 72.5,
      "citationShare": 28.5,
      "totalMentions": 47,
      "promptsWon": 5
    },
    {
      "rank": 3,
      "brand": "Pipedrive",
      "visibilityScore": 55.0,
      "citationShare": 20.3,
      "totalMentions": 32,
      "promptsWon": 2
    }
  ],
  "platformLeaderboards": {
    "chatgpt": [
      { "rank": 1, "brand": "HubSpot", "citationShare": 38.5, "mentions": 22 },
      {
        "rank": 2,
        "brand": "Salesforce",
        "citationShare": 32.0,
        "mentions": 18
      }
    ],
    "claude": [
      { "rank": 1, "brand": "HubSpot", "citationShare": 33.0, "mentions": 19 },
      {
        "rank": 2,
        "brand": "Salesforce",
        "citationShare": 25.0,
        "mentions": 14
      }
    ]
  }
}
```

### 4. `run_summary` (One per run)

Run metadata, execution details, and billing information.

```json
{
  "type": "run_summary",
  "status": "completed",
  "input": {
    "category": "CRM software",
    "yourBrand": "Salesforce",
    "competitors": ["HubSpot", "Pipedrive", "Zoho"],
    "platforms": ["chatgpt", "claude"],
    "promptCount": 10
  },
  "execution": {
    "startedAt": "2025-01-08T10:30:00.000Z",
    "completedAt": "2025-01-08T10:31:45.000Z",
    "durationMs": 105000,
    "promptsProcessed": 10,
    "responsesCollected": 20
  },
  "billing": {
    "eventType": "prompt_analyzed",
    "eventsCharged": 20,
    "pricePerEvent": 0.02
  }
}
```

### 5. `error_summary` (If errors occurred)

Transparency report of any issues during the run.

```json
{
  "type": "error_summary",
  "totalErrors": 2,
  "totalWarnings": 1,
  "hasFatalErrors": false,
  "errors": [
    {
      "errorType": "query_failed",
      "message": "Rate limit exceeded",
      "context": "chatgpt:prompt_008",
      "recoverable": true
    }
  ],
  "warnings": ["LLM extraction fallback used for 1 response"]
}
```

---

## 🎯 Use Cases

### Marketing Teams

- **Monitor Brand Visibility** — Track how often AI mentions your brand when users search your category
- **Competitive Intelligence** — Discover which competitors dominate AI recommendations
- **Identify Content Gaps** — Find prompts where your brand is missing but competitors appear

### SEO & GEO Specialists

- **AI Search Optimization** — Understand how AI platforms perceive and rank your brand
- **Citation Discovery** — Find which sources AI platforms cite (potential link targets)
- **Platform-Specific Strategies** — Tailor content for ChatGPT vs Claude vs Gemini

### Brand Managers

- **Brand Perception Analysis** — See how AI describes your brand in context
- **Competitive Positioning** — Track visibility trends vs competitors
- **Cross-Platform Insights** — Compare brand strength across different AI platforms

### Research & Analytics Teams

- **Market Landscape Analysis** — Map brand visibility across an entire industry
- **Trend Tracking** — Run periodic checks to track visibility changes over time
- **Recommendation Mapping** — Understand which brands AI recommends for specific use cases

---

## 💰 Pricing

This Actor uses **Pay-Per-Event** pricing. You are not charged for Apify platform usage, only a fixed price per analyzed prompt.

| Event             | Price (Free Tier) | Price (Gold Tier) |
| ----------------- | ----------------- | ----------------- |
| `prompt-analyzed` | $0.02             | $0.012            |

---

## ❓ FAQ

**Q: What categories work best?**

This Actor works best for product/service categories where multiple brands compete — SaaS tools, software platforms, consumer products, professional services, etc.

**Q: How accurate are the visibility scores?**

Visibility scores reflect how often AI mentions your brand across diverse prompts. For more accurate results, use higher prompt counts and test across multiple AI platforms.

**Q: Why do different platforms give different results?**

Each AI platform has different training data, recommendation logic, and update frequencies. This is valuable insight — it shows where you're strong and where you need to improve.

**Q: Can I use custom prompts only?**

Yes! Set `promptCount` to 0 and provide your own prompts in `customPrompts`. This is useful for testing specific scenarios.

**Q: How often should I run this?**

For ongoing monitoring, weekly or bi-weekly runs are recommended. AI platform responses can change as they update their models and training data.

---

## 🧩 Known Limitations

| Limitation             | Details                                                      |
| ---------------------- | ------------------------------------------------------------ |
| Maximum 15 prompts     | Auto-generated prompts capped at 15 per run                  |
| Maximum 10 competitors | Up to 10 competitor brands can be tracked simultaneously     |
| API rate limits        | High prompt counts may trigger rate limiting on AI platforms |
| API key required       | At least one platform API key must be provided               |

---

## 💬 Questions or Issues?

If you encounter problems or have feature requests, please open an issue on the Issues tab of the Actor's page in the Apify Store.

---

## 📝 Changelog

### v1.0.0 (2025-01-08)

**Initial Release** 🚀

**Core Capabilities:**

- Multi-platform AI querying (ChatGPT, Claude, Gemini)
- LLM-powered prompt generation
- Brand mention extraction with count, rank, and context
- Citation/URL extraction from AI responses
- Visibility score and citation share calculation
- Competitive leaderboards (overall and per-platform)

**Performance:**

- Parallel platform querying for faster execution
- Batch processing with rate limit awareness
- Optimized LLM calls (1 analysis call per platform)

**Reliability:**

- Comprehensive error tracking and recovery
- Exponential backoff on API failures
- Graceful fallback for prompt generation and extraction
- Detailed error summaries in output

**Developer Experience:**

- Pay-Per-Event pricing model
- Structured dataset output with multiple record types
- Full input validation with helpful error messages
- Progress tracking and execution logging
