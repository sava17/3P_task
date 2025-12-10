from google import genai
from google.genai import types
from typing import List, Dict
import json
import uuid
from datetime import datetime
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from src.models import (
    MunicipalityFeedback,
    LearningInsight,
    DocumentType,
    KnowledgeChunk
)

class FeedbackAnalyzer:
    """
    Analyze municipality feedback using Gemini to extract learning insights.
    This is the core of the continuous learning system.
    """

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze_feedback_batch(
        self,
        feedback_batch: List[MunicipalityFeedback],
        document_type: DocumentType
    ) -> List[LearningInsight]:
        """
        Analyze a batch of feedback to extract patterns and learning insights

        Args:
            feedback_batch: List of municipality feedback
            document_type: Type of document being analyzed

        Returns:
            List of extracted learning insights
        """
        # Group feedback by municipality
        by_municipality = {}
        for feedback in feedback_batch:
            if feedback.municipality not in by_municipality:
                by_municipality[feedback.municipality] = []
            by_municipality[feedback.municipality].append(feedback)

        all_insights = []

        for municipality, feedbacks in by_municipality.items():
            insights = self._analyze_municipality_feedback(
                municipality,
                feedbacks,
                document_type
            )
            all_insights.extend(insights)

        return all_insights

    def _analyze_municipality_feedback(
        self,
        municipality: str,
        feedbacks: List[MunicipalityFeedback],
        document_type: DocumentType
    ) -> List[LearningInsight]:
        """
        Analyze feedback for a specific municipality and document type

        Args:
            municipality: Municipality name
            feedbacks: Feedback from this municipality
            document_type: Document type

        Returns:
            List of learning insights
        """
        # Prepare feedback summary for analysis
        approved = [f for f in feedbacks if f.approved]
        rejected = [f for f in feedbacks if not f.approved]

        feedback_summary = f"""Municipality: {municipality}
Document Type: {document_type.value}
Total Submissions: {len(feedbacks)}
Approved: {len(approved)}
Rejected: {len(rejected)}
Approval Rate: {len(approved)/len(feedbacks)*100:.1f}%

REJECTED DOCUMENTS ANALYSIS:
"""
        for i, feedback in enumerate(rejected, 1):
            feedback_summary += f"\n{i}. Document ID: {feedback.document_id}\n"
            feedback_summary += f"   Reasons: {', '.join(feedback.rejection_reasons)}\n"
            if feedback.feedback_text:
                feedback_summary += f"   Feedback: {feedback.feedback_text}\n"
            if feedback.suggestions:
                feedback_summary += f"   Suggestions: {', '.join(feedback.suggestions)}\n"

        feedback_summary += f"\nAPPROVED DOCUMENTS (for positive patterns):\n"
        for i, feedback in enumerate(approved[:5], 1):  # Sample first 5
            feedback_summary += f"{i}. Document ID: {feedback.document_id}\n"
            if feedback.feedback_text:
                feedback_summary += f"   Positive notes: {feedback.feedback_text}\n"

        # Use Gemini to analyze and extract patterns
        prompt = f"""You are an expert in Danish BR18 building regulations and municipality approval processes.

Analyze the following feedback data from {municipality} for {document_type.value} documents:

{feedback_summary}

Extract specific, actionable learning insights that can improve future document generation. Focus on:

1. **Rejection Patterns**: Common reasons for rejection that appear across multiple documents
2. **Municipality-Specific Requirements**: Unique requirements or preferences of {municipality}
3. **Approval Patterns**: What makes documents get approved by this municipality
4. **Technical Details**: Specific paragraph references, formatting, or content requirements
5. **Language and Terminology**: Preferred Danish terms or phrasing

For each insight, provide:
- A clear pattern description
- Specific examples from the feedback
- Confidence score (0.0-1.0) based on how many times the pattern appears
- Actionable recommendation for future document generation

Return your analysis as a JSON array of insights:
[
  {{
    "pattern_description": "Clear description of the pattern",
    "examples": ["Example 1 from feedback", "Example 2 from feedback"],
    "confidence_score": 0.85,
    "recommendation": "Specific action to take when generating future documents"
  }},
  ...
]

Return ONLY the JSON array, no other text."""

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Low for factual analysis
                    max_output_tokens=65536,  # Max output - prevent cutoffs
                )
            )

            # Parse JSON response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            insights_data = json.loads(text.strip())

            # Convert to LearningInsight objects
            insights = []
            for insight_dict in insights_data:
                insight = LearningInsight(
                    insight_id=str(uuid.uuid4()),
                    municipality=municipality,
                    document_type=document_type,
                    pattern_description=insight_dict.get("pattern_description", ""),
                    examples=insight_dict.get("examples", []),
                    confidence_score=insight_dict.get("confidence_score", 0.5)
                )
                insights.append(insight)
                print(f"Extracted insight: {insight.pattern_description[:60]}...")

            return insights

        except json.JSONDecodeError as e:
            print(f"Failed to parse insights JSON: {e}")
            print(f"Response was: {response.text[:200]}")
            return []

    def generate_knowledge_chunks_from_insights(
        self,
        insights: List[LearningInsight]
    ) -> List[KnowledgeChunk]:
        """
        Convert learning insights into knowledge chunks for RAG system

        Args:
            insights: List of learning insights

        Returns:
            List of knowledge chunks to add to vector store
        """
        chunks = []

        for insight in insights:
            # Create a rich context chunk from the insight
            content = f"""Municipality: {insight.municipality}
Document Type: {insight.document_type.value}
Requirement Pattern (Confidence: {insight.confidence_score:.0%}):

{insight.pattern_description}

Examples from approved/rejected documents:
{chr(10).join(f'- {ex}' for ex in insight.examples)}

Applied successfully: {insight.applied_count} times
Success rate: {insight.success_rate:.0%}
"""

            chunk = KnowledgeChunk(
                chunk_id=str(uuid.uuid4()),
                source_type="insight",
                source_reference=insight.insight_id,
                municipality=insight.municipality,
                document_type=insight.document_type,
                content=content,
                metadata={
                    "confidence_score": insight.confidence_score,
                    "applied_count": insight.applied_count,
                    "success_rate": insight.success_rate,
                    "pattern_description": insight.pattern_description
                }
            )

            chunks.append(chunk)

        return chunks

    def evaluate_document_quality(
        self,
        generated_content: str,
        document_type: DocumentType,
        project_details: Dict
    ) -> Dict:
        """
        Use Gemini to evaluate generated document quality before submission

        Args:
            generated_content: The generated document text
            document_type: Type of document
            project_details: Project information

        Returns:
            Quality evaluation with score and suggestions
        """
        prompt = f"""You are a BR18 fire safety expert evaluating a {document_type.value} document.

PROJECT CONTEXT:
{json.dumps(project_details, indent=2)}

GENERATED DOCUMENT:
{generated_content}

Evaluate this document for:
1. Completeness (all required sections present)
2. BR18 compliance (proper paragraph references)
3. Technical accuracy (fire classifications, materials, distances)
4. Language quality (proper Danish terminology)
5. Formatting (structure, clarity, professional presentation)

Provide:
- Overall quality score (0-100)
- Strengths (what's done well)
- Weaknesses (what needs improvement)
- Specific recommendations for improvement
- Risk assessment (likelihood of municipal rejection)

Return as JSON:
{{
  "quality_score": 85,
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "rejection_risk": "low/medium/high",
  "missing_elements": ["element 1 if any"]
}}"""

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=65536,  # Max output - prevent cutoffs
                )
            )

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text.strip())

        except json.JSONDecodeError:
            return {
                "quality_score": 50,
                "error": "Failed to parse evaluation",
                "raw_response": response.text
            }
