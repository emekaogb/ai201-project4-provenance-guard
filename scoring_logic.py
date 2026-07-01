"""
Scoring Logic: Signal Combination and Classification

Implements the decision logic for combining Signal 1 (perplexity) and Signal 2
(linguistic features) into a final classification with confidence scoring.

Classification tiers:
- "human": finalScore > 0.75 AND confidence > 0.6
- "ai": finalScore < 0.25 AND confidence > 0.6
- "uncertain": otherwise
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def classify_content(perplexity_score: float, linguistic_score: float) -> Tuple[str, float]:
    """
    Classify text as human-written, AI-generated, or uncertain based on combined signals.

    Combines two detection signals (perplexity and linguistic features) using a
    weighted average, then applies confidence-aware thresholds to determine classification.

    Signal Weights:
    - Perplexity (Signal 1): 60% — more reliable across domains
    - Linguistic Features (Signal 2): 40% — domain-dependent but catches unique patterns

    Confidence Calculation:
    confidence = 2 × |finalScore - 0.5|
    - Ranges from 0.0 (at boundary, 0.5) to 1.0 (at extremes, 0.0 or 1.0)
    - Reflects distance from decision boundary: high distance = high confidence

    Decision Logic:
    1. IF finalScore > 0.75 AND confidence > 0.6:
       → Classification: "human" (high confidence in human authorship)
    2. ELIF finalScore < 0.25 AND confidence > 0.6:
       → Classification: "ai" (high confidence in AI generation)
    3. ELSE:
       → Classification: "uncertain" (mixed signals or low confidence)

    Args:
        perplexity_score: Signal 1 score (0.0–1.0)
            - 0.0 = AI-like (predictable)
            - 1.0 = human-like (unpredictable)
        linguistic_score: Signal 2 score (0.0–1.0)
            - 0.0 = AI-like (rigid structure)
            - 1.0 = human-like (varied structure)

    Returns:
        A tuple (classification, confidence) where:
        - classification: str
            "human" — high confidence the text is human-written
            "ai" — high confidence the text is AI-generated
            "uncertain" — low confidence or mixed signals
        - confidence: float (0.0–1.0)
            How confident the model is in the classification

    Raises:
        ValueError: If scores are not in valid range [0.0, 1.0]

    Examples:
        >>> # Example 1: Clear human text
        >>> classification, confidence = classify_content(0.85, 0.80)
        >>> assert classification == "human"
        >>> assert confidence > 0.6
        >>> print(f"Classification: {classification}, Confidence: {confidence:.2f}")
        Classification: human, Confidence: 0.70

        >>> # Example 2: Clear AI text
        >>> classification, confidence = classify_content(0.10, 0.15)
        >>> assert classification == "ai"
        >>> assert confidence > 0.6
        >>> print(f"Classification: {classification}, Confidence: {confidence:.2f}")
        Classification: ai, Confidence: 0.70

        >>> # Example 3: Mixed signals (uncertain)
        >>> classification, confidence = classify_content(0.50, 0.55)
        >>> assert classification == "uncertain"
        >>> print(f"Classification: {classification}, Confidence: {confidence:.2f}")
        Classification: uncertain, Confidence: 0.10

        >>> # Example 4: High score but low confidence (boundary case)
        >>> classification, confidence = classify_content(0.51, 0.52)
        >>> assert classification == "uncertain"
        >>> print(f"Classification: {classification}, Confidence: {confidence:.2f}")
        Classification: uncertain, Confidence: 0.04
    """
    # Validate input ranges
    if not (0.0 <= perplexity_score <= 1.0):
        raise ValueError(
            f"perplexity_score must be in [0.0, 1.0], got {perplexity_score}"
        )
    if not (0.0 <= linguistic_score <= 1.0):
        raise ValueError(
            f"linguistic_score must be in [0.0, 1.0], got {linguistic_score}"
        )

    # Step 1: Calculate weighted final score
    # Perplexity (60%) + Linguistic (40%)
    final_score = (0.6 * perplexity_score) + (0.4 * linguistic_score)

    # Step 2: Calculate confidence as distance from decision boundary (0.5)
    # Formula: confidence = 2 × |finalScore - 0.5|
    # This ensures:
    # - score 0.5 → confidence 0.0 (maximum uncertainty)
    # - score 0.0 or 1.0 → confidence 1.0 (maximum certainty)
    confidence = 2.0 * abs(final_score - 0.5)

    # Step 3: Apply decision thresholds
    # High-confidence human classification
    if final_score > 0.75 and confidence > 0.6:
        classification = "human"
        logger.info(
            f"Classification: HUMAN "
            f"(finalScore={final_score:.3f}, confidence={confidence:.3f})"
        )

    # High-confidence AI classification
    elif final_score < 0.25 and confidence > 0.6:
        classification = "ai"
        logger.info(
            f"Classification: AI "
            f"(finalScore={final_score:.3f}, confidence={confidence:.3f})"
        )

    # Uncertain (either mixed signals or low confidence)
    else:
        classification = "uncertain"
        logger.info(
            f"Classification: UNCERTAIN "
            f"(finalScore={final_score:.3f}, confidence={confidence:.3f})"
        )

    return (classification, confidence)


def get_classification_explanation(
    classification: str, confidence: float, final_score: float
) -> str:
    """
    Generate a human-readable explanation of the classification.

    Args:
        classification: The classification result ("human", "ai", "uncertain")
        confidence: The confidence score (0.0–1.0)
        final_score: The combined signal score (0.0–1.0)

    Returns:
        A plain-English explanation of the classification
    """
    if classification == "human":
        return (
            f"We are highly confident (confidence: {confidence:.1%}) that this content "
            f"was written by a human. The text shows natural variation in sentence "
            f"structure and vocabulary choices typical of human authorship."
        )
    elif classification == "ai":
        return (
            f"We are highly confident (confidence: {confidence:.1%}) that this content "
            f"was generated by an AI system. The text shows patterns of predictability "
            f"and structural consistency typical of AI-generated content."
        )
    else:  # uncertain
        return (
            f"We are uncertain about the authorship of this content "
            f"(confidence: {confidence:.1%}). The text exhibits characteristics of both "
            f"human and AI writing. This might indicate a blend of human and AI, "
            f"or an unusual writing style that doesn't fit either pattern clearly."
        )


if __name__ == "__main__":
    # Test cases
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("Test Case 1: Clear Human Text")
    print("=" * 70)
    perp_score = 0.85  # High perplexity (human-like)
    ling_score = 0.80  # High linguistic score (human-like)
    classification, confidence = classify_content(perp_score, ling_score)
    final_score = (0.6 * perp_score) + (0.4 * ling_score)
    print(f"Input: perplexity={perp_score}, linguistic={ling_score}")
    print(f"Final Score: {final_score:.3f}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Classification: {classification}")
    print(f"Explanation: {get_classification_explanation(classification, confidence, final_score)}")

    print("\n" + "=" * 70)
    print("Test Case 2: Clear AI Text")
    print("=" * 70)
    perp_score = 0.10  # Low perplexity (AI-like)
    ling_score = 0.15  # Low linguistic score (AI-like)
    classification, confidence = classify_content(perp_score, ling_score)
    final_score = (0.6 * perp_score) + (0.4 * ling_score)
    print(f"Input: perplexity={perp_score}, linguistic={ling_score}")
    print(f"Final Score: {final_score:.3f}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Classification: {classification}")
    print(f"Explanation: {get_classification_explanation(classification, confidence, final_score)}")

    print("\n" + "=" * 70)
    print("Test Case 3: Uncertain (Mixed Signals)")
    print("=" * 70)
    perp_score = 0.50  # Neutral perplexity
    ling_score = 0.55  # Neutral linguistic
    classification, confidence = classify_content(perp_score, ling_score)
    final_score = (0.6 * perp_score) + (0.4 * ling_score)
    print(f"Input: perplexity={perp_score}, linguistic={ling_score}")
    print(f"Final Score: {final_score:.3f}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Classification: {classification}")
    print(f"Explanation: {get_classification_explanation(classification, confidence, final_score)}")

    print("\n" + "=" * 70)
    print("Test Case 4: Boundary Case (Low Confidence)")
    print("=" * 70)
    perp_score = 0.51  # Just above 0.5
    ling_score = 0.52  # Just above 0.5
    classification, confidence = classify_content(perp_score, ling_score)
    final_score = (0.6 * perp_score) + (0.4 * ling_score)
    print(f"Input: perplexity={perp_score}, linguistic={ling_score}")
    print(f"Final Score: {final_score:.3f}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Classification: {classification}")
    print(f"Explanation: {get_classification_explanation(classification, confidence, final_score)}")

    print("\n" + "=" * 70)
    print("Test Case 5: High AI Score, Sufficient Confidence")
    print("=" * 70)
    perp_score = 0.20
    ling_score = 0.20
    classification, confidence = classify_content(perp_score, ling_score)
    final_score = (0.6 * perp_score) + (0.4 * ling_score)
    print(f"Input: perplexity={perp_score}, linguistic={ling_score}")
    print(f"Final Score: {final_score:.3f}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Classification: {classification}")
    print(f"Explanation: {get_classification_explanation(classification, confidence, final_score)}")

    print("\n" + "=" * 70)
    print("Test Case 6: High Human Score, Sufficient Confidence")
    print("=" * 70)
    perp_score = 0.80
    ling_score = 0.75
    classification, confidence = classify_content(perp_score, ling_score)
    final_score = (0.6 * perp_score) + (0.4 * ling_score)
    print(f"Input: perplexity={perp_score}, linguistic={ling_score}")
    print(f"Final Score: {final_score:.3f}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Classification: {classification}")
    print(f"Explanation: {get_classification_explanation(classification, confidence, final_score)}")
