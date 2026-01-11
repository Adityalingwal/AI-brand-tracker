# AI Brand Visibility

Track how AI platforms like ChatGPT, Gemini, and Perplexity recommend your brand versus competitors. Get instant visibility into which brands dominate AI-generated recommendations in your industry — perfect for marketing teams, SEO specialists, and brand managers optimizing for the AI search era.

## 🚀 Why Use AI Brand Visibility?

As AI-powered search becomes mainstream, understanding how ChatGPT, Gemini, and other AI platforms perceive your brand is critical. This Actor provides:

- **AI Visibility Monitoring** — See exactly how often AI platforms mention and recommend your brand
- **Competitive Intelligence** — Discover which competitors dominate AI recommendations in your space
- **Cross-Platform Insights** — Compare how different AI platforms (ChatGPT vs Gemini vs Perplexity) perceive your brand
- **Actionable Gap Analysis** — Identify specific queries where your brand is missing from AI recommendations
- **Plain English Summaries** — No complex metrics, just clear insights you can act on

---

## 🧭 How to Use

1. Enter your **brand name** and **industry category** (e.g., "CRM software")
2. Add **competitor brands** you want to compare against (optional)
3. Select which **AI platforms** to query (ChatGPT, Gemini, Perplexity)
4. Add your own **custom prompts**
5. Click **Run** and receive a comprehensive visibility report

---

## 📊 What You Get

For each brand tracked, you receive:

| Insight              | Description                                      |
| -------------------- | ------------------------------------------------ |
| **Mention Count**    | How many times the brand appears in AI responses |
| **Platform Ranking** | Which brands rank highest on each AI platform    |
| **Visibility Gaps**  | Specific prompts where your brand is missing     |
| **Context Analysis** | How AI describes and positions each brand        |

---

### Sample Input

```json
{
  "category": "CRM software",
  "myBrand": "Salesforce",
  "competitors": ["HubSpot", "Pipedrive"],
  "platforms": ["chatgpt", "gemini", "perplexity"],
  "prompts": [
    "What are the best CRM tools for small businesses?",
    "Compare enterprise CRM solutions",
    "Which CRM has the best automation features?"
  ]
}
```

---

## 📤 Output Example

Results are stored in the Apify Dataset. You can download them as JSON, CSV, or Excel.

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
        "summary": "Salesforce maintains strong enterprise positioning with 5 mentions across 2 of 3 prompts — ranking #2 behind HubSpot. Positioned as the sophisticated leader for complex enterprise needs, but absent from small business recommendations.",
        "promptsMentionSummary": "Strong in enterprise and automation queries. **Visibility gap**: Missing from small business recommendations dominated by HubSpot and Zoho."
      },
      "gemini": {
        "summary": "Commanding visibility with 7 mentions across all 3 prompts — ranking #1. Featured as the comprehensive enterprise solution with advanced AI capabilities.",
        "promptsMentionSummary": "Mentioned in all prompts with emphasis on customization depth and Einstein AI forecasting."
      },
      "perplexity": {
        "summary": "Selective but authoritative visibility with 5 mentions across 2 of 3 prompts — ranking #2. Positioned as enterprise-grade for complex operations.",
        "promptsMentionSummary": "Featured in enterprise and automation queries. Absent from small business recommendations."
      }
    }
  },

  "competitorBrandPerformance": {
    "HubSpot": {
      "platformPerformance": {
        "chatgpt": {
          "summary": "Dominates with 7 mentions across all prompts — #1 ranking. Featured as leading SMB recommendation and credible enterprise alternative.",
          "promptsMentionSummary": "Complete coverage with no visibility gaps. Dominant in small business and automation queries."
        },
        "gemini": {
          "summary": "5 mentions, #2 ranking. Positioned as accessible alternative with excellent ease-of-use."
        },
        "perplexity": {
          "summary": "6 mentions, #1 ranking. Go-to recommendation for feature-accessibility balance."
        }
      }
    },
    "Pipedrive": {
      "platformPerformance": {
        "chatgpt": {
          "summary": "3 mentions, #3 ranking. Affordable, pipeline-focused alternative for small teams."
        },
        "gemini": {
          "summary": "3 mentions, #3 ranking. Emphasized for visual pipelines and competitive pricing."
        },
        "perplexity": {
          "summary": "3 mentions, #3 ranking. Cost-effective, sales-focused option."
        }
      }
    }
  },

  "executionMetadata": {
    "startedAt": "2025-01-11T12:00:00Z",
    "completedAt": "2025-01-11T12:02:30Z",
    "durationMs": 150000,
    "totalResponses": 9,
    "platformsQueried": ["chatgpt", "gemini", "perplexity"]
  }
}
```

---

## 🎯 Use Cases

### Marketing Teams

- Monitor brand visibility in AI-generated recommendations
- Track competitive positioning across AI platforms
- Identify content gaps where competitors outrank you

### SEO & GEO Specialists

- Optimize content for AI search engines (Generative Engine Optimization)
- Understand how AI platforms source and cite information
- Develop platform-specific content strategies

### Brand Managers

- Analyze brand perception across AI platforms
- Benchmark against competitors
- Track visibility changes over time with scheduled runs

### Sales Intelligence

- Understand how prospects research your category via AI
- Identify which competitors appear in buying-intent queries
- Tailor sales messaging based on AI positioning

---

## 💰 Cost of Usage

This Actor uses Pay-Per-Event pricing. You pay a flat fee per complete analysis.

| Event            | Price | What You Get                                       |
| ---------------- | ----- | -------------------------------------------------- |
| `brand-analysis` | $0.10 | Complete analysis across all platforms and prompts |

**💡 Example:** Analyzing your brand across 3 AI platforms with 3 prompts costs $0.10 total.

### Tier Discounts

Apify subscription members get discounts:

| Plan           | Price per Analysis |
| -------------- | ------------------ |
| Free / Starter | $0.10              |
| Bronze         | $0.08 (20% off)    |
| Silver         | $0.06 (40% off)    |
| Gold           | $0.04 (60% off)    |

### Compute Costs (Paid Separately to Apify)

In addition to the analysis fee above, Apify charges for compute resources:

- **Memory**: 4 GB recommended
- **Typical run time**: 3-5 minutes
- **Estimated compute cost**: ~$0.05 per run

This compute cost is charged by Apify from your account.

---

## ❓ FAQ

**Q: How does it query AI platforms without API keys?**

The Actor uses browser automation to interact with AI platforms exactly like a human user would.

**Q: Which AI platforms are supported?**

Currently: ChatGPT, Gemini, and Perplexity.

**Q: How accurate is the brand detection?**

An AI analyzes each response to detect brand mentions, context, and positioning. Full responses are included so you can verify results.

**Q: Can I track visibility over time?**

Yes! Schedule recurring runs in Apify Console to track how your brand visibility changes week-over-week.

---

## 🧩 Known Limitations

| Limitation            | Details                                                       |
| --------------------- | ------------------------------------------------------------- |
| Rate limits           | AI platforms may throttle queries during high-traffic periods |
| Response variability  | AI responses can vary between runs for the same prompt        |
| Platform availability | Occasional downtime on AI platforms may affect results        |


---

## 📝 Changelog

### v1.0.0 (2025-01-11)

**Initial Release** 🚀

- Multi-platform brand visibility tracking (ChatGPT, Gemini, Perplexity)
- AI-powered brand mention detection with context analysis
- Competitive benchmarking across AI platforms
- Plain English summaries for actionable insights
- Custom prompt support
- Pay-per-event pricing ($0.10 per complete analysis)
