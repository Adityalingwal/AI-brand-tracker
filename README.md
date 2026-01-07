# AI Brand Tracker

Track your brand's visibility across AI platforms (ChatGPT, Claude, Gemini). Analyze how often AI assistants mention your brand, compare against competitors, and discover citation opportunities.

## What It Does

When users ask AI assistants questions like "What's the best CRM software?", some brands get mentioned while others don't. This actor helps you understand:

- **Is your brand visible?** - How often does AI mention you when users ask about your category?
- **Who's winning?** - Which competitors get mentioned more often?
- **What context?** - How is your brand described when mentioned?
- **Where to improve?** - Which prompts miss your brand entirely?

## Features

- **Multi-Platform Analysis** - Query ChatGPT, Claude, and Gemini simultaneously
- **Auto-Generated Prompts** - AI generates diverse, realistic search queries for your category
- **Brand Mention Extraction** - Detects mentions with count, rank, and context
- **Citation Discovery** - Identifies URLs cited in AI responses
- **Competitive Analysis** - Compare visibility scores across brands
- **Platform Breakdown** - See which AI platforms favor which brands

## Input

| Field             | Required    | Description                                         |
| ----------------- | ----------- | --------------------------------------------------- |
| `category`        | Yes         | Industry/niche (e.g., "CRM software")               |
| `yourBrand`       | Yes         | Your brand name to track                            |
| `competitors`     | No          | Competitor brands to compare (max 10)               |
| `platforms`       | Yes         | AI platforms to query (min 1)                       |
| `promptCount`     | No          | Number of prompts to generate (default: 5, max: 15) |
| `customPrompts`   | No          | Your own prompts to include                         |
| `openaiApiKey`    | Conditional | Required for ChatGPT                                |
| `anthropicApiKey` | Conditional | Required for Claude                                 |
| `googleApiKey`    | Conditional | Required for Gemini                                 |

### Example Input

```json
{
  "category": "CRM software",
  "yourBrand": "Salesforce",
  "competitors": ["HubSpot", "Pipedrive", "Zoho"],
  "platforms": ["chatgpt", "claude"],
  "promptCount": 10,
  "openaiApiKey": "sk-...",
  "anthropicApiKey": "sk-ant-..."
}
```

## Output

The actor produces 4 types of records in the dataset:

### 1. `prompt_result` (One per prompt per platform)

Raw data for each prompt/platform combination.

```json
{
  "type": "prompt_result",
  "promptId": "prompt_001",
  "promptText": "What are the best CRM tools for startups?",
  "platform": "chatgpt",
  "platformModel": "gpt-4o",
  "rawResponse": "For startups...",
  "mentions": [
    {
      "brand": "HubSpot",
      "count": 3,
      "rank": 1,
      "context": "HubSpot offers a free tier...",
      "isRecommended": true
    }
  ],
  "citations": ["https://g2.com/..."],
  "promptWinner": "HubSpot",
  "yourBrandMentioned": true,
  "yourBrandRank": 2
}
```

### 2. `brand_summary` (One per brand)

Aggregated metrics for each tracked brand.

```json
{
  "type": "brand_summary",
  "brand": "Salesforce",
  "overallMetrics": {
    "visibilityScore": 72,
    "citationShare": 28.5,
    "totalMentions": 47,
    "promptsWithMention": 15,
    "promptsMissed": 5
  },
  "platformBreakdown": {
    "chatgpt": { "visibilityScore": 80, "citationShare": 32 },
    "claude": { "visibilityScore": 70, "citationShare": 25 }
  }
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
      "visibilityScore": 85,
      "citationShare": 35.2
    },
    {
      "rank": 2,
      "brand": "Salesforce",
      "visibilityScore": 72,
      "citationShare": 28.5
    }
  ]
}
```

### 4. `run_summary` (One per run)

Run metadata and billing information.

```json
{
  "type": "run_summary",
  "status": "completed",
  "execution": {
    "promptsProcessed": 10,
    "responsesCollected": 20
  },
  "billing": {
    "eventsCharged": 20,
    "pricePerEvent": 0.02
  }
}
```

## Pricing

This actor uses **Pay-Per-Event** pricing:

| Event             | Price                         |
| ----------------- | ----------------------------- |
| `prompt-analyzed` | $0.02 per prompt per platform |

**Example costs:**

- 5 prompts × 2 platforms = 10 events = $0.20
- 10 prompts × 3 platforms = 30 events = $0.60

Note: You also pay for the AI API calls directly to OpenAI, Anthropic, or Google.

## Use Cases

### Marketing Teams

- Monitor brand visibility in AI search
- Track competitor presence
- Identify content gaps

### SEO/GEO Specialists

- Discover which sources AI cites
- Find citation opportunities
- Optimize for AI visibility

### Brand Managers

- Understand brand perception in AI responses
- Track visibility trends over time
- Compare across different AI platforms

## API Keys

You need API keys for the platforms you want to query:

| Platform | Get API Key From                                                     |
| -------- | -------------------------------------------------------------------- |
| ChatGPT  | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Claude   | [console.anthropic.com](https://console.anthropic.com)               |
| Gemini   | [aistudio.google.com/apikey](https://aistudio.google.com/apikey)     |

## Limitations

- Maximum 15 prompts per run
- Maximum 10 competitors
- Requires at least one AI platform API key
- API rate limits may slow down large runs

## Support

If you encounter issues or have feature requests, please open an issue on the Actor's page in the Apify Store.

---

Built for the Apify 1M Challenge

# AI-brand-tracker
