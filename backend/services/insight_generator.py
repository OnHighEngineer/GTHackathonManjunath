# services/insight_generator.py
"""
InsightGenerator using Google Gemini (google-generativeai).
This module exposes an async `generate_insights(processed_data)` method
that your main.py expects (await insight_generator.generate_insights(...)).
If Gemini is unavailable or the key is missing, it returns a canned fallback.
"""

import os
import asyncio
from typing import Any, Dict

# Import Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    genai = None
    GEMINI_AVAILABLE = False

# Read key from env
GEMINI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-flash"  # fast model; change if you prefer another

if GEMINI_KEY and GEMINI_AVAILABLE:
    try:
        genai.configure(api_key=GEMINI_KEY)
        GEMINI_CONFIGURED = True
        print("Gemini API configured successfully")
    except Exception as e:
        print("Warning: failed to configure google.generativeai:", e)
        GEMINI_CONFIGURED = False
else:
    GEMINI_CONFIGURED = False
    if not GEMINI_KEY:
        print("Warning: GOOGLE_API_KEY / GEMINI_API_KEY not set; InsightGenerator will use fallback text.")
    if not GEMINI_AVAILABLE:
        print("Warning: google.generativeai library not available; install via `pip install google-generativeai`")


class InsightGenerator:
    def __init__(self):
        self.model = MODEL_NAME
        self.gemini_available = GEMINI_CONFIGURED
        print(f"InsightGenerator initialized. Gemini available: {self.gemini_available}")

    async def generate_insights(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously generate insights from processed_data.
        Returns a dict (so main.py can store `insights` as dict).
        If Gemini call fails, returns a demo fallback dict.
        """
        print(f"Generating insights for data with {processed_data.get('metadata', {}).get('total_rows', 0)} rows")
        
        # Build a textual summary from processed_data for LLM
        # Keep it concise to reduce latency
        summary = self._build_summary(processed_data)
        
        print(f"Built summary of {len(summary)} characters")

        # If Gemini is configured and SDK available, call it in a thread to avoid blocking the event loop
        if self.gemini_available and GEMINI_KEY and genai:
            try:
                print("Attempting to call Gemini API...")
                # Use asyncio.to_thread to run blocking network call off the event loop
                raw_text = await asyncio.to_thread(self._call_gemini, summary)
                print("Gemini API call successful")
                return {"text": raw_text, "source": "gemini"}
            except Exception as e:
                print(f"Gemini API error: {str(e)}")
                print("Falling back to canned insights...")
                # fall through to fallback
        else:
            print(f"Gemini not available. Available: {self.gemini_available}, Key: {bool(GEMINI_KEY)}, SDK: {bool(genai)}")
        
        # Fallback canned insights
        fallback = self._canned_fallback(processed_data)
        return {"text": fallback, "source": "fallback"}

    def _call_gemini(self, prompt_text: str) -> str:
        """
        Blocking call to Gemini SDK. Kept in sync function and run via to_thread.
        Uses a straightforward text generation call and returns a single string.
        """
        try:
            # Compose an instruction prompt: ask for short insights + recommendations + summary
            prompt = f"""
You are an expert data analyst. Given the following concise data summary, produce:
1) Three short business insights (one-line each).
2) Two practical recommendations.
3) A one-sentence executive summary.

Format the response as:
**Insights:**
1. [Insight 1]
2. [Insight 2]
3. [Insight 3]

**Recommendations:**
1. [Recommendation 1]
2. [Recommendation 2]

**Executive Summary:**
[One sentence summary]

Data summary:
{prompt_text}
"""
            
            # Try the newer generate_content API which is more reliable
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt, generation_config={"max_output_tokens": 512})
            
            # Extract text from response
            if hasattr(response, "text"):
                return response.text.strip()
            elif hasattr(response, "candidates") and response.candidates:
                first_candidate = response.candidates[0]
                if hasattr(first_candidate, "content"):
                    if hasattr(first_candidate.content, "parts"):
                        parts = first_candidate.content.parts
                        return " ".join([part.text for part in parts if hasattr(part, "text")]).strip()
                    elif hasattr(first_candidate.content, "text"):
                        return first_candidate.content.text.strip()
            
            # Fallback to string representation
            return str(response).strip()
            
        except Exception as e:
            print(f"Error in _call_gemini: {str(e)}")
            # Try alternate approach if the first fails
            try:
                # Try the simpler API
                response = genai.generate_text(model=self.model, prompt=prompt_text[:500], max_output_tokens=512)
                if hasattr(response, "text"):
                    return response.text.strip()
                return str(response).strip()
            except Exception as e2:
                print(f"Alternate Gemini call also failed: {str(e2)}")
                raise

    def _build_summary(self, processed_data: Dict[str, Any]) -> str:
        """
        Create a compact data summary from processed_data.
        Try to include: total rows, columns, top numeric columns and example aggregates.
        This function should be adapted to the shape of your DataProcessor output.
        """
        meta = processed_data.get("metadata", {})
        total_rows = meta.get("total_rows", "unknown")
        columns = meta.get("columns", [])
        numeric_stats = meta.get("numeric_stats", {})  # optional
        top_cols = ", ".join(columns[:6]) if columns else "N/A"
        
        # Build concise numeric summary if available
        num_summary_lines = []
        if isinstance(numeric_stats, dict) and numeric_stats:
            for col, stats in list(numeric_stats.items())[:5]:
                # stats expected like {'mean':..., 'min':..., 'max':...}
                mean = stats.get("mean", "N/A")
                md = f"{col}: mean={mean}, min={stats.get('min','N/A')}, max={stats.get('max','N/A')}"
                num_summary_lines.append(md)

        summary = (
            f"Dataset Summary:\n"
            f"- Total rows: {total_rows}\n"
            f"- Number of columns: {len(columns)}\n"
            f"- Column names (sample): {top_cols}\n"
        )
        
        if num_summary_lines:
            summary += "\nNumeric column statistics:\n" + "\n".join(num_summary_lines) + "\n"
        
        # Check for categorical columns
        categorical_cols = meta.get("categorical_columns", [])
        if categorical_cols:
            summary += f"\nCategorical columns: {', '.join(categorical_cols[:5])}\n"
        
        # If processed_data contains a short preview, include first 200-800 chars
        preview = processed_data.get("preview_text") or processed_data.get("sample_text")
        if preview:
            # truncate to keep prompt short
            truncated_preview = preview[:600] + ("..." if len(preview) > 600 else "")
            summary += f"\nData preview:\n{truncated_preview}\n"
        
        # Add any other relevant metadata
        if meta.get("missing_values"):
            summary += f"\nMissing values detected in: {meta.get('missing_values')}\n"
        
        return summary

    def _canned_fallback(self, processed_data: Dict[str, Any]) -> str:
        """Return a demo insights string when the LLM is unavailable."""
        total_rows = processed_data.get("metadata", {}).get("total_rows", "unknown")
        columns = processed_data.get("metadata", {}).get("columns", [])
        col_count = len(columns)
        
        return (
            f"**Insights:**\n"
            f"1. The dataset contains {total_rows} records across {col_count} columns, providing a solid foundation for analysis.\n"
            f"2. Top performing metrics show consistent growth trends in key business indicators.\n"
            f"3. Data quality appears good with minimal missing values detected in critical fields.\n\n"
            f"**Recommendations:**\n"
            f"1. Focus on optimizing the highest performing segments which show 15-20% better conversion rates.\n"
            f"2. Consider A/B testing new strategies on underperforming categories to improve overall metrics.\n\n"
            f"**Executive Summary:**\n"
            f"The data reveals clear opportunities for performance optimization through targeted resource allocation and process improvements."
        )


# Create a singleton instance
insight_generator = InsightGenerator()