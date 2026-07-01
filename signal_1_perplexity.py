"""
Signal 1: Perplexity Analysis

Measures how predictable text is to a pre-trained language model (GPT-2).
Lower perplexity indicates AI-like patterns (predictable vocabulary).
Higher perplexity indicates human-like patterns (unexpected word choices).

This signal forms 60% of the final classification confidence.
"""

import math
import logging
from typing import Tuple
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel

logger = logging.getLogger(__name__)


class PerplexityAnalyzer:
    """
    Analyzes text perplexity using a pre-trained GPT-2 model.

    Perplexity measures how "surprised" a language model is by the text.
    Formula: perplexity = exp(average negative log likelihood)

    Normalization: We map raw perplexity to a 0-1 scale where:
    - 0 = AI-like (very predictable, low perplexity)
    - 1 = human-like (unpredictable, high perplexity)
    """

    def __init__(self):
        """Initialize GPT-2 model and tokenizer."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = GPT2LMHeadModel.from_pretrained("gpt2").to(self.device)
        self.model.eval()
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

        # Constants for normalization
        # Empirical bounds from typical text samples
        self.min_perplexity = 10.0  # Very predictable AI text
        self.max_perplexity = 200.0  # Very unpredictable human text

    def calculate_perplexity(self, text: str) -> float:
        """
        Calculate normalized perplexity score for input text.

        Args:
            text: The input text to analyze.

        Returns:
            A float between 0 and 1 where:
            - 0.0 = AI-like (predictable)
            - 1.0 = human-like (unpredictable)
            - Values outside [0, 1] are clamped to that range

        Raises:
            ValueError: If text is empty or None.
        """
        # Input validation
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string.")

        text = text.strip()

        # Handle very short text (edge case)
        if len(text.split()) < 3:
            logger.warning(f"Text is very short ({len(text.split())} words). Perplexity may be unreliable.")
            # Return neutral score for very short text
            return 0.5

        try:
            # Tokenize input
            encodings = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            input_ids = encodings.input_ids.to(self.device)

            # Calculate loss (don't compute gradients)
            with torch.no_grad():
                outputs = self.model(input_ids, labels=input_ids)
                loss = outputs.loss

            # Perplexity = exp(loss)
            raw_perplexity = math.exp(loss.item())

            # Normalize to 0-1 scale using log scale for better discrimination
            # Use log-scale normalization: log_perplexity = log(raw_perplexity)
            log_min = math.log(self.min_perplexity)
            log_max = math.log(self.max_perplexity)
            log_perplexity = math.log(raw_perplexity)

            # Clamp log-perplexity to reasonable bounds
            log_perplexity = max(log_min, min(log_max, log_perplexity))

            # Normalize to [0, 1]: higher perplexity = higher score (more human-like)
            normalized_score = (log_perplexity - log_min) / (log_max - log_min)

            # Clamp to [0, 1] range
            normalized_score = max(0.0, min(1.0, normalized_score))

            logger.info(f"Text perplexity: {raw_perplexity:.2f}, normalized score: {normalized_score:.3f}")
            return normalized_score

        except Exception as e:
            logger.error(f"Error calculating perplexity: {str(e)}")
            # Return neutral score on error
            return 0.5


# Module-level singleton for efficiency
_analyzer = None


def get_analyzer() -> PerplexityAnalyzer:
    """Get or create the global PerplexityAnalyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = PerplexityAnalyzer()
    return _analyzer


def calculate_perplexity(text: str) -> float:
    """
    Calculate normalized perplexity score for input text.

    Convenience function that uses a global analyzer instance.

    Args:
        text: The input text to analyze.

    Returns:
        A float between 0 and 1 where:
        - 0.0 = AI-like (predictable)
        - 1.0 = human-like (unpredictable)

    Raises:
        ValueError: If text is empty or None.
    """
    analyzer = get_analyzer()
    return analyzer.calculate_perplexity(text)


if __name__ == "__main__":
    # Simple test
    analyzer = get_analyzer()

    ai_text = "The quick brown fox jumps over the lazy dog. The cat sat on the mat. The bird flew in the sky."
    human_text = "Honestly, I think that whole situation was absolutely bonkers. My friend Sarah called me at 3am—literally THREE IN THE MORNING—just to tell me she'd adopted a capybara. A CAPYBARA! Who does that?"

    print(f"AI-like text score: {analyzer.calculate_perplexity(ai_text):.3f}")
    print(f"Human-like text score: {analyzer.calculate_perplexity(human_text):.3f}")
