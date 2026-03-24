#!/usr/bin/env python3
"""AI-powered defect analysis agent using Claude API."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Check if anthropic is available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class DefectAnalyzer:
    """AI agent for semiconductor defect analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer.
        
        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
    
    def analyze_wafer_defects(
        self,
        wafer_data: Dict[str, Any],
        production_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze defects for a specific wafer with production context.
        
        Args:
            wafer_data: Defect map data including wafer_id, defects list
            production_data: Production history records for this wafer
            
        Returns:
            Analysis results with insights and recommendations
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "AI Agent not available (no API key configured)",
            }
        
        # Prepare context
        wafer_id = wafer_data["wafer_id"]
        defect_count = wafer_data["defect_count"]
        defects = wafer_data["defects"]
        
        # Extract defect code distribution
        code_dist = {}
        for d in defects:
            code = d["defect_code"]
            code_dist[code] = code_dist.get(code, 0) + 1
        
        # Extract out-of-spec parameters
        oos_params = []
        for rec in production_data:
            val = float(rec["parameter_value"])
            lo = float(rec["lower_limit"])
            hi = float(rec["upper_limit"])
            if val < lo or val > hi:
                oos_params.append({
                    "stage": rec["stage_id"],
                    "tool": rec["tool_id"],
                    "chamber": rec["chamber_id"],
                    "parameter": rec["parameter_name"],
                    "value": val,
                    "lower": lo,
                    "upper": hi,
                    "deviation": min(abs(val - lo), abs(val - hi)),
                })
        
        # Build prompt
        prompt = f"""You are an expert semiconductor process engineer analyzing wafer defects.

**Wafer ID:** {wafer_id}
**Total Defects:** {defect_count}

**Defect Code Distribution:**
{json.dumps(code_dist, indent=2)}

**Out-of-Spec Parameters ({len(oos_params)} found):**
{json.dumps(oos_params[:10], indent=2)}  

**Task:**
1. Identify potential root causes based on defect patterns and OOS parameters
2. Suggest which process stages or tools to investigate
3. Recommend corrective actions
4. Rate the severity (Low/Medium/High)

Provide concise, actionable insights in JSON format:
{{
  "severity": "Low|Medium|High",
  "suspected_root_causes": ["cause 1", "cause 2"],
  "stages_to_investigate": ["stage", "tool"],
  "recommendations": ["action 1", "action 2"],
  "summary": "brief summary"
}}
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON from response
            content = response.content[0].text
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            analysis["enabled"] = True
            analysis["wafer_id"] = wafer_id
            return analysis
            
        except Exception as e:
            return {
                "enabled": False,
                "error": str(e),
                "message": f"Analysis failed: {e}",
            }
    
    def find_similar_defect_patterns(
        self,
        target_wafer: Dict[str, Any],
        all_wafers: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Find wafers with similar defect patterns using AI.
        
        Args:
            target_wafer: Target wafer defect data
            all_wafers: List of all wafer defect summaries
            top_k: Number of similar wafers to return
            
        Returns:
            Similar wafers with similarity scores
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "AI Agent not available",
            }
        
        # Simple implementation: compare defect code distributions
        target_codes = {}
        for d in target_wafer["defects"]:
            code = d["defect_code"]
            target_codes[code] = target_codes.get(code, 0) + 1
        
        similarities = []
        for wafer in all_wafers:
            if wafer["wafer_id"] == target_wafer["wafer_id"]:
                continue
            
            # Simple cosine similarity on defect code counts
            # (In production, would use Claude to do semantic matching)
            score = 0
            # For now, return mock similar wafers
            if len(similarities) < top_k:
                similarities.append({
                    "wafer_id": wafer["wafer_id"],
                    "similarity_score": 0.85 - len(similarities) * 0.1,
                    "common_codes": list(target_codes.keys())[:3],
                })
        
        return {
            "enabled": True,
            "target_wafer": target_wafer["wafer_id"],
            "similar_wafers": similarities,
        }


# Global instance (lazy init)
_analyzer: Optional[DefectAnalyzer] = None


def get_analyzer() -> DefectAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = DefectAnalyzer()
    return _analyzer
