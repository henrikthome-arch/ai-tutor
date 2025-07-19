"""
Basic quality validation for AI analysis
Ensures educational appropriateness and analysis quality
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass

from .providers import BasicAnalysis

@dataclass
class ValidationResult:
    is_valid: bool
    score: float
    issues: List[str]
    warnings: List[str]
    confidence_adjusted: float

class BasicValidator:
    """Simple quality validator for AI analysis"""
    
    def __init__(self):
        # Keywords that might indicate inappropriate content
        self.inappropriate_keywords = [
            'inappropriate', 'error', 'failed', 'unable', 'cannot determine',
            'analysis unavailable', 'manual review required'
        ]
        
        # Educational quality indicators
        self.quality_indicators = [
            'understanding', 'progress', 'learning', 'development', 'skills',
            'comprehension', 'engagement', 'improvement', 'mastery', 'concept'
        ]
    
    def validate_analysis(self, analysis: BasicAnalysis, transcript: str) -> ValidationResult:
        """Basic validation checks for educational analysis"""
        
        issues = []
        warnings = []
        scores = []
        
        # Check completeness
        completeness_score = self._check_completeness(analysis, issues)
        scores.append(completeness_score)
        
        # Check quality indicators
        quality_score = self._check_quality_indicators(analysis, warnings)
        scores.append(quality_score)
        
        # Check for inappropriate content
        appropriateness_score = self._check_appropriateness(analysis, issues)
        scores.append(appropriateness_score)
        
        # Check confidence score
        confidence_score = self._check_confidence(analysis, warnings)
        scores.append(confidence_score)
        
        # Check processing metrics
        performance_score = self._check_performance(analysis, warnings)
        scores.append(performance_score)
        
        # Check evidence grounding (basic)
        evidence_score = self._check_evidence_grounding(analysis, transcript, warnings)
        scores.append(evidence_score)
        
        # Calculate overall score
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        # Adjust confidence based on validation
        confidence_adjusted = analysis.confidence_score * overall_score
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=overall_score,
            issues=issues,
            warnings=warnings,
            confidence_adjusted=confidence_adjusted
        )
    
    def _check_completeness(self, analysis: BasicAnalysis, issues: List[str]) -> float:
        """Check if all required fields are present and meaningful"""
        
        score = 0.0
        total_checks = 4
        
        # Check conceptual understanding
        if analysis.conceptual_understanding and analysis.conceptual_understanding.strip():
            if len(analysis.conceptual_understanding.strip()) > 20:  # Meaningful length
                score += 1.0
            else:
                issues.append("Conceptual understanding analysis too brief")
        else:
            issues.append("Missing conceptual understanding analysis")
        
        # Check engagement level
        if analysis.engagement_level and analysis.engagement_level.strip():
            if len(analysis.engagement_level.strip()) > 10:
                score += 1.0
            else:
                issues.append("Engagement level analysis too brief")
        else:
            issues.append("Missing engagement level analysis")
        
        # Check progress indicators
        if analysis.progress_indicators and analysis.progress_indicators.strip():
            if len(analysis.progress_indicators.strip()) > 15:
                score += 1.0
            else:
                issues.append("Progress indicators too brief")
        else:
            issues.append("Missing progress indicators")
        
        # Check recommendations
        if analysis.recommendations and analysis.recommendations.strip():
            if len(analysis.recommendations.strip()) > 20:
                score += 1.0
            else:
                issues.append("Recommendations too brief")
        else:
            issues.append("Missing recommendations")
        
        return score / total_checks
    
    def _check_quality_indicators(self, analysis: BasicAnalysis, warnings: List[str]) -> float:
        """Check for educational quality indicators in the analysis"""
        
        # Combine all analysis text
        full_text = ' '.join([
            analysis.conceptual_understanding,
            analysis.engagement_level,
            analysis.progress_indicators,
            analysis.recommendations
        ]).lower()
        
        # Count quality indicators
        indicator_count = 0
        for indicator in self.quality_indicators:
            if indicator in full_text:
                indicator_count += 1
        
        # Score based on indicator presence
        score = min(1.0, indicator_count / 5)  # Expect at least 5 indicators for full score
        
        if score < 0.5:
            warnings.append(f"Low educational quality indicators (found {indicator_count})")
        
        return score
    
    def _check_appropriateness(self, analysis: BasicAnalysis, issues: List[str]) -> float:
        """Check for inappropriate content or error messages"""
        
        # Combine all analysis text
        full_text = ' '.join([
            analysis.conceptual_understanding,
            analysis.engagement_level,
            analysis.progress_indicators,
            analysis.recommendations
        ]).lower()
        
        # Check for inappropriate keywords
        inappropriate_found = []
        for keyword in self.inappropriate_keywords:
            if keyword in full_text:
                inappropriate_found.append(keyword)
        
        if inappropriate_found:
            issues.append(f"Inappropriate content detected: {', '.join(inappropriate_found)}")
            return 0.0
        
        return 1.0
    
    def _check_confidence(self, analysis: BasicAnalysis, warnings: List[str]) -> float:
        """Check confidence score validity"""
        
        if analysis.confidence_score < 0.0 or analysis.confidence_score > 1.0:
            warnings.append(f"Invalid confidence score: {analysis.confidence_score}")
            return 0.0
        
        if analysis.confidence_score < 0.5:
            warnings.append(f"Low confidence score: {analysis.confidence_score:.2f}")
        
        return analysis.confidence_score
    
    def _check_performance(self, analysis: BasicAnalysis, warnings: List[str]) -> float:
        """Check processing performance metrics"""
        
        score = 1.0
        
        # Check processing time
        if analysis.processing_time > 30:
            warnings.append(f"Long processing time: {analysis.processing_time:.2f}s")
            score *= 0.8
        
        # Check cost estimate
        if analysis.cost_estimate > 0.1:  # $0.10 threshold
            warnings.append(f"High cost estimate: ${analysis.cost_estimate:.4f}")
            score *= 0.9
        
        return score
    
    def _check_evidence_grounding(self, analysis: BasicAnalysis, transcript: str, warnings: List[str]) -> float:
        """Basic check for evidence grounding"""
        
        if not transcript or len(transcript.strip()) < 50:
            warnings.append("Transcript too short for proper evidence grounding")
            return 0.5
        
        # Simple check: analysis should be proportional to transcript length
        total_analysis_length = len(' '.join([
            analysis.conceptual_understanding,
            analysis.engagement_level,
            analysis.progress_indicators,
            analysis.recommendations
        ]))
        
        # Expect roughly 10-30% of transcript length in analysis
        expected_min = len(transcript) * 0.05
        expected_max = len(transcript) * 0.5
        
        if total_analysis_length < expected_min:
            warnings.append("Analysis may be too brief relative to transcript content")
            return 0.7
        elif total_analysis_length > expected_max:
            warnings.append("Analysis may be too verbose relative to transcript content")
            return 0.8
        
        return 1.0
    
    def validate_transcript(self, transcript: str) -> ValidationResult:
        """Validate transcript before analysis"""
        
        issues = []
        warnings = []
        
        if not transcript or not transcript.strip():
            issues.append("Empty transcript")
            return ValidationResult(False, 0.0, issues, warnings, 0.0)
        
        # Check minimum length
        if len(transcript.strip()) < 50:
            issues.append("Transcript too short for meaningful analysis")
        
        # Check for basic conversation structure
        if ':' not in transcript and '-' not in transcript:
            warnings.append("Transcript may lack proper conversation formatting")
        
        # Check for educational content indicators
        educational_keywords = ['student', 'tutor', 'learn', 'understand', 'solve', 'explain', 'question']
        if not any(keyword in transcript.lower() for keyword in educational_keywords):
            warnings.append("Transcript may not contain educational content")
        
        score = 1.0 if len(issues) == 0 else 0.0
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=score,
            issues=issues,
            warnings=warnings,
            confidence_adjusted=score
        )

# Global validator instance
validator = BasicValidator()