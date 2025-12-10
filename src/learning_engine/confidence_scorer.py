"""
Confidence Scoring System - Dynamic confidence calculation for knowledge chunks

This module implements proper confidence scoring that varies based on:
- Pattern confirmation frequency (how many times seen)
- Source quality (official approval vs. initial extraction)
- Municipality specificity (specific vs. general)
- Replicability (how consistently it works)
- Temporal decay (older patterns get slightly lower confidence)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class ConfidenceScorer:
    """Calculate dynamic confidence scores for knowledge chunks"""

    def __init__(self):
        """Initialize confidence scorer"""
        self.confirmation_counts: Dict[str, int] = {}  # Track how many times pattern confirmed

    def calculate_initial_confidence(
        self,
        source_type: str,
        approval_status: str,
        municipality: Optional[str] = None,
        replicable: bool = True,
        approval_speed: Optional[str] = None
    ) -> float:
        """
        Calculate initial confidence score for a new knowledge chunk

        Args:
            source_type: Type of source (feedback, approved_doc, etc.)
            approval_status: approved, rejected, or unknown
            municipality: Specific municipality or None for general
            replicable: Whether the pattern is consistently replicable
            approval_speed: fast, standard, slow, or unknown

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence by source type
        base_confidence = {
            "feedback": 0.75,      # Learned from real municipal feedback
            "approved_doc": 0.65,  # Extracted from approved examples
            "regulation": 0.85,    # Official BR18 regulations
            "insight": 0.70        # Extracted insights
        }.get(source_type, 0.5)

        # Adjust for approval status
        if approval_status == "approved":
            status_multiplier = 1.0
        elif approval_status == "rejected":
            return 0.0  # Rejected patterns should never be used
        else:
            status_multiplier = 0.6  # Unknown status - lower confidence

        # Municipality specificity bonus
        municipality_bonus = 0.1 if municipality else 0.0

        # Replicability adjustment
        replicability_multiplier = 1.0 if replicable else 0.85

        # Approval speed bonus (fast approval = higher confidence)
        speed_bonus = {
            "fast": 0.1,      # Approved quickly = very clear compliance
            "standard": 0.05,
            "slow": 0.0,      # Slow approval = borderline case
            "unknown": 0.0
        }.get(approval_speed, 0.0)

        # Calculate final confidence
        confidence = (base_confidence * status_multiplier * replicability_multiplier) + \
                     municipality_bonus + speed_bonus

        # Ensure confidence is between 0.0 and 1.0
        return min(max(confidence, 0.0), 1.0)

    def calculate_updated_confidence(
        self,
        current_confidence: float,
        confirmations: int,
        rejections: int = 0,
        age_days: int = 0
    ) -> float:
        """
        Update confidence score based on new evidence

        Args:
            current_confidence: Current confidence score
            confirmations: Number of times pattern has been confirmed
            rejections: Number of times pattern failed
            age_days: Days since pattern was first learned

        Returns:
            Updated confidence score
        """
        # Confirmation boost (diminishing returns)
        # First confirmation: +0.10, second: +0.07, third: +0.05, etc.
        confirmation_boost = sum([0.1 / (i + 1) for i in range(confirmations)])

        # Rejection penalty
        rejection_penalty = rejections * 0.15

        # Temporal decay (very slow - 1% per 90 days)
        decay_factor = 1.0 - (age_days / 9000)
        decay_factor = max(decay_factor, 0.8)  # Never decay below 80% of original

        # Calculate updated confidence
        updated = (current_confidence + confirmation_boost - rejection_penalty) * decay_factor

        # Ensure confidence is between 0.0 and 1.0
        return min(max(updated, 0.0), 1.0)

    def calculate_approval_pattern_confidence(
        self,
        approval_data: Dict,
        municipality: str,
        pattern_type: str  # "recommended_pattern" or "successful_element"
    ) -> tuple[float, Dict]:
        """
        Calculate confidence for patterns extracted from approval documents

        Args:
            approval_data: Approval document data
            municipality: Municipality name
            pattern_type: Type of pattern being scored

        Returns:
            Tuple of (confidence_score, calculation_breakdown)
            - confidence_score: Float between 0.0 and 1.0
            - calculation_breakdown: Dict explaining how score was calculated
        """
        # Base confidence for approval patterns
        base_confidence = 0.70

        # Municipality-specific bonus
        municipality_bonus = 0.08 if municipality else 0.0

        # Approval speed bonus (ADDITIVE not multiplicative to avoid exceeding 1.0)
        speed = approval_data.get('approval_speed', 'unknown')
        speed_bonus = {
            "fast": 0.12,      # Very clear pattern
            "normal": 0.06,    # Standard approval (parser might return "normal")
            "standard": 0.06,  # Standard approval
            "slow": 0.0,       # Borderline - might not always work
            "unknown": 0.03    # Give small benefit of doubt
        }.get(speed, 0.03)

        # Pattern type bonus
        if pattern_type == "recommended_pattern":
            # These are explicit recommendations extracted from approval
            type_bonus = 0.08
            type_explanation = "explicit recommendation"
        elif pattern_type == "successful_element":
            # These are observed successful aspects
            type_bonus = 0.04
            type_explanation = "successful element"
        else:
            type_bonus = 0.0
            type_explanation = "generic pattern"

        # Calculate final confidence (ADDITIVE to stay under 1.0)
        confidence = base_confidence + municipality_bonus + speed_bonus + type_bonus

        # Ensure between 0.0 and 1.0
        final_confidence = min(max(confidence, 0.0), 1.0)

        # Build calculation breakdown for transparency
        breakdown = {
            "base": round(base_confidence, 2),
            "municipality_bonus": round(municipality_bonus, 2),
            "municipality": municipality if municipality else "none",
            "speed_bonus": round(speed_bonus, 2),
            "approval_speed": speed,
            "type_bonus": round(type_bonus, 2),
            "pattern_type": type_explanation,
            "calculation": f"Base: {base_confidence:.2f} + Municipality: {municipality_bonus:.2f} + Speed: {speed_bonus:.2f} ({speed}) + Type: {type_bonus:.2f} ({type_explanation}) = {final_confidence:.2f}",
            "calculation_simple": f"{base_confidence:.2f} + {municipality_bonus:.2f} + {speed_bonus:.2f} + {type_bonus:.2f} = {final_confidence:.2f}"
        }

        return final_confidence, breakdown

    def calculate_rejection_pattern_confidence(
        self,
        rejection_data: Dict,
        severity: str  # "critical", "major", "minor"
    ) -> float:
        """
        Calculate confidence for rejection patterns (what to avoid)

        For rejection patterns, confidence = 0.0 means "never use this"
        But we track severity in metadata

        Args:
            rejection_data: Rejection document data
            severity: Severity level of the issue

        Returns:
            Always 0.0 for rejection patterns (metadata tracks severity)
        """
        # Rejection patterns always have 0.0 confidence
        # This ensures they're never used in generation
        # Severity is tracked separately in metadata for analytics
        return 0.0

    def get_confidence_category(self, confidence: float) -> str:
        """
        Categorize confidence score for reporting

        Args:
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            Category string
        """
        if confidence >= 0.85:
            return "very_high"
        elif confidence >= 0.75:
            return "high"
        elif confidence >= 0.60:
            return "medium"
        elif confidence >= 0.40:
            return "low"
        else:
            return "very_low"

    def record_confirmation(self, pattern_id: str):
        """
        Record that a pattern has been confirmed (used successfully)

        Args:
            pattern_id: Unique identifier for the pattern
        """
        self.confirmation_counts[pattern_id] = self.confirmation_counts.get(pattern_id, 0) + 1

    def get_confirmation_count(self, pattern_id: str) -> int:
        """
        Get number of confirmations for a pattern

        Args:
            pattern_id: Unique identifier for the pattern

        Returns:
            Number of confirmations
        """
        return self.confirmation_counts.get(pattern_id, 0)


# Example usage and expected confidence ranges:
"""
EXPECTED CONFIDENCE RANGES:

Very High (0.85-1.0):
- BR18 regulations: 0.90
- Patterns confirmed 5+ times: 0.88-0.95
- Fast-approved municipality-specific patterns: 0.85-0.90

High (0.75-0.84):
- Initial approval feedback patterns: 0.75-0.80
- Patterns confirmed 2-3 times: 0.78-0.82
- Municipality-specific golden records: 0.77-0.83

Medium (0.60-0.74):
- Approved example document extracts: 0.65-0.70
- General insights (no municipality): 0.60-0.68
- Patterns confirmed once: 0.62-0.70

Low (0.40-0.59):
- Unknown approval status: 0.45-0.55
- Non-replicable patterns: 0.40-0.50
- Patterns with slow approval: 0.48-0.58

Very Low/Rejected (0.0-0.39):
- Rejected patterns: 0.0 (never use)
- Patterns with multiple failures: 0.10-0.30
"""
