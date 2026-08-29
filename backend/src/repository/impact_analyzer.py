"""Impact Analyzer inspecting repository files, imports, and keywords to identify affected areas."""
import re
from pathlib import Path
from typing import Dict, List, Set
from pydantic import BaseModel


class ImpactPrediction(BaseModel):
    """Predicted impacted file with reasoning and confidence score."""
    file_path: str
    impact_type: str  # "SOURCE_MODIFICATION", "TEST_VERIFICATION", "NEW_MODULE", "DEPENDENCY"
    reason: str
    confidence: float
    matched_keywords: List[str] = []


class ImpactAnalyzer:
    """Analyzes requirements against repository topology and source code to estimate impact areas."""

    @staticmethod
    def analyze_impact(
        title: str,
        description: str,
        source_files: List[str],
        test_files: List[str],
        file_contents: Dict[str, str]
    ) -> List[ImpactPrediction]:
        """Calculates probable impacted files based on keyword overlap, imports, and test pairings."""
        predictions: List[ImpactPrediction] = []
        combined_text = f"{title} {description}".lower()
        
        # Tokenize requirements into significant keywords
        raw_tokens = re.findall(r"\b[a-zA-Z_]{3,}\b", combined_text)
        stopwords = {"the", "and", "for", "with", "that", "this", "from", "should", "must", "will", "have", "been"}
        keywords = {t for t in raw_tokens if t not in stopwords}

        # Check each source file
        for src in source_files:
            file_name = Path(src).stem.lower()
            content = file_contents.get(src, "").lower()
            
            matched = [kw for kw in keywords if kw in file_name or kw in content]
            
            score = 0.5  # Base probability for primary sources
            if any(kw == file_name for kw in keywords):
                score += 0.4
            elif matched:
                score += min(0.35, len(matched) * 0.1)

            if matched or len(source_files) <= 3:
                predictions.append(ImpactPrediction(
                    file_path=src,
                    impact_type="SOURCE_MODIFICATION",
                    reason=f"Matches requirements keywords: {', '.join(matched[:4]) or 'Primary application module'}",
                    confidence=min(0.99, round(score, 2)),
                    matched_keywords=matched
                ))

        # Check each test file
        for test in test_files:
            test_stem = Path(test).stem.lower().replace("test_", "").replace("_test", "").replace(".spec", "")
            content = file_contents.get(test, "").lower()
            
            matched = [kw for kw in keywords if kw in test_stem or kw in content]
            paired_src = any(Path(p.file_path).stem.lower() in test.lower() for p in predictions if p.impact_type == "SOURCE_MODIFICATION")

            score = 0.6 if paired_src else 0.4
            if matched:
                score += min(0.3, len(matched) * 0.1)

            if paired_src or matched or len(test_files) <= 2:
                predictions.append(ImpactPrediction(
                    file_path=test,
                    impact_type="TEST_VERIFICATION",
                    reason=f"Unit tests for verifying changes and preventing regressions ({', '.join(matched[:3]) or 'Paired test suite'})",
                    confidence=min(0.98, round(score, 2)),
                    matched_keywords=matched
                ))

        # Sort by confidence descending
        predictions.sort(key=lambda p: p.confidence, reverse=True)
        return predictions
