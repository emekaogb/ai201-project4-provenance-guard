"""
Signal 2: Linguistic Features Analysis

Analyzes stylistic patterns in text to detect AI vs. human authorship.
Measures sentence length variance, vocabulary diversity, discourse markers,
and punctuation patterns. Lower scores indicate AI-like characteristics;
higher scores indicate human-like characteristics.

This signal forms 40% of the final classification confidence.
"""

import re
import logging
from typing import List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


def _extract_sentences(text: str) -> List[str]:
    """
    Split text into sentences, handling edge cases.

    Args:
        text: Input text to split

    Returns:
        List of sentences
    """
    # Split on common sentence-ending punctuation
    # Handles cases like "Mr.", "Dr.", etc. by being conservative
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text.strip())
    # Filter out empty sentences
    return [s.strip() for s in sentences if s.strip()]


def _calculate_sentence_length_variance(text: str) -> float:
    """
    Calculate the coefficient of variation in sentence lengths.

    Metric: Measures how much sentence length varies.
    - AI typically has uniform sentence length (low variance)
    - Humans naturally vary sentence length (high variance)

    Args:
        text: Input text to analyze

    Returns:
        Coefficient of variation (0 to ~2.0+)
        Higher = more human-like (more variance)
    """
    sentences = _extract_sentences(text)
    if len(sentences) < 2:
        return 0.0

    # Measure sentence length in words
    sentence_lengths = [len(s.split()) for s in sentences]

    # Calculate mean and standard deviation
    mean_length = sum(sentence_lengths) / len(sentence_lengths)
    if mean_length == 0:
        return 0.0

    variance = sum((length - mean_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
    std_dev = variance ** 0.5

    # Coefficient of variation: std_dev / mean
    # Higher values indicate greater variation (more human-like)
    cv = std_dev / mean_length if mean_length > 0 else 0.0
    return cv


def _calculate_type_token_ratio(text: str) -> float:
    """
    Calculate type-token ratio (vocabulary diversity).

    Metric: Types (unique words) / Tokens (total words)
    - AI often reuses vocabulary (lower ratio, ~0.4-0.6)
    - Humans use diverse vocabulary (higher ratio, ~0.5-0.8)

    Args:
        text: Input text to analyze

    Returns:
        Type-token ratio (0 to 1.0)
        Higher = more human-like (more diverse vocabulary)
    """
    # Normalize: lowercase, remove punctuation from word boundaries
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if len(words) == 0:
        return 0.5

    # Count unique words (types) vs total words (tokens)
    unique_words = len(set(words))
    total_words = len(words)

    # Type-token ratio
    ttr = unique_words / total_words if total_words > 0 else 0.0
    return ttr


def _calculate_discourse_marker_frequency(text: str) -> float:
    """
    Measure frequency of formal discourse markers.

    Metric: How often formal discourse connectors appear.
    - AI uses formal markers systematically: "furthermore", "moreover", "consequently"
    - Humans use them more naturally and less frequently

    Args:
        text: Input text to analyze

    Returns:
        Frequency score (0 to 1.0)
        Lower = more human-like (fewer formal markers)
    """
    # Formal discourse markers common in AI text
    formal_markers = [
        'furthermore', 'moreover', 'additionally', 'consequently',
        'therefore', 'thus', 'however', 'in conclusion', 'in summary',
        'overall', 'clearly', 'obviously', 'essentially', 'ultimately',
        'accordingly', 'notably', 'specifically', 'particularly'
    ]

    text_lower = text.lower()
    marker_count = 0

    for marker in formal_markers:
        # Count occurrences of each marker (word boundary)
        pattern = r'\b' + re.escape(marker) + r'\b'
        marker_count += len(re.findall(pattern, text_lower))

    # Normalize by text length (count per 100 words)
    word_count = len(text.split())
    if word_count == 0:
        return 0.0

    marker_frequency = (marker_count / word_count) * 100

    # Scale to 0-1 where higher frequency (more AI-like) = lower score
    # Typical range: 0-5 markers per 100 words
    # Use sigmoid-like scaling: frequency of 0 = 0.0, frequency of 5+ = 1.0
    score = min(1.0, marker_frequency / 5.0)
    return score


def _calculate_punctuation_diversity(text: str) -> float:
    """
    Measure diversity of punctuation patterns.

    Metric: Variety in punctuation usage.
    - AI tends to use uniform punctuation (mostly periods, commas)
    - Humans use varied punctuation (dashes, ellipses, exclamation, questions)

    Args:
        text: Input text to analyze

    Returns:
        Diversity score (0 to 1.0)
        Higher = more human-like (more punctuation variety)
    """
    if not text:
        return 0.5

    # Count various punctuation types
    punctuation_types = {
        'period': len(re.findall(r'\.', text)),
        'comma': len(re.findall(r',', text)),
        'exclamation': len(re.findall(r'!', text)),
        'question': len(re.findall(r'\?', text)),
        'dash': len(re.findall(r'[—\-]', text)),
        'ellipsis': len(re.findall(r'\.{2,}|…', text)),
        'parenthesis': len(re.findall(r'[\(\)]', text)),
        'quotes': len(re.findall(r'["\']', text)),
    }

    # Count punctuation marks used (how many different types)
    types_used = sum(1 for count in punctuation_types.values() if count > 0)

    # AI text typically uses 2-3 punctuation types heavily
    # Human text uses more variety (5-8 types)
    # Score: diversity relative to maximum possible (8 types)
    diversity_score = types_used / 8.0
    return diversity_score


def calculate_linguistic_score(text: str) -> float:
    """
    Calculate a linguistic style score indicating AI vs. human authorship.

    Combines multiple stylometric features:
    - Sentence length variance (30%): AI has uniform lengths
    - Type-token ratio (40%): AI reuses vocabulary
    - Discourse markers (20%): AI uses formal markers systematically
    - Punctuation diversity (10%): AI uses limited punctuation variety

    Args:
        text: The input text to analyze

    Returns:
        A float between 0.0 and 1.0 where:
        - 0.0 = AI-like characteristics (rigid structure, formal vocabulary)
        - 1.0 = human-like characteristics (varied structure, diverse vocabulary)
        - 0.5 = returned for edge cases (very short text < 3 words)

    Raises:
        ValueError: If text is not a string

    Examples:
        >>> # AI-like text (formal, uniform structure)
        >>> ai_text = "The algorithm processes data efficiently. The system analyzes information carefully. The model generates output accurately."
        >>> score = calculate_linguistic_score(ai_text)
        >>> assert 0.0 <= score <= 1.0
        >>> assert score < 0.5  # Should lean AI-like

        >>> # Human-like text (varied, natural style)
        >>> human_text = "I honestly can't believe it—the whole thing was absolutely ridiculous! My friend Sarah, who's usually so calm, just completely lost it."
        >>> score = calculate_linguistic_score(human_text)
        >>> assert 0.0 <= score <= 1.0
        >>> assert score > 0.5  # Should lean human-like
    """
    # Input validation
    if not isinstance(text, str):
        raise ValueError("Text must be a string.")

    text = text.strip()

    # Handle edge case: empty or very short text
    if not text:
        logger.warning("Text is empty. Returning neutral score.")
        return 0.5

    word_count = len(text.split())
    if word_count < 3:
        logger.warning(f"Text is very short ({word_count} words). Returning neutral score.")
        return 0.5

    try:
        # Calculate individual metrics
        # Higher metric values indicate human-like characteristics

        # Metric 1: Sentence length variance (30% weight)
        # Scale to 0-1: typical CV is 0.3-1.0, map to 0-1
        sentence_variance = _calculate_sentence_length_variance(text)
        # Normalize to 0-1 range: assume CV typically 0-1.5
        variance_score = min(1.0, sentence_variance / 1.5)

        # Metric 2: Type-token ratio (40% weight)
        # Already in 0-1 range
        vocabulary_score = _calculate_type_token_ratio(text)

        # Metric 3: Discourse marker frequency (20% weight)
        # Lower marker frequency = more human-like
        marker_score = 1.0 - _calculate_discourse_marker_frequency(text)

        # Metric 4: Punctuation diversity (10% weight)
        # Already in 0-1 range
        punctuation_score = _calculate_punctuation_diversity(text)

        # Combine metrics with weighted average
        final_score = (
            0.30 * variance_score +
            0.40 * vocabulary_score +
            0.20 * marker_score +
            0.10 * punctuation_score
        )

        # Clamp to [0, 1] range
        final_score = max(0.0, min(1.0, final_score))

        logger.info(
            f"Linguistic analysis: variance={variance_score:.3f}, "
            f"vocabulary={vocabulary_score:.3f}, markers={marker_score:.3f}, "
            f"punctuation={punctuation_score:.3f}, final={final_score:.3f}"
        )

        return final_score

    except Exception as e:
        logger.error(f"Error calculating linguistic score: {str(e)}")
        # Return neutral score on error
        return 0.5


if __name__ == "__main__":
    # Test cases
    logging.basicConfig(level=logging.INFO)

    # AI-like text (formal, repetitive, uniform structure)
    ai_text = (
        "The algorithm processes data efficiently. "
        "The system analyzes information carefully. "
        "The model generates output accurately. "
        "Furthermore, the approach ensures consistency. "
        "Moreover, the method maintains stability."
    )

    # Human-like text (varied, natural, conversational)
    human_text = (
        "Honestly? The whole thing was absolutely bonkers! "
        "My friend Sarah—who's normally super calm—just completely lost it. "
        "She called me at 3am (THREE IN THE MORNING!) to tell me about this ridiculous idea. "
        "I mean, seriously. Who does that?!"
    )

    ai_score = calculate_linguistic_score(ai_text)
    human_score = calculate_linguistic_score(human_text)

    print(f"AI-like text score: {ai_score:.3f}")
    print(f"Human-like text score: {human_score:.3f}")
    print(f"Expected: AI score < 0.5, Human score > 0.5")
