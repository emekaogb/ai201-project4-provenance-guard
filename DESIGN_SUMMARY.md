# Provenance Guard Design Summary

## What Was Added to planning.md

### 1. Architecture Narrative: The Complete Journey

A text submission follows this **8-step path**:

1. **Rate Limiter** checks IP quota (100/hour)
2. **Input Validator** ensures text is 1-5000 characters, valid UTF-8
3. **Signal 1: Perplexity Analyzer** scores vocabulary predictability (0-1)
4. **Signal 2: Linguistic Feature Extractor** scores writing structure variation (0-1)
5. **Confidence Scorer** combines signals: `finalScore = (0.6 × perplexity) + (0.4 × linguistic)`
6. **Label Generator** outputs one of three variants (human/AI/uncertain)
7. **Audit Logger** records everything with full context
8. **HTTP Response** returns to user with submission ID and confidence score

**Key insight:** The confidence score (`2 × |finalScore - 0.5|`) ensures:
- Score 0.95 → confidence 0.90 (high confidence human)
- Score 0.50 → confidence 0.00 (complete uncertainty)
- Score 0.51 → confidence 0.02 (barely confident human)

This means the label is **meaningfully different** at different confidence levels.

---

### 2. Two Detection Signals with Blind Spots

#### Signal 1: Perplexity Analysis

**What it measures:** How "surprising" each word is to a pre-trained language model

**Why it differs:**
- AI produces low-perplexity text (predictable, follows high-probability paths)
- Humans produce high-perplexity text (varied vocabulary, unexpected word choices)

**Blind spots (what it CANNOT detect):**
1. Humans who write formally/mechanically (academics, lawyers, tax forms)
2. AI fine-tuned on human data (modern GPT variants)
3. Short text (<30 words, too high variance)
4. Non-English text (model calibration differs)
5. Domain-specific jargon (medical journals, legal documents)
6. Human-edited AI text (rewriting introduces perplexity variation)

#### Signal 2: Linguistic Feature Extraction

**What it measures:** Stylistic patterns (sentence length variance, vocabulary diversity, punctuation, discourse markers)

**Why it differs:**
- AI produces uniform sentence length, formal structure, consistent vocabulary
- Humans produce varied sentences, natural discourse, personal word choices

**Blind spots (what it CANNOT detect):**
1. Humans who write formally (researchers, lawyers, non-native speakers)
2. AI trained on informal data (ChatGPT on Reddit/Twitter data)
3. Heavily edited AI text (human revision introduces variation)
4. Code comments and technical proofs (naturally repetitive)
5. Short fragments (one sentence/paragraph has no variation)
6. Non-English text (discourse markers don't translate)
7. Transcribed speech (natural but not written)

**Why these two together?**
- **Orthogonal signals:** Perplexity = word-level surprise. Linguistics = sentence-level structure.
- **Reduce false positives:** If both signals agree (both high = human, both low = AI), confidence is high. If they disagree, confidence is lower, triggering "uncertain."

---

### 3. False Positive Scenario: How the System Protects Against Mistakes

**Scenario:** Maya writes a formal technical blog post (academic style, uniform sentences, formal vocabulary). Both signals suggest AI, but the system doesn't misclassify her.

**Why it doesn't fail:**
- Signal 1: 0.38 (predictable vocab)
- Signal 2: 0.35 (rigid structure)
- Combined score: 0.368
- **Confidence: 0.264 (LOW!)**
- **Classification: "uncertain"** (not "AI")
- **Label:** "? We're unsure about the authorship..."

**What happens next:**
- Maya clicks "Appeal" and submits: "This is my original blog post from June 2026"
- Appeal is logged, submission status updates to "under_review"
- Audit log shows: original scores, low confidence, and her appeal reasoning
- If a human reviewer examines it, they see all context and can make correct decision

**Design lesson:**
Low confidence saved Maya. Even though both signals pointed toward AI, the system said "uncertain," not "definitely AI." The transparency label was honest about uncertainty. The appeal mechanism provided recourse.

---

### 4. Complete API Surface: All Endpoints and Contracts

#### Submission Flow

**POST /api/content/submit**
- Input: `{ content, contentId?, creatorId? }`
- Output: `{ submissionId, classification, confidenceScore, signals, transparencyLabel, timestamp }`
- Errors: 400 (invalid input), 429 (rate limit)
- Rate limit headers: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

**GET /api/submissions/{submissionId}**
- Retrieve previous submission and result
- Output: full submission details with all scores

#### Appeal Flow

**POST /api/appeals/submit**
- Input: `{ submissionId, creatorId, reasoning, evidence? }`
- Output: `{ appealId, submissionId, status: "under_review", submittedAt }`
- Errors: 400 (invalid), 404 (submission not found), 409 (appeal exists)

**GET /api/appeals/{appealId}**
- Check appeal status
- Output: `{ appealId, submissionId, status, submittedAt, resolvedAt?, resolution? }`

#### Audit Log

**GET /api/log**
- Query params: `limit`, `offset`, `classification`, `from`, `to`
- Output: paginated list of log entries with all signal scores and appeal info

**GET /api/log/text**
- Same data as JSON, but formatted as human-readable text
- Used in README to show 3+ example log entries

---

### 5. System Diagrams: Two Main Flows

#### Diagram 1: Submission Flow

```
Text Input
    ↓
[Rate Limiter] → Pass/Fail (429)
    ↓
[Input Validator] → Pass/Fail (400)
    ↓
[Generate Submission ID]
    ↓
        ┌─────────────────┬──────────────────┐
        ↓                 ↓                  ↓
   [Signal 1]      [Signal 2]          [Parallel]
   Perplexity      Linguistic
   0-1 score       0-1 score
        │                 │
        └─────────────────┘
              ↓
      [Confidence Scorer]
      finalScore = (0.6×A) + (0.4×B)
      confidence = 2×|score-0.5|
      classification: human/ai/uncertain
              ↓
      [Label Generator]
      (one of 3 variants)
              ↓
      [Audit Logger]
      (write permanent record)
              ↓
      [HTTP Response 200]
```

**Data passed at each stage:**
- Submission → Signal 1: Raw text
- Signal 1 → Scorer: Score A (0-1) + metadata
- Signal 2 → Scorer: Score B (0-1) + metadata
- Scorer → Label Gen: finalScore, confidence, classification
- Label Gen → Audit: classification, confidence, label text
- Audit → Response: submissionId, classification, confidenceScore, signals, label

#### Diagram 2: Appeal Flow

```
Appeal Input
    ↓
[Rate Limiter] → Pass/Fail (429)
    ↓
[Appeal Validator]
- Check submission exists
- Check reasoning length (50-1000)
- Validate evidence URL
- Ensure no duplicate
              ↓
      [Generate Appeal ID]
              ↓
      [Audit Logger]
      Find original submission
      Append appeal to appeals array:
      {
        appealId, creatorId, reasoning,
        evidence, submittedAt,
        status: "under_review"
      }
      Update submission.status = "under_review"
              ↓
      [HTTP Response 200]
```

**Data passed:**
- Appeal → Validator: submissionId, creatorId, reasoning, evidence
- Validator → Logger: validated appeal data
- Logger → Response: appealId, status, timestamp

---

## Key Design Decisions Explained

### Why 60/40 weights for perplexity/linguistic?

Perplexity is more reliable across different writing domains, so it's weighted higher (60%). Linguistic features are domain-dependent (formal writing is risky), so lower weight (40%). Weights are adjustable based on testing.

### Why confidence = 2 × |finalScore - 0.5|?

The boundary between human/AI is 0.5. Confidence measures distance from that boundary:
- At 0.5: completely uncertain (confidence 0)
- At 0.75: moderately confident (confidence 0.5)
- At 0.95: very confident (confidence 0.9)

This makes confidence **proportional to meaningful separation** between human and AI signals.

### Why three label variants, not a slider?

Three variants match three decision states:
- **High-confidence human:** Tell the user clearly, explain why
- **High-confidence AI:** Warn the user, but not alarmingly
- **Uncertain:** Be honest about doubt, explain it's not a failure of the system

A slider (0-1 confidence) would be harder to interpret for non-technical users.

### Why is the appeal mechanism simple (no auto-reclassification)?

Automated re-runs risk infinite loops and don't address the core issue (signals might have the same bias). A human reviewer can:
- Consider context the signals missed
- Recognize domain-specific challenges
- Make judgment calls
- Create teachable moments for improving signals

The system is designed to support future human review, not bypass it.

### Why log everything?

Audit logging enables:
- **Transparency:** Users can see why the system decided what it did
- **Accountability:** Every decision is traceable
- **Improvement:** Reviewers can find patterns in mistakes
- **Appeals:** Disputes are resolved with full context
- **Regulation:** If authorities ask "why was this classified as AI?", there's an answer

---

## Next Steps

1. **Implementation:** Follow the API surface defined above. Each endpoint is a contract.
2. **Signal Implementation:** Build Signal 1 (perplexity) and Signal 2 (linguistic) as independent modules. Test each against ground-truth data.
3. **Testing:** Validate confidence calibration (high confidence should have high accuracy).
4. **Documentation:** Use the diagrams and explanations in this file as context for README.md.

See planning.md for the full details and implementation timeline.
