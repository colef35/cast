import os
import re
from app.models.product_profile import ProductProfile
from app.models.opportunity import OpportunityCreate
from app.services.datum_profile import DATUM_PROFILE, DRAFT_VOICES, detect_feature


def _keyword_score(text: str, keywords: list[str]) -> float:
    text = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text)
    return min(hits / max(len(keywords) * 0.3, 1), 1.0)


def _buying_signal_score(text: str) -> float:
    text = text.lower()
    signals = DATUM_PROFILE["buying_signals"]
    hits = sum(1 for s in signals if s in text)
    return min(hits * 0.2, 1.0)


def _roi_score(title: str, body: str) -> float:
    text = (title + " " + body).lower()
    score = 0.2
    # Active question = high ROI
    if any(q in text for q in ["?", "how do", "what do", "anyone", "recommend", "suggestions"]):
        score += 0.3
    # Pain point language
    if any(p in text for p in ["frustrated", "tired", "manual", "spreadsheet", "pain", "wish"]):
        score += 0.3
    # Generic discussion = lower ROI
    if len(body) < 100:
        score -= 0.1
    return min(max(score, 0.0), 1.0)


def _build_draft(product: ProductProfile, opp: OpportunityCreate) -> str:
    combined = opp.source_title + " " + opp.source_body
    feature = detect_feature(combined)
    template = DRAFT_VOICES.get(opp.channel.value, DRAFT_VOICES["reddit"])
    return template.format(
        feature=feature,
        url=product.url or DATUM_PROFILE["url"],
    )


def score_and_draft(product: ProductProfile, opp: OpportunityCreate) -> tuple[float, float, str]:
    combined = opp.source_title + " " + opp.source_body

    relevance = max(
        _keyword_score(combined, product.keywords),
        _buying_signal_score(combined),
    )
    roi = _roi_score(opp.source_title, opp.source_body)

    # Kill low-relevance noise early
    if relevance < 0.15:
        roi = roi * 0.3

    draft = _build_draft(product, opp)

    # Upgrade to AI if key available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            relevance, roi, draft = _ai_score_and_draft(api_key, product, opp)
        except Exception:
            pass

    return round(relevance, 3), round(roi, 3), draft


def _ai_score_and_draft(api_key: str, product: ProductProfile, opp: OpportunityCreate) -> tuple[float, float, str]:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    combined = opp.source_title + " " + opp.source_body
    feature = detect_feature(combined)

    prompt = f"""You are a founder of {product.name} — {product.tagline}.
Target audience: {product.target_audience}
Core pain solved: {product.pain_point_solved}
URL: {product.url}

You found this {opp.channel} post:
Title: {opp.source_title}
Body: {opp.source_body[:1500]}

Most relevant feature to highlight: {feature}

Score this opportunity and write a reply.

Rules for the reply:
- Sound like a real person, not marketing
- Be genuinely helpful even if they don't click
- Only mention the product if it truly fits — if it doesn't fit well, say so honestly
- Match the tone of the channel ({opp.channel})
- Keep it under 3 sentences for reddit/twitter, up to 5 for linkedin/hackernews

Reply in this exact format:
RELEVANCE: <0.0-1.0>
ROI: <0.0-1.0>
DRAFT:
<reply>"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text
    lines = text.strip().split("\n")
    relevance = roi = 0.5
    draft_lines, in_draft = [], False
    for line in lines:
        if line.startswith("RELEVANCE:"):
            try:
                relevance = float(line.split(":")[1].strip())
            except Exception:
                pass
        elif line.startswith("ROI:"):
            try:
                roi = float(line.split(":")[1].strip())
            except Exception:
                pass
        elif line.startswith("DRAFT:"):
            in_draft = True
        elif in_draft:
            draft_lines.append(line)
    return relevance, roi, "\n".join(draft_lines).strip()
