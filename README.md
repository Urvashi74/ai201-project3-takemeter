# r/womenintech Post Classifier

---

## Community Choice

**Community:** r/womenintech

r/womenintech is an active, text-heavy subreddit where members share professional experiences, seek career advice, post resources, and recruit for jobs or research. The discourse is varied enough to be interesting because posts range from raw emotional venting about workplace bias to structured career-strategy questions to informational threads and job postings — each with a distinct communicative purpose that a regular community member would immediately recognize.

The variation is driven by intent, not just topic. Two posts can both be about salary negotiation — one asking "how do I negotiate my first offer?" (`advice_request`) and one sharing "here's the script I used" (`sharing_resource_or_info`). That intent-level distinction is learnable from surface text and is the kind of signal a community moderation or recommendation tool would actually need.

---

## Label Taxonomy

Each post is assigned exactly one label based on communicative intent.

| Label | Definition |
|---|---|
| `advice_request` | The poster describes their own situation and wants actionable guidance for a decision or problem they face. There is a question the community can answer, and a recommendation would resolve it. |
| `vent_or_solidarity` | The poster shares a frustrating, painful, or unfair experience to be heard, to process, or to ask "does anyone else feel this?" No actionable ask — removing every question still leaves a complete emotional or pattern-naming narrative. |
| `sharing_resource_or_info` | The payload is information, analysis, a resource, or advice directed at others rather than a request for the self. The poster is supplying value, not seeking it. |
| `solicitation` | The post recruits or promotes: job listings, co-founder searches, surveys, app/product promotion, paid research participants, event hosting, self-referral for hiring. The poster wants the reader to take an action external to the discussion. |

### Examples per label

**`advice_request`**
1. "I recently found out my boss' boss takes the guys on my team out for lunch all the time but never invites me. Idk what to do."
2. "Hybrid 2 days vs fully remote — which would you choose at this stage of your career?"

**`vent_or_solidarity`**
1. "I cried in a one-on-one with my manager today. I'm so tired of feeling invisible on this team."
2. "Is it just me or did AI adoption become a pink-collar job? We're the ones doing all the prompt engineering grunt work."

**`sharing_resource_or_info`**
1. "Document document document. This is the key to life. Keep a journal of every time this happens. HR has a fetish for the written word."
2. "New study: remote work reduces gender pay gap by ~8% for women in senior roles [link]"

**`solicitation`**
1. "We're hiring senior engineers at [Company] — DM me if interested, happy to refer."
2. "Running a 10-min survey on women's experiences with performance reviews — would love your input [link]."

---

## Data Collection, Labeling, and Distribution

**Source:** Posts were scraped manually from r/womenintech and saved to a CSV (`r_women_in_tech_classifier.csv`).

**Labeling process:** An annotation assistance script (`annotate.py`) called `claude-haiku-4-5-20251001` via the Anthropic SDK to pre-label each post with a predicted label and a one-sentence rationale. Every pre-label was reviewed by a human annotator before acceptance. Where the rationale did not match the decision rules in the taxonomy, the label was corrected manually and `human_overruled` was set to `yes` in the CSV. The CSV tracks `pre_labeled`, `human_overruled`, and `ai_rationale` for every row to enable post-hoc analysis of annotation quality.

**Label distribution (239 total posts):**

| Label | Count | % |
|---|---|---|
| `advice_request` | 112 | 46.9% |
| `vent_or_solidarity` | 63 | 26.4% |
| `sharing_resource_or_info` | 44 | 18.4% |
| `solicitation` | 20 | 8.4% |

### Three difficult-to-label examples

**1. "This post is half vent, half request for advice. I got burnt out and took a sabbatical... Need to get back into the job market, but I don't know if I can."**

The post explicitly names itself as hybrid. Decision: `vent_or_solidarity`. The poster frames the core uncertainty as emotional processing ("I don't know if I can"), not a request for a concrete recommendation about how to return. The stated inability to act is the subject, not the object of an actionable question.

**2. "How common is actually being expected to work during maternity leave? Two different experiences — we all know working during maternity leave is often illegal..."**

Superficially reads as `advice_request` because it opens with a question. Decision: `vent_or_solidarity`. "How common is X" is solidarity-seeking, not a personal decision question. The poster is naming a pattern, not asking what they should do.

**3. "I'm so sorry. I started my own company the third time I was laid off. My only piece of advice is to network. I connect with anyone and everyone on LinkedIn..."**

Opens with "I'm so sorry" and reads as empathetic support. Decision: `sharing_resource_or_info`. The emotional opener is a framing device; the payload is concrete, outward-directed career advice the community can use. The poster is supplying value, not processing their own experience.

---

## Fine-Tuning Approach

**Base model:** `distilbert-base-uncased`

DistilBERT was chosen as the base model because it is small enough to fine-tune in a Colab environment with limited compute, has strong benchmark performance on text classification tasks, and serves as a meaningful baseline for intent classification — a task that requires understanding sentence-level semantics rather than just keyword matching.

**Training setup:**
- Platform: Google Colab (T4 GPU)
- Task: 4-class sequence classification
- Training data: 80% of 239 labeled examples (~191 posts), stratified by label
- Validation data: held-out split used for checkpoint selection (`load_best_model_at_end=True`)
- Test data: 20% (~48 posts), held out before training
- Optimizer: AdamW
- Epochs: 3
- Learning rate: 2e-5
- Batch size: 16 (train), 32 (eval)
- Weight decay: 0.01
- Warmup steps: 50
- Evaluation strategy: per epoch; best checkpoint selected on validation accuracy

**Hyperparameter decision:** 3 epochs was kept as-is rather than increased because this dataset has 239 examples across 4 classes — roughly 50 examples per class on average. At this scale, additional epochs risk overfitting to the majority class (`advice_request`, 47% of data) rather than learning the minority class boundaries. The learning rate of 2e-5 is the standard starting point for fine-tuning BERT-family models and is conservative enough to avoid destabilizing the pre-trained weights on a small dataset. Increasing it on a 200-example corpus tends to cause the model to collapse to majority-class prediction within the first epoch.

---

## Baseline Description

**Model:** `llama-3.1-8b-instant` via Groq API

**Prompt used:**

```
You are classifying posts from the r/womenintech subreddit.
Assign each post to exactly one of the following categories.

advice_request: The poster describes their own situation and wants actionable guidance
for a decision or problem they face. There is a question the community can answer,
and a recommendation would resolve it.
Example: "I recently found out my boss' boss takes the guys on my team out for lunch
all the time but never invites me. Idk what to do."

vent_or_solidarity: The poster shares a frustrating, painful, or unfair experience to
be heard, to process, or to ask "does anyone else feel this?" No actionable ask —
removing every question still leaves a complete emotional or pattern-naming narrative.
Example: "I cried in a one-on-one with my manager today. I'm so tired of feeling
invisible on this team."

sharing_resource_or_info: The payload is information, analysis, a resource, or advice
directed at others rather than a request for the self. The poster is supplying value,
not seeking it.
Example: "Document document document. Keep a journal of every time this happens.
HR has a fetish for the written word."

solicitation: The post recruits or promotes — job listings, surveys, app/product
promotion, event hosting, or co-founder searches. The poster wants the reader to
take an action external to the discussion.
Example: "We're hiring senior engineers at [Company] — DM me if interested, happy
to refer."

KEY RULE for advice_request vs vent_or_solidarity:
Ask: is there a genuine, answerable question about what the poster should DO?
- Yes → advice_request
- Only rhetorical questions, "am I wrong?", or "anyone else?" → vent_or_solidarity

Respond with ONLY the label name. Do not explain your reasoning.

Valid labels:
advice_request
vent_or_solidarity
sharing_resource_or_info
solicitation
```

**How results were collected:** Each post in the test set was passed to the Groq API with the above system prompt. The model's response was stripped of whitespace and matched against the four valid label strings. Responses that did not exactly match a valid label were marked as unparseable. 36/36 responses were parseable.

---

## Evaluation Report

### Overall accuracy

| Model | Accuracy | Test set size |
|---|---|---|
| Baseline (Groq LLM) | **0.917** | 36 |
| Fine-tuned DistilBERT | **0.472** | 36 |

### Per-class metrics — Baseline

| | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| `advice_request` | 0.85 | 1.00 | 0.92 | 17 |
| `vent_or_solidarity` | 1.00 | 0.70 | 0.82 | 10 |
| `sharing_resource_or_info` | 1.00 | 1.00 | 1.00 | 6 |
| `solicitation` | 1.00 | 1.00 | 1.00 | 3 |
| **accuracy** | | | **0.92** | **36** |
| **macro avg** | **0.96** | **0.93** | **0.94** | **36** |
| **weighted avg** | **0.93** | **0.92** | **0.91** | **36** |

### Per-class metrics — Fine-tuned DistilBERT

Derived from the confusion matrix below.

| | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| `advice_request` | 0.57 | 0.94 | 0.71 | 17 |
| `vent_or_solidarity` | 0.14 | 0.10 | 0.12 | 10 |
| `sharing_resource_or_info` | 0.00 | 0.00 | 0.00 | 6 |
| `solicitation` | 0.00 | 0.00 | 0.00 | 3 |
| **accuracy** | | | **0.47** | **36** |
| **macro avg** | **0.18** | **0.26** | **0.21** | **36** |

### Confusion matrix — Fine-tuned DistilBERT (Test Set)

|  | Pred: advice_request | Pred: vent_or_solidarity | Pred: sharing_resource_or_info | Pred: solicitation |
|---|---|---|---|---|
| **True: advice_request** | 16 | 1 | 0 | 0 |
| **True: vent_or_solidarity** | 8 | 1 | 1 | 0 |
| **True: sharing_resource_or_info** | 2 | 4 | 0 | 0 |
| **True: solicitation** | 2 | 1 | 0 | 0 |

The model never once predicted `sharing_resource_or_info` or `solicitation` correctly. Every error in both classes was absorbed into `advice_request` or `vent_or_solidarity`.

### Analysis of wrong predictions

**Wrong prediction 1**

> "is it just me or does 'culture fit' only ever get raised about the women and the people who push back, never about the guy everyone agrees is brilliant but impossible? asking because I've now watched this happen at three separate companies..."

True: `vent_or_solidarity` — Predicted: `advice_request` (confidence: 0.30)

The phrase "asking because" is a surface signal the model has associated with advice-seeking. But this post is pattern-naming across companies — the poster is not describing a current decision or asking what to do. The question is rhetorical and solidarity-seeking. This is the core `advice_request` / `vent_or_solidarity` boundary failure: the model learned that questions indicate `advice_request` without learning that intent, not surface syntax, determines the label. To fix this, the training set needs more examples of rhetorical questions and "anyone else?" framing explicitly labeled as `vent_or_solidarity`.

**Wrong prediction 2**

> "Document document document. This is the key to life. Keep a journal (paper or not your work machine) of every time this happens. Document everything you know about it: who was there, when it happened..."

True: `sharing_resource_or_info` — Predicted: `advice_request` (confidence: 0.28)

This post gives concrete, outward-directed advice in the imperative voice — a strong signal of `sharing_resource_or_info`. The model predicted `advice_request`, likely because the content is practical and actionable, a surface feature it has linked to advice-seeking rather than advice-giving. The distinction requires understanding the direction of the information flow (outward to the community vs. inward, seeking input), which the model has not learned. The training set likely contains too few clear `sharing_resource_or_info` examples with imperative voice to establish this boundary.

**Wrong prediction 3**

> "Mass call tomorrow for laid off tech workers. Update: link to recording of call. [mods: hopefully this free resource and community-building event isn't viewed as self-promotion. Our past calls were maj...]"

True: `solicitation` — Predicted: `vent_or_solidarity` (confidence: 0.29)

The model has 0% recall on `solicitation`. This post is a community event promotion — the poster wants readers to attend and take an external action. But the framing is empathetic ("laid off tech workers", "community-building"), which the model has associated with `vent_or_solidarity`. The model never learned the distinguishing feature of solicitation: *the poster wants the reader to do something outside the discussion*, regardless of how helpful or community-oriented the framing is. With only 20 solicitation examples in training and 0 correct predictions on the test set, this is a data quantity problem as much as a boundary problem.

### Sample classifications

| Post (truncated) | True label | Predicted | Confidence |
|---|---|---|---|
| "Hybrid 2 days vs fully remote — which would you choose at this stage of your career?" | `advice_request` | `advice_request` | ~0.35 |
| "I'm so tired of eating lunch alone" | `vent_or_solidarity` | `sharing_resource_or_info` | 0.28 |
| "Document document document. This is the key to life. Keep a journal of every time this happens..." | `sharing_resource_or_info` | `advice_request` | 0.28 |
| "I built a free careers resource for ECE technical engineering interview prep after seeing my friends struggle..." | `solicitation` | `advice_request` | 0.29 |
| "Need to get back into the job market, but I don't know if I can. This post is half vent, half request for advice..." | `vent_or_solidarity` | `advice_request` | 0.30 |

**Correct prediction explained:** "Hybrid 2 days vs fully remote — which would you choose at this stage of your career?" is a straightforward `advice_request`: the poster faces a concrete binary decision and is asking the community to weigh in. The prediction is reasonable because the post contains a direct, answerable question about what the poster should do — the clearest surface signal for this label.

Note that even the correct prediction carries low confidence (~0.35). This is consistent with the finding that the model's confidence scores are uniformly low across all outputs, signaling that the fine-tuned weights have not encoded meaningful label representations.

---

## Reflection

The model learned one thing: most posts are `advice_request`. With 47% of training examples in that class, defaulting to it yields nearly 50% accuracy — and that is roughly what the model achieved (0.472). It did not learn the intent-level distinctions that define the taxonomy.

The intended decision boundary for `advice_request` vs `vent_or_solidarity` is about the direction and actionability of the post's ask: is the poster seeking a recommendation that changes what they will *do*, or are they seeking to be heard? The model substituted a surface proxy: the presence of a question mark. Posts with rhetorical questions or "anyone else?" framing were reliably predicted as `advice_request`.

For `sharing_resource_or_info`, the intended signal is the direction of information flow: the poster is supplying value outward rather than requesting it for themselves. The model did not learn this at all — 0% recall. It conflated advice-giving in imperative voice with advice-seeking, possibly because the vocabulary overlaps (both involve practical language and actionable topics).

For `solicitation`, the intended signal is the external action ask: regardless of how helpful or community-oriented the post feels, if it wants the reader to apply, attend, fill out, or DM, it is solicitation. The model learned nothing here either — 0% recall — likely because 20 training examples is too few to establish this as a distinct pattern, and because solicitation posts in this community are deliberately framed to minimize their promotional character.

In short, the model captured majority-class frequency. The taxonomy was built around communicative intent; the model responded to surface syntax and topic distribution.

---

## Spec Reflection

**One way the spec helped:** The decision rules in `planning.md §3` were directly usable as annotation guidance. The rule for `advice_request` vs `vent_or_solidarity` — "Is there a genuine, answerable question about what the poster should DO?" — resolved genuinely ambiguous cases during annotation and translated directly into the LLM baseline prompt. Having written the rule precisely before annotating meant that borderline posts were labeled consistently rather than case-by-case, which is what made the baseline perform well on this boundary (vent recall = 0.70, not 0%).

**One way implementation diverged from the spec:** The spec targeted 30 `solicitation` examples; the final dataset contains only 20. Solicitation posts in this community are relatively rare and often deleted by moderators before scraping. Rather than weaken the label definition to capture borderline promotional posts, the annotation integrity rule from §4 was held ("do not oversample by weakening label definitions"), which means the class remained underrepresented. In retrospect, the spec's contingency plan — targeted scraping using signal phrases like "we're hiring" and "survey" — should have been executed earlier in the data collection process rather than treated as a fallback.

---

## AI Usage

**Instance 1 — Annotation pre-labeling (`annotate.py`)**

The script sent each unlabeled post to `claude-haiku-4-5-20251001` via the Anthropic SDK with the full label definitions and decision rules as a cached system prompt. The model returned a predicted label and a one-sentence rationale for each post. Every output was reviewed by a human annotator before acceptance. Posts where the rationale did not match the decision rules — for example, where the model labeled a rhetorical "anyone else?" question as `advice_request` — were manually corrected and flagged with `human_overruled = yes`. The model's pre-labels were used as a starting point, not as ground truth.

**Instance 2 — Error pattern analysis (failure analysis step)**

After computing the confusion matrix for the fine-tuned model, the 15 misclassified examples were pasted into Claude with the prompt: *"Identify the most common patterns in these errors — are there surface features (question marks, specific phrases) that correlate with misclassification? Are there edge cases the label definitions don't handle well?"* The AI identified three candidate patterns: question marks triggering `advice_request`, post length, and solicitation posts with community framing. Post length was discarded after manual re-reading — example #4 ("I'm so tired of eating lunch alone", 10 words) was still misclassified, making length an unreliable predictor. The question-mark pattern and the solicitation framing pattern held up on manual verification across multiple examples and are reported in the evaluation above.

**Annotation disclosure:** 239 posts were pre-labeled using `claude-haiku-4-5-20251001`. The pre-label acceptance rate and per-row override flags are tracked in `human_overruled` column of `r_women_in_tech_classifier.csv`.
