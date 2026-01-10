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
  "myBrand": "Salesforce",
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
| `myBrand`          | String  | ✅ Yes   | Your brand name to track                         | —       |
| `competitors`        | Array   | No       | Competitor brands to compare against (max 10)    | `[]`    |
| `platforms`          | Array   | ✅ Yes   | AI platforms: `chatgpt`, `gemini`, `perplexity`  | —       |
| `promptCount`        | Integer | No       | Number of template prompts to use (1-5)          | `1`     |
| `customPrompts`      | Array   | No       | Your own prompts to use instead of templates     | `[]`    |
| `proxyConfiguration` | Object  | No       | Apify Proxy settings (recommended)               | Enabled |

### Example: Minimum Required Input

```json
{
  "category": "CRM software",
  "myBrand": "Salesforce",
  "platforms": ["chatgpt"]
}
```

### Example: Full Configuration

```json
{
  "category": "Email marketing platforms",
  "myBrand": "Mailchimp",
  "competitors": ["Klaviyo", "ConvertKit", "Brevo"],
  "platforms": ["chatgpt", "gemini", "perplexity"],
  "promptCount": 5
}
```

### Example: Custom Prompts

```json
{
  "category": "Email marketing platforms",
  "myBrand": "Mailchimp",
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

Results are stored in the Apify Dataset as a **single consolidated JSON object**. You can download as JSON, CSV, or Excel.

### Output Structure

The output contains everything in one clean, organized structure:

```json
{
  "summary": {
    "category": "CRM software",
    "myBrand": "Salesforce",
    "competitors": ["HubSpot", "Pipedrive"]
  },

  "myBrandPerformance": {
    "brand": "Salesforce",
    "platformPerformance": {
      "chatgpt": {
        "summary": "Mentioned 5 times across 2 out of 3 prompts. Ranked #2 on this platform (HubSpot ranked #1).",
        "promptsMentionSummary": "Mentioned in Prompt #1 and Prompt #3. Missing from Prompt #2."
      },
      "gemini": {
        "summary": "Mentioned 7 times across 3 out of 3 prompts. Ranked #1 on this platform.",
        "promptsMentionSummary": "Mentioned in all prompts."
      }
    }
  },

  "competitorBrandPerformance": {
    "HubSpot": {
      "platformPerformance": {
        "chatgpt": {
          "summary": "Mentioned 8 times across 3 out of 3 prompts. Ranked #1 on this platform.",
          "promptsMentionSummary": "Mentioned in all prompts."
        }
      }
    }
  },

  "promptResults": [
    {
      "platform": "chatgpt",
      "prompts": [
        {
          "promptText": "What are the best CRM tools?",
          "response": "The top CRM tools include Salesforce, HubSpot...",
          "allBrandsMentioned": ["Salesforce", "HubSpot", "Zoho"]
        }
      ]
    }
  ],

  "executionMetadata": {
    "startedAt": "2025-01-10T12:00:00Z",
    "completedAt": "2025-01-10T12:05:30Z",
    "durationMs": 330000,
    "totalResponses": 9,
    "platformsQueried": ["chatgpt", "gemini", "perplexity"]
  }
}
```

### Key Features

- **Single Output**: One consolidated record per run (no more 14+ scattered records)
- **Plain English Summaries**: No complex metrics like "visibilityScore: 75.5%" — just clear summaries
- **Platform-Focused**: See how each brand performs on each AI platform
- **Actionable Insights**: Know exactly which prompts missed your brand
- **Complete Transparency**: Full AI responses included for verification

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

### v2.1.0 (2025-01-10)

**Simplified Output Structure** 📊

- **Single consolidated output** instead of 14+ separate records
- **Plain English summaries** instead of technical metrics (visibilityScore, citationShare)
- **Platform-focused analysis** with per-platform brand performance
- **Single LLM call** for analysis (reduced from 10+ calls)
- **Cleaner dataset** - one JSON object per run

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
