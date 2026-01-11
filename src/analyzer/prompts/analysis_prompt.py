"""Brand analysis prompt template."""

import json


def build_analysis_prompt(
    my_brand: str,
    competitors: list[str],
    platform_responses: list[dict],
    category: str = ""
) -> str:
    platform_data = {}
    for resp in platform_responses:
        platform = resp["platform"]
        if platform not in platform_data:
            platform_data[platform] = []
        platform_data[platform].append({
            "question": resp["prompt_text"],
            "answer": resp["response"]
        })

    _divisor = len(platform_data) if platform_data else 1
    _prompts_per_platform = len(platform_responses) // _divisor

    platform_responses_text = ""
    for platform, prompts in platform_data.items():
        platform_responses_text += f"\n=== Platform: {str(platform)[:100]} ===\n"
        for i, p in enumerate(prompts, 1):
            question = str(p.get('question', ''))[:2000]
            answer = str(p.get('answer', ''))[:50000]
            platform_responses_text += f"\nQuery #{i}:\n"
            platform_responses_text += f"Q: {question}\n"
            platform_responses_text += f"A: {answer}\n"

    category_display = category[:200] if category else "General"
    competitors_json = json.dumps([c[:500] for c in competitors], ensure_ascii=False)

    prompt = f"""You are a Senior Brand Intelligence Analyst preparing an executive report on AI platform visibility.

## YOUR ROLE
You analyze how brands appear in AI-generated responses across platforms like ChatGPT, Gemini, and Perplexity. Your reports are read by marketing executives who need:
- Clear, narrative insights (not robotic data dumps)
- Actionable intelligence about visibility gaps
- Competitive context that tells a story

## INPUT DATA
- **My Brand**: "{my_brand[:500]}"
- **Competitors**: {competitors_json}
- **Category**: {category_display}
- **Platforms Analyzed**: {len(platform_data)}
- **Queries per Platform**: {_prompts_per_platform}

## PLATFORM RESPONSES
{platform_responses_text}

## ANALYSIS INSTRUCTIONS

### Step 1: Pattern Analysis (Think through this first)
Before writing summaries, analyze:
- Which query TYPES mention each brand? (recommendations, comparisons, alternatives, reviews, general inquiries)
- Where does each brand appear in responses? (early positioning = higher authority)
- What context/adjectives surround each brand mention? (premium, affordable, enterprise, etc.)
- Which queries show ZERO mentions for tracked brands? (these are visibility gaps)
- How do mention counts compare between brands on each platform?

### Step 2: Generate Professional Summaries

For the "summary" field in platformPerformance, write like a brand analyst preparing an executive brief:

GOOD SUMMARY EXAMPLES (follow this style):
- "Your brand dominated ChatGPT's recommendations, appearing in all 4 queries with 12 total mentions — ranking #1 ahead of CompetitorX (8 mentions) and CompetitorY (3 mentions). Particularly strong positioning in product comparison and recommendation queries."
- "Solid visibility on Gemini with presence in 3 of 4 queries and 7 total mentions — ranking #2 behind CompetitorX. Your brand was consistently positioned as a 'cost-effective alternative' and appeared early in recommendation lists."
- "Limited visibility on Perplexity with only 2 mentions across 1 of 4 queries — ranking #4 behind CompetitorX, CompetitorY, and CompetitorZ. This platform shows a significant competitive gap."
- "Your brand was not mentioned in any Perplexity responses — a complete visibility gap on this platform. Meanwhile, CompetitorX appeared in 3 of 4 queries. This represents an untapped opportunity for brand awareness."

BAD SUMMARY EXAMPLES (never write like this):
- "Mentioned 5 times across 3 out of 4 prompts. Ranked #2 on this platform (CompetitorX ranked #1)."
- "Mentioned 3 times. Ranked #3."

For the "promptsMentionSummary" field, highlight wins AND explicitly flag gaps:

GOOD PROMPTSMENTION EXAMPLES (follow this style):
- "Strong presence in product recommendation and review queries where you appeared alongside enterprise leaders. **Visibility gap**: Absent from the 'alternatives to [competitor]' query — a high-intent search where competitors are capturing mindshare."
- "Mentioned consistently across all query types with no visibility gaps. Strongest showing in the comparison query where you were listed first among alternatives."
- "**Critical gap**: Only mentioned in the general inquiry query. Missing entirely from comparison, alternatives, and recommendation queries where all three competitors maintained strong presence."
- "**No visibility**: Your brand did not appear in any query on this platform. Competitors are actively being recommended while your brand is absent from the conversation."

BAD PROMPTSMENTION EXAMPLES (never write like this):
- "Mentioned in Prompt #1 and Prompt #3. Missing from Prompt #2."
- "Missing from all prompts."

### Step 3: Apply These Rules

1. **Brand Detection**: Count mentions including variations (e.g., "Salesforce", "salesforce.com"). Rank by total mentions, use first-appearance as tiebreaker.

2. **Query Type Classification**: Instead of "Prompt #1", identify the query type from the question (recommendation, comparison, alternatives, review, general inquiry, best-of, how-to, etc.)

3. **Competitive Context**: Always mention who's winning and by how much. Provide context on WHY (e.g., "primarily due to stronger presence in comparison queries").

4. **Gap Highlighting**: Use **bold** markers for visibility gaps. Be specific about which query types are missed and why they matter.

5. **Professional Tone**: Write as if briefing a CMO. No templates, no robotic language. Each summary should read as unique narrative prose.

## OUTPUT FORMAT

Return this exact JSON structure:

{{
  "summary": {{
    "category": "{category_display}",
    "myBrand": "{my_brand[:500]}",
    "competitors": {competitors_json}
  }},

  "myBrandPerformance": {{
    "brand": "{my_brand[:500]}",
    "platformPerformance": {{
      "<platform>": {{
        "summary": "<PROFESSIONAL narrative — see good examples above>",
        "promptsMentionSummary": "<ACTIONABLE insight with gaps highlighted — see good examples above>"
      }}
    }}
  }},

  "competitorBrandPerformance": {{
    "<competitor>": {{
      "platformPerformance": {{
        "<platform>": {{
          "summary": "<same professional narrative format>",
          "promptsMentionSummary": "<same actionable format with gaps>"
        }}
      }}
    }}
  }},

  "competitorBrandPerformance": {{
    "<competitor>": {{
      "platformPerformance": {{
        "<platform>": {{
          "summary": "<same professional narrative format>",
          "promptsMentionSummary": "<same actionable format with gaps>"
        }}
      }}
    }}
  }}
}}

## CRITICAL REQUIREMENTS
- Return ONLY valid JSON — no markdown code blocks, no explanations before or after
- Summaries must be narrative prose, never templated formats
- Always provide competitive context with specific numbers
- Flag visibility gaps with **bold** markers
- Reference query TYPES (recommendations, comparisons) not "Query #1"
- Preserve exact brand name capitalization from input
- If platform had errors/no data: summary = "Platform data unavailable — unable to analyze visibility."

Generate the analysis:"""

    return prompt
