import logging
import re
from typing import Dict, Any, Optional

from app.core.config import load_config, save_config

logger = logging.getLogger("ForgeHub.InstructionRefiner")


def heuristic_compress(text: str, tier: str) -> str:
    """
    Intelligent rule-based compression fallback when AI providers are offline/unconfigured.
    Removes conversational fluff, verbose prefixes, and boilerplate while preserving core directives.
    """
    # 1. Strip common conversational prefixes and filler
    filler_patterns = [
        r"(?i)\b(please\s+(make\s+sure\s+to|ensure\s+that\s+you|try\s+to|remember\s+to|be\s+sure\s+to))\b",
        r"(?i)\b(i\s+would\s+like\s+you\s+to|i\s+want\s+you\s+to|it\s+is\s+important\s+that\s+you)\b",
        r"(?i)\b(as\s+an\s+ai\s+(assistant|model)|in\s+all\s+your\s+responses)\b",
        r"(?i)\b(always\s+keep\s+in\s+mind\s+that|do\s+not\s+forget\s+to)\b",
        r"(?i)\b(you\s+should\s+always|you\s+must\s+always)\b",
        r"(?i)\b(could\s+you\s+please|kindly|basically|essentially)\b",
    ]
    
    cleaned = text.strip()
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, "", cleaned)
    
    # Clean up whitespace and punctuation artifacts
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*([,.;:])\s*", r"\1 ", cleaned).strip()

    if tier == "short":
        return text.strip()

    sentences = [s.strip() for s in re.split(r"[.!?\n]+", cleaned) if s.strip()]
    if not sentences:
        return cleaned

    if tier == "medium":
        # Target ~55-65% length
        condensed_sentences = []
        for s in sentences:
            s = re.sub(r'^[,\s;:.-]+', '', s).strip()
            if s:
                s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
                condensed_sentences.append(s)
        result = "; ".join(condensed_sentences)
        if not result.endswith("."):
            result += "."
        return result

    # Big tier: aggressively distill down to core rules (target 20-30%)
    condensed_points = []
    for s in sentences:
        s = re.sub(r'^[,\s;:.-]+', '', s).strip()
        words = s.split()
        if len(words) > 12:
            clause_split = re.split(r"(?i)\b(which|because|since|for\s+example|such\s+as|so\s+that)\b", s)
            words = clause_split[0].strip().split()
        if words:
            s_short = " ".join(words)
            s_short = re.sub(r'^[,\s;:.-]+', '', s_short).strip()
            if s_short:
                s_short = s_short[0].upper() + s_short[1:] if len(s_short) > 1 else s_short.upper()
                condensed_points.append(s_short)
            
    # Limit number of points to preserve strict target length
    max_points = max(2, len(sentences) // 2)
    result = "; ".join(condensed_points[:max_points])
    if not result.endswith("."):
        result += "."
    return result


def refine_personalized_instruction(raw_instruction: str, db_manager=None) -> Dict[str, Any]:
    """
    Refines and compresses the user's custom personalized instruction:
    - Short (<120 chars or <=25 words): Kept same (0% reduction).
    - Medium (120-400 chars or 26-80 words): Condense by 30-40% (target 50-60% length) using AI.
    - Big (>400 chars or >80 words): Distill by 70-80% (target 20-30% length) using AI.
    
    Falls back to heuristic compression if AI router is unavailable.
    """
    raw = (raw_instruction or "").strip()
    if not raw:
        return {
            "raw_instruction": "",
            "refined_instruction": "",
            "original_len": 0,
            "refined_len": 0,
            "reduction_pct": 0.0,
            "tier": "empty",
            "method": "none"
        }

    char_count = len(raw)
    word_count = len(raw.split())

    # Tier determination
    if char_count < 120 or word_count <= 25:
        tier = "short"
    elif char_count <= 400 or word_count <= 80:
        tier = "medium"
    else:
        tier = "big"

    # Case A: Short -> Keep as-is
    if tier == "short":
        return {
            "raw_instruction": raw,
            "refined_instruction": raw,
            "original_len": char_count,
            "refined_len": char_count,
            "reduction_pct": 0.0,
            "tier": tier,
            "method": "direct_short"
        }

    # Prepare AI distillation prompts
    target_len_chars = int(char_count * (0.55 if tier == "medium" else 0.25))
    target_words = int(word_count * (0.60 if tier == "medium" else 0.25))

    if tier == "medium":
        system_prompt = (
            "You are a prompt engineering and instruction compression specialist. "
            "Your task is to refine and condense the user's custom instructions by 30% to 40% "
            f"(target length: approximately {target_len_chars} characters or {target_words} words). "
            "Strip conversational filler, polite greetings, and wordy explanations. "
            "Preserve 100% of the core directives, constraints, style preferences, tech stack, and behavioral rules. "
            "Output ONLY the condensed instruction text. Do not wrap in markdown quotes, and do not add preamble or commentary."
        )
    else:
        system_prompt = (
            "You are a prompt engineering and instruction distillation specialist. "
            "Your task is to aggressively distill, summarize, and compress the user's custom instructions by 70% to 80% "
            f"(target length: approximately {target_len_chars} characters or {target_words} words). "
            "Transform the input into dense, compact, high-priority imperative directives. "
            "Strip all background stories, conversational text, examples, and filler words. "
            "Preserve all strict constraints, role identities, formatting requirements, and key tech stack rules. "
            "Output ONLY the distilled instruction text. Do not wrap in markdown quotes, and do not add preamble or commentary."
        )

    refined_text = ""
    method = "ai"

    if db_manager:
        try:
            from app.ai.router import ModelRouter
            router = ModelRouter(db_manager)
            
            # Request compression using Lightweight/fast category
            ai_response = router.route_request(
                prompt=f"Condense these custom user instructions into a dense directive:\n\n{raw}",
                category="Lightweight",
                system_prompt=system_prompt,
                max_tokens=256
            )
            
            if isinstance(ai_response, tuple):
                refined_text = ai_response[0].strip()
            elif isinstance(ai_response, str):
                refined_text = ai_response.strip()

            # Strip any residual markdown quote blocks or preamble like "Here is the condensed..."
            if refined_text.startswith("```") and refined_text.endswith("```"):
                lines = refined_text.splitlines()
                refined_text = "\n".join(lines[1:-1]).strip()

            refined_text = re.sub(r'^(Here\s+is\s+the\s+(condensed|distilled|refined)\s+instruction:?|Refined\s+instruction:?)\s*', '', refined_text, flags=re.I).strip()
            refined_text = refined_text.strip('\'"')

        except Exception as e:
            logger.warning(f"AI instruction refinement unavailable or failed: {e}. Using heuristic fallback.")
            refined_text = ""

    # Fallback to heuristic compression if AI was empty or errored
    if not refined_text:
        refined_text = heuristic_compress(raw, tier)
        method = "heuristic_fallback"

    refined_len = len(refined_text)
    reduction = round(max(0.0, ((char_count - refined_len) / char_count) * 100), 1)

    return {
        "raw_instruction": raw,
        "refined_instruction": refined_text,
        "original_len": char_count,
        "refined_len": refined_len,
        "reduction_pct": reduction,
        "tier": tier,
        "method": method
    }


def save_personalized_instruction(result_dict: Dict[str, Any]) -> None:
    """Persists raw and refined personalized instructions and stats to config.json."""
    cfg = load_config()
    cfg["raw_personalized_instruction"] = result_dict.get("raw_instruction", "")
    cfg["refined_personalized_instruction"] = result_dict.get("refined_instruction", "")
    cfg["personalized_instruction_stats"] = {
        "original_len": result_dict.get("original_len", 0),
        "refined_len": result_dict.get("refined_len", 0),
        "reduction_pct": result_dict.get("reduction_pct", 0.0),
        "tier": result_dict.get("tier", "short"),
        "method": result_dict.get("method", "direct_short")
    }
    save_config(cfg)
