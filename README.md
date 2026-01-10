# AI Brand Tracker

Track your brand's visibility across AI platforms — **Zero API keys required from users!** This Actor uses browser automation to query ChatGPT, Gemini, and Perplexity directly, just like a real user would. All platforms are queried in parallel for fast results.

## 🆕 What's New in v2.0

- 🆓 **No API Keys Needed** — Users don't need to provide any API keys!
- 🌐 **Browser Automation** — Uses Playwright to interact with AI platforms like a real user
- ⚡ **Parallel Execution** — All platforms are queried simultaneously (not sequentially)
- 🔄 **Replaced Claude with Perplexity** — Claude requires login, Perplexity doesn't

## Main Features

- 🤖 **Multi-Platform Analysis** — Queries ChatGPT, Gemini, and Perplexity simultaneously
- 🎯 **Template-Based Prompts** — 5 pre-built prompt templates covering recommendations, comparisons, pricing, use-cases, and reviews
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

Choose which AI platforms to query:

```json
{
  "platforms": ["chatgpt", "gemini", "perplexity"]
}
```

**That's it!** No API keys needed. The Actor handles everything.

**Step 3: The Actor Queries All Platforms in Parallel**

The Actor opens browser windows for each platform simultaneously and queries them like a real user would.

**Step 4: Responses are Analyzed**

The Actor extracts from each response:

- Brand mentions (with count, rank, and context)
- Whether brands are explicitly recommended
- URLs/citations included in responses
- Winner/loser determination per prompt

**Step 5: You Receive Comprehensive Results**

The final output includes detailed prompt-by-prompt results, brand summaries, competitive leaderboards, and run metadata.

---

## 📥 Input Parameters

| Parameter            | Type    | Required | Description                                      | Default |
| -------------------- | ------- | -------- | ------------------------------------------------ | ------- |
| `category`           | String  | ✅ Yes   | Industry/niche to analyze (e.g., "CRM software") | —       |
| `yourBrand`          | String  | ✅ Yes   | Your brand name to track                         | —       |
| `competitors`        | Array   | No       | Competitor brands to compare against (max 10)    | `[]`    |
| `platforms`          | Array   | ✅ Yes   | AI platforms: `chatgpt`, `gemini`, `perplexity`  | —       |
| `promptCount`        | Integer | No       | Number of template prompts to use (1-5)          | `1`     |
| `customPrompts`      | Array   | No       | Your own prompts to use instead of templates     | `[]`    |
| `proxyConfiguration` | Object  | No       | Apify Proxy settings (recommended)               | Enabled |

### Example: Minimum Required Input

```json
{
  "category": "CRM software",
  "yourBrand": "Salesforce",
  "platforms": ["chatgpt"]
}
```

### Example: Full Configuration

```json
{
  "category": "Email marketing platforms",
  "yourBrand": "Mailchimp",
  "competitors": ["Klaviyo", "ConvertKit", "Brevo"],
  "platforms": ["chatgpt", "gemini", "perplexity"],
  "promptCount": 5
}
```

### Example: Custom Prompts

```json
{
  "category": "Email marketing platforms",
  "yourBrand": "Mailchimp",
  "competitors": ["Klaviyo", "ConvertKit"],
  "platforms": ["chatgpt", "perplexity"],
  "customPrompts": [
    "What's the best email marketing tool for e-commerce?",
    "Which email platform has the best automation features?",
    "Compare Mailchimp vs Klaviyo for small businesses"
  ]
}
```

---

## 📤 Output Format

Results are stored in the Apify Dataset. You can download as JSON, CSV, or Excel.

### 1. `prompt_result` (One per prompt × platform)

```json
{
  "type": "prompt_result",
  "promptId": "chatgpt_prompt_001",
  "promptText": "What are the best CRM tools for startups?",
  "platform": "chatgpt",
  "platformModel": "gpt-4o-mini (free)",
  "rawResponse": "For startups looking for CRM solutions...",
  "mentions": [
    {
      "brand": "HubSpot",
      "count": 3,
      "rank": 1,
      "context": "HubSpot offers a generous free tier...",
      "isRecommended": true
    }
  ],
  "citations": ["https://www.g2.com/categories/crm"],
  "promptWinner": "HubSpot",
  "yourBrandMentioned": true,
  "yourBrandRank": 2
}
```

### 2. `brand_summary` (One per brand)

Aggregated metrics for each tracked brand.

### 3. `leaderboard` (One per run)

Overall rankings across all brands.

### 4. `run_summary` (One per run)

Run metadata and execution details.

---

## 🎯 Use Cases

### Marketing Teams

- **Monitor Brand Visibility** — Track how often AI mentions your brand
- **Competitive Intelligence** — Discover which competitors dominate AI recommendations
- **Identify Content Gaps** — Find prompts where your brand is missing

### SEO & GEO Specialists

- **AI Search Optimization** — Understand how AI platforms perceive your brand
- **Citation Discovery** — Find which sources AI platforms cite
- **Platform-Specific Strategies** — Tailor content for different AI platforms

### Brand Managers

- **Brand Perception Analysis** — See how AI describes your brand
- **Competitive Positioning** — Track visibility vs competitors
- **Cross-Platform Insights** — Compare brand strength across AI platforms

---

## 💰 Pricing

This Actor uses **Pay-Per-Event** pricing.

| Event             | Price |
| ----------------- | ----- |
| `prompt-analyzed` | $0.02 |

---

## ❓ FAQ

**Q: Do I need any API keys?**

No! The Actor uses browser automation to query AI platforms and has built-in analysis. You don't need to provide any API keys.

**Q: How does it work without API keys?**

The Actor opens real browser windows (using Playwright) and interacts with AI platforms exactly like a human user would — typing queries, waiting for responses, and extracting the text.

**Q: Why was Claude replaced with Perplexity?**

Claude's web interface requires login/authentication, making it impossible to automate. Perplexity allows queries without login.

**Q: How fast is it?**

All platforms are queried in parallel, so querying 3 platforms takes about the same time as querying 1.

---

## 🧩 Known Limitations

| Limitation             | Details                                        |
| ---------------------- | ---------------------------------------------- |
| Maximum 5 prompts      | Template or custom prompts capped at 5 per run |
| Maximum 10 competitors | Up to 10 competitor brands can be tracked      |
| Rate limits            | AI platforms may limit queries                 |

---

## 📝 Changelog

### v2.0.0 (2025-01-10)

**Browser Automation** 🌐

- Replaced API-based querying with browser automation (Playwright)
- No API keys needed from users!
- Parallel platform execution (ChatGPT, Gemini, Perplexity queried simultaneously)
- Replaced Claude with Perplexity (Claude requires login)
- Added stealth patches to avoid bot detection

### v1.1.0 (2025-01-09)

**Simplified Prompts** 📝

- Replaced LLM-powered prompt generation with 5 pre-built templates
- Reduced maximum prompts from 15 to 5

### v1.0.0 (2025-01-08)

**Initial Release** 🚀

- Multi-platform AI querying
- Brand mention extraction
- Visibility scores and leaderboards
