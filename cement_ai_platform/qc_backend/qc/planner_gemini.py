import os, json, re, google.generativeai as genai
from typing import Dict, Any
from .config import settings
from .schemas import Plan, PlanAction

PROMPT_TMPL = """
You are an expert cement quality control assistant. Your primary goal is to propose SMALL, SAFE, and PROACTIVE corrections to maintain cement quality KPIs within their target bands, optimizing for stability and efficiency.

Targets:
- LSF (Lime Saturation Factor): {lsf_min} to {lsf_max}
- Blaine (Fineness): {bl_min} to {bl_max}
- fCaO (Free Lime): Less than {fcao_max}
- **Energy Consumption**: Minimize this value where possible without compromising quality.

When proposing actions, consider the following:
1.  **Prioritize Stability**: Aim to bring KPIs back to the center of their target bands, not just within limits.
2.  **Small, Incremental Changes**: Prefer smaller adjustments to avoid overcorrection and maintain process stability.
3.  **Interconnectedness**: Acknowledge that changes to one knob (e.g., raw mix) can affect multiple KPIs.
4.  **Reasoning**: Provide clear, concise, and technically sound reasons for each proposed action.
5.  **Current Context**: Use the provided window statistics and detected issue to inform your decisions.

Return ONLY compact JSON per the following schema. Ensure all fields are present and correctly formatted.

SCHEMA:
{{
 "issue": "string",
 "kpi_impact": {{"LSF":"up|down|neutral", "Blaine":"up|down|neutral", "fCaO":"up|down|neutral"}},
 "actions": [{{"knob":"sand_pct","delta_pct":-0.5,"reason":"SiO2 high → reduce sand to lower LSF"}},
             {{"knob":"limestone_pct","delta_pct":+0.5,"reason":"Raise CaO to lift LSF and balance raw mix"}}],
 "notes":"string (Optional: provide additional context or monitoring instructions)"
}}

CURRENT PLANT STATE:
- Window statistics (recent trends and values): {window_stats}
- Detected issue (if any): {issue_text}
- Current knob settings: {knobs}

OPERATIONAL CONSTRAINTS (Ramp Limits per step):
- Raw mix components (limestone_pct, sand_pct, clay_pct): ±{ramp}%
- Separator speed: ±{sep_ramp} RPM
- Gypsum percentage: ±{gy_ramp}%
- **Crucial**: Ensure limestone_pct + sand_pct + clay_pct always sums to approximately 100%. If your actions cause a deviation, explain how it will be balanced (e.g., by adjusting clay_pct).
"""

def _extract_json(text: str) -> Dict[str, Any]:
    # Try to find a JSON block, potentially wrapped in markdown code fences
    m = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if m:
        payload = m.group(1)
    else:
        # Fallback to original behavior if no markdown fence is found
        m = re.search(r"\{.*\}", text, flags=re.S)
        payload = m.group(0) if m else text
    
    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Problematic payload: {payload}")
        # Return a more informative error message
        return {"issue": "JSON Decode Error", "kpi_impact": {}, "actions": [], "notes": f"Failed to parse AI response. Raw text: {payload}"}


def propose_plan(window_stats: Dict[str, Any], issue_text: str, knobs: Dict[str, float]) -> Plan:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        # Return a default plan indicating configuration error
        return Plan(issue="Gemini API Configuration Error", kpi_impact={}, actions=[], notes="Failed to configure Gemini API.")

    try:
        prompt = PROMPT_TMPL.format(
            lsf_min=settings.LSF_MIN, lsf_max=settings.LSF_MAX,
            bl_min=settings.BLAINE_MIN, bl_max=settings.BLAINE_MAX,
            fcao_max=settings.FCAO_MAX,
            window_stats=json.dumps(window_stats, default=str)[:2000],
            issue_text=issue_text,
            knobs=json.dumps(knobs),
            ramp=settings.RAMP_LIMIT_PCT,
            sep_ramp=settings.SEP_RAMP_LIMIT,
            gy_ramp=settings.GYPSUM_RAMP_LIMIT,
        )
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        raw_response_text = resp.text.strip()
        print(f"DEBUG: Raw Gemini response: {raw_response_text}") # Add this line for debugging
        plan_json = _extract_json(raw_response_text)
        
        # validate minimally
        actions = [PlanAction(**a) for a in plan_json.get("actions", [])]
        return Plan(issue=plan_json.get("issue",""),
                    kpi_impact=plan_json.get("kpi_impact", {"LSF":"neutral","Blaine":"neutral","fCaO":"neutral"}),
                    actions=actions,
                    notes=plan_json.get("notes"))

    except google.api_core.exceptions.PermissionDenied as e:
        print(f"Gemini API Permission Denied: {e}")
        return Plan(issue="Gemini API Authentication Error", kpi_impact={}, actions=[], notes="Permission denied. Please check if your GEMINI_API_KEY is valid and has the required permissions.")
    except google.api_core.exceptions.GoogleAPIError as e:
        print(f"Gemini API Error: {e}")
        # Return a default plan indicating API error
        return Plan(issue="Gemini API Error", kpi_impact={}, actions=[], notes=f"Error calling Gemini API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during plan generation: {e}")
        # Return a default plan for any other unexpected errors
        return Plan(issue="Plan Generation Error", kpi_impact={}, actions=[], notes=f"An unexpected error occurred: {e}")
