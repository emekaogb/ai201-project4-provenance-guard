"""
Test suite for Signal 1 and Signal 2 detection functions.

Tests signals independently and together to verify:
1. Each signal behaves as expected on known inputs
2. Signals agree/disagree appropriately
3. Confidence scoring produces meaningful outputs
4. Classifications match intuition
"""

from signal_1_perplexity import calculate_perplexity

# Test inputs with expected classifications
TEST_CASES = {
    "clearly_ai": {
        "text": """Artificial intelligence represents a transformative paradigm shift in modern society.
It is important to note that while the benefits of AI are numerous, it is equally
essential to consider the ethical implications. Furthermore, stakeholders across
various sectors must collaborate to ensure responsible deployment.""",
        "expected": "ai",
        "reason": "Formal, uniform sentences, predictable vocabulary, discourse markers",
    },
    "clearly_human": {
        "text": """ok so i finally tried that new ramen place downtown and honestly?
underwhelming. the broth was fine but they put WAY too much sodium in it and
i was thirsty for like three hours after. my friend got the spicy version and
said it was better. probably won't go back unless someone drags me there""",
        "expected": "human",
        "reason": "Casual, varied sentence length, informal vocabulary, natural punctuation",
    },
    "formal_human": {
        "text": """The relationship between monetary policy and asset price inflation has been
extensively studied in the literature. Central banks face a fundamental tension
between their mandate for price stability and the unintended consequences of
prolonged low interest rates on equity and real estate valuations.""",
        "expected": "uncertain",
        "reason": "Formal human writing - perplexity may score as AI, linguistic may catch human patterns",
    },
    "lightly_edited_ai": {
        "text": """I've been thinking a lot about remote work lately. There are genuine tradeoffs —
flexibility and no commute on one side, isolation and blurred work-life boundaries
on the other. Studies show productivity varies widely by individual and role type.""",
        "expected": "uncertain",
        "reason": "Borderline - may score mid-range, signals might disagree",
    },
}


def test_signal_1_independently():
    """Test Signal 1 (Perplexity) on all test cases."""
    print("\n" + "=" * 80)
    print("SIGNAL 1: PERPLEXITY ANALYSIS")
    print("=" * 80)
    print("(Lower score = AI-like, Higher score = Human-like)\n")

    for name, case in TEST_CASES.items():
        text = case["text"]
        expected = case["expected"]
        reason = case["reason"]

        try:
            score = calculate_perplexity(text)
            print(f"Test: {name}")
            print(f"Expected: {expected}")
            print(f"Reason: {reason}")
            print(f"Perplexity Score: {score:.3f}")

            # Simple interpretation
            if score < 0.25:
                interpretation = "AI-like"
            elif score > 0.75:
                interpretation = "Human-like"
            else:
                interpretation = "Ambiguous"
            print(f"Interpretation: {interpretation}")
            print()

        except Exception as e:
            print(f"Test: {name} - ERROR: {str(e)}\n")


def test_signal_2_independently():
    """Test Signal 2 (Linguistic Features) on all test cases.

    Note: This function will be available after Signal 2 is implemented.
    """
    try:
        from signal_2_linguistic_features import calculate_linguistic_score

        print("\n" + "=" * 80)
        print("SIGNAL 2: LINGUISTIC FEATURES ANALYSIS")
        print("=" * 80)
        print("(Lower score = AI-like, Higher score = Human-like)\n")

        for name, case in TEST_CASES.items():
            text = case["text"]
            expected = case["expected"]
            reason = case["reason"]

            try:
                score = calculate_linguistic_score(text)
                print(f"Test: {name}")
                print(f"Expected: {expected}")
                print(f"Reason: {reason}")
                print(f"Linguistic Score: {score:.3f}")

                # Simple interpretation
                if score < 0.25:
                    interpretation = "AI-like"
                elif score > 0.75:
                    interpretation = "Human-like"
                else:
                    interpretation = "Ambiguous"
                print(f"Interpretation: {interpretation}")
                print()

            except Exception as e:
                print(f"Test: {name} - ERROR: {str(e)}\n")

    except ImportError:
        print("\n[Signal 2 not yet implemented]\n")


def test_signal_agreement():
    """Test how Signals 1 and 2 agree/disagree on each case."""
    try:
        from signal_2_linguistic_features import calculate_linguistic_score

        print("\n" + "=" * 80)
        print("SIGNAL AGREEMENT ANALYSIS")
        print("=" * 80)
        print("(Do signals agree on each input?)\n")

        for name, case in TEST_CASES.items():
            text = case["text"]

            try:
                sig1_score = calculate_perplexity(text)
                sig2_score = calculate_linguistic_score(text)

                # Classify each signal independently
                sig1_class = "ai" if sig1_score < 0.25 else "human" if sig1_score > 0.75 else "uncertain"
                sig2_class = "ai" if sig2_score < 0.25 else "human" if sig2_score > 0.75 else "uncertain"

                agreement = "✓ AGREE" if sig1_class == sig2_class else "✗ DISAGREE"

                print(f"Test: {name}")
                print(f"  Signal 1 (Perplexity): {sig1_score:.3f} → {sig1_class}")
                print(f"  Signal 2 (Linguistic): {sig2_score:.3f} → {sig2_class}")
                print(f"  {agreement}")
                print()

            except Exception as e:
                print(f"Test: {name} - ERROR: {str(e)}\n")

    except ImportError:
        print("\n[Signal 2 not yet implemented]\n")


def test_combined_scoring():
    """Test the combined confidence scoring with both signals."""
    try:
        from signal_2_linguistic_features import calculate_linguistic_score
        from scoring_logic import classify_content

        print("\n" + "=" * 80)
        print("COMBINED CONFIDENCE SCORING")
        print("=" * 80)
        print("(finalScore = 0.6×Perplexity + 0.4×Linguistic)")
        print("(confidence = 2 × |finalScore - 0.5|)\n")

        for name, case in TEST_CASES.items():
            text = case["text"]
            expected = case["expected"]

            try:
                sig1_score = calculate_perplexity(text)
                sig2_score = calculate_linguistic_score(text)

                classification, confidence = classify_content(sig1_score, sig2_score)

                # Calculate final score for inspection
                final_score = (0.6 * sig1_score) + (0.4 * sig2_score)

                match = "✓ MATCH" if classification == expected else "✗ MISMATCH"

                print(f"Test: {name}")
                print(f"  Expected: {expected}")
                print(f"  Signal 1: {sig1_score:.3f}")
                print(f"  Signal 2: {sig2_score:.3f}")
                print(f"  Final Score: {final_score:.3f}")
                print(f"  Classification: {classification}")
                print(f"  Confidence: {confidence:.3f}")
                print(f"  {match}")
                print()

            except Exception as e:
                print(f"Test: {name} - ERROR: {str(e)}\n")

    except ImportError:
        print("\n[Signal 2 or scoring logic not yet implemented]\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PROVENANCE GUARD - SIGNAL TESTING SUITE")
    print("=" * 80)

    test_signal_1_independently()
    test_signal_2_independently()
    test_signal_agreement()
    test_combined_scoring()

    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)
