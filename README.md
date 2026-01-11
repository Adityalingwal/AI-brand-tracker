# AI Brand Tracker

Track how AI platforms like ChatGPT, Gemini, and Perplexity recommend your brand versus competitors. Get instant visibility into which brands dominate AI-generated recommendations in your industry — perfect for marketing teams, SEO specialists, and brand managers optimizing for the AI search era.

## 🚀 Why Use AI Brand Tracker?

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

| Insight               | Description                                      |
| --------------------- | ------------------------------------------------ |
| **Mention Count**     | How many times the brand appears in AI responses |
| **Platform Ranking**  | Which brands rank highest on each AI platform    |
| **Visibility Gaps**   | Specific prompts where your brand is missing     |
| **Context Analysis**  | How AI describes and positions each brand        |
| **Full AI Responses** | Complete responses for verification and analysis |

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
        "summary": "Salesforce maintains strong enterprise positioning on ChatGPT with 5 mentions across 2 of 3 prompts — ranking #2 behind HubSpot's dominant 7 mentions. The platform consistently positions Salesforce as the sophisticated, full-featured leader for complex enterprise needs, but notably absent from small business recommendations where affordability-focused alternatives dominate.",
        "promptsMentionSummary": "Strong presence in enterprise comparison and automation feature queries where Salesforce is positioned as the industry leader. **Critical visibility gap**: Completely absent from small business CRM recommendations — a high-volume search dominated by HubSpot, Zoho, and Pipedrive."
      },
      "gemini": {
        "summary": "Salesforce achieves commanding visibility on Gemini with 7 mentions across all 3 prompts — ranking #1 ahead of HubSpot (5 mentions) and Pipedrive (3 mentions). Gemini consistently features Salesforce as the comprehensive enterprise solution with advanced AI capabilities through Einstein.",
        "promptsMentionSummary": "Mentioned in all prompts with particularly strong positioning in automation and enterprise comparison queries. Gemini emphasizes Salesforce's customization depth, AppExchange ecosystem, and AI-powered forecasting as key differentiators."
      },
      "perplexity": {
        "summary": "Salesforce maintains selective but authoritative visibility on Perplexity, appearing in 2 of 3 prompts with 5 total mentions — ranking #2 overall behind HubSpot's 6 mentions. Perplexity positions Salesforce as the enterprise-grade solution for complex, large-scale operations requiring advanced customization.",
        "promptsMentionSummary": "Featured prominently in enterprise comparison and automation queries. **Visibility gap**: Absent from small business recommendations where Perplexity prioritizes affordability-focused alternatives like Zoho and Freshsales."
      }
    }
  },

  "competitorBrandPerformance": {
    "HubSpot": {
      "platformPerformance": {
        "chatgpt": {
          "summary": "HubSpot dominates ChatGPT with commanding visibility across all 3 queries and 7 total mentions — establishing clear #1 ranking ahead of Salesforce (5 mentions) and Pipedrive (3 mentions). ChatGPT consistently features HubSpot as the leading recommendation for small businesses and as a credible enterprise alternative.",
          "promptsMentionSummary": "Complete coverage across all query types with no visibility gaps. Particularly dominant in small business recommendations (featured first and prominently) and automation features (praised for intuitive workflows and free tier)."
        },
        "gemini": {
          "summary": "HubSpot achieves strong visibility on Gemini with 5 mentions across all 3 prompts — ranking #2 behind Salesforce (7 mentions). Gemini positions HubSpot as the accessible alternative with excellent ease-of-use, though it acknowledges limitations for complex enterprise needs.",
          "promptsMentionSummary": "Consistent mentions across all prompts with emphasis on HubSpot's free tier, marketing integration, and user-friendly interface. Positioned as ideal for SMBs and growing businesses."
        },
        "perplexity": {
          "summary": "HubSpot leads on Perplexity with 6 total mentions across all 3 prompts — ranking #1 ahead of Salesforce (5 mentions) and Pipedrive (3 mentions). The platform consistently positions HubSpot as the go-to recommendation for businesses seeking balance between features and accessibility.",
          "promptsMentionSummary": "Dominant in small business recommendations and automation queries. Featured as the accessible alternative to Salesforce in enterprise comparisons, capturing 'better value for smaller teams' positioning."
        }
      }
    },
    "Pipedrive": {
      "platformPerformance": {
        "chatgpt": {
          "summary": "Pipedrive achieves focused visibility on ChatGPT, appearing in 2 of 3 prompts with 3 total mentions — ranking #3 behind HubSpot and Salesforce. Positioned as an affordable, sales-pipeline-focused alternative for small teams.",
          "promptsMentionSummary": "Mentioned in small business recommendations and automation queries as a cost-effective option with visual pipeline management. **Absent from enterprise comparison query** — limiting perception as an enterprise-grade competitor."
        },
        "gemini": {
          "summary": "Pipedrive shows modest visibility on Gemini with 3 mentions across 2 of 3 prompts — ranking #3. Gemini emphasizes Pipedrive's pipeline-focused approach and competitive pricing for sales teams.",
          "promptsMentionSummary": "Featured in small business and automation queries with focus on visual pipelines and email automation. Missing from enterprise comparison discussions."
        },
        "perplexity": {
          "summary": "Pipedrive achieves targeted visibility on Perplexity with 3 mentions across 2 of 3 prompts — ranking #3 well behind HubSpot (6) and Salesforce (5). Perplexity positions Pipedrive as an affordable, sales-focused alternative.",
          "promptsMentionSummary": "Appears in small business recommendations and automation features queries as a cost-effective, pipeline-focused option. Absent from enterprise comparison query."
        }
      }
    }
  },

  "promptResults": [
    {
      "platform": "chatgpt",
      "prompts": [
        {
          "promptText": "What are the best CRM tools for small businesses?",
          "response": "For small businesses, the best CRM options include HubSpot CRM (free tier with robust features), Zoho CRM (affordable at $14/user/month with excellent customization), and Pipedrive (visual pipeline management starting at $14/user/month). These tools prioritize ease of use, affordability, and essential features like contact management and sales automation...",
          "allBrandsMentioned": [
            "HubSpot",
            "Zoho",
            "Pipedrive",
            "Freshsales",
            "Agile CRM"
          ]
        },
        {
          "promptText": "Compare enterprise CRM solutions",
          "response": "Salesforce excels for enterprise sales teams handling complex, large-scale operations with features like Einstein AI, advanced forecasting, and deep customization through AppExchange. HubSpot Enterprise offers a more accessible alternative with simpler implementation but may lack depth for multi-region complexity...",
          "allBrandsMentioned": [
            "Salesforce",
            "HubSpot",
            "Microsoft Dynamics",
            "Oracle"
          ]
        },
        {
          "promptText": "Which CRM has the best automation features?",
          "response": "HubSpot CRM stands out for intuitive automation with email sequences, lead routing, and deal stage workflows. Salesforce provides enterprise-level automation with Einstein AI for lead scoring and predictive analytics. For budget-conscious teams, Zoho CRM offers Zia AI for predictions and workflow automation at lower cost...",
          "allBrandsMentioned": ["HubSpot", "Salesforce", "Zoho", "Freshsales"]
        }
      ]
    },
    {
      "platform": "gemini",
      "prompts": [
        {
          "promptText": "What are the best CRM tools for small businesses?",
          "response": "Top CRM solutions for small businesses include HubSpot (excellent free tier), Salesforce Essentials (scaled-down enterprise features), and Zoho CRM (best value for customization). Each offers contact management, pipeline tracking, and integrations with popular business tools...",
          "allBrandsMentioned": [
            "HubSpot",
            "Salesforce",
            "Zoho",
            "Pipedrive",
            "Freshsales"
          ]
        },
        {
          "promptText": "Compare enterprise CRM solutions",
          "response": "Salesforce remains the market leader for enterprise CRM with unmatched customization, Einstein AI capabilities, and the largest ecosystem of integrations. HubSpot has emerged as a viable alternative for companies seeking faster implementation with strong marketing alignment...",
          "allBrandsMentioned": [
            "Salesforce",
            "HubSpot",
            "Microsoft Dynamics",
            "SAP"
          ]
        },
        {
          "promptText": "Which CRM has the best automation features?",
          "response": "Salesforce leads in enterprise automation with Einstein AI powering lead scoring, forecasting, and workflow automation. HubSpot excels in marketing-sales alignment with intuitive sequences. Pipedrive offers strong pipeline automation with visual workflows...",
          "allBrandsMentioned": ["Salesforce", "HubSpot", "Pipedrive", "Zoho"]
        }
      ]
    },
    {
      "platform": "perplexity",
      "prompts": [
        {
          "promptText": "What are the best CRM tools for small businesses?",
          "response": "HubSpot CRM, Zoho CRM, and Pipedrive stand out as top CRM options for small businesses due to their affordability, ease of use, and essential features. HubSpot offers a robust free tier, Zoho excels in customization, and Pipedrive focuses on visual pipeline management...",
          "allBrandsMentioned": [
            "HubSpot",
            "Zoho",
            "Pipedrive",
            "Freshsales",
            "Less Annoying CRM"
          ]
        },
        {
          "promptText": "Compare enterprise CRM solutions",
          "response": "Salesforce excels over HubSpot for enterprise sales teams handling complex operations. Salesforce offers highly customizable pipelines, territory management, and Einstein AI for predictions. HubSpot suits smaller or faster-moving teams but lacks depth for intricate enterprise needs...",
          "allBrandsMentioned": ["Salesforce", "HubSpot"]
        },
        {
          "promptText": "Which CRM has the best automation features?",
          "response": "HubSpot CRM stands out for intuitive automation tailored to sales and marketing workflows. Salesforce excels in enterprise-level customization with Einstein AI. Zoho CRM features Zia AI for predictions and multi-channel automation at lower cost...",
          "allBrandsMentioned": ["HubSpot", "Salesforce", "Zoho", "Freshsales"]
        }
      ]
    }
  ],

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

This Actor uses Pay-Per-Event pricing. You pay a flat fee per complete analysis, not for platform usage.

| Event            | Price | What You Get                                       |
| ---------------- | ----- | -------------------------------------------------- |
| `brand-analysis` | $0.20 | Complete analysis across all platforms and prompts |

**💡 Example:** Analyzing your brand across 3 AI platforms with 3 prompts costs $0.20 total.

### Tier Discounts

Apify subscription members get discounts:

| Plan           | Price per Analysis |
| -------------- | ------------------ |
| Free / Starter | $0.20              |
| Bronze         | $0.18 (10% off)    |
| Silver         | $0.15 (25% off)    |
| Gold           | $0.12 (40% off)    |

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

## 💬 Questions or Issues?

If you encounter problems or have feature requests, please open an issue on the [Issues tab](https://apify.com/your-username/ai-brand-tracker/issues) of the Actor's page in the Apify Store.

---

## 📝 Changelog

### v1.0.0 (2025-01-11)

**Initial Release** 🚀

- Multi-platform brand visibility tracking (ChatGPT, Gemini, Perplexity)
- AI-powered brand mention detection with context analysis
- Competitive benchmarking across AI platforms
- Plain English summaries for actionable insights
- Custom prompt support
- Pay-per-event pricing ($0.20 per complete analysis)
