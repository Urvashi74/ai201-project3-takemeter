# Project 3 Planning: r/womenintech Post Classifier

---

## 1. Community

**Chosen community:** r/womenintech

**Why this community:** r/womenintech is an active, text-heavy subreddit where members share professional experiences, seek career advice, post resources, and recruit for jobs or research. The discourse is varied enough to be interesting because posts range from raw emotional venting about workplace bias to structured career-strategy questions to informational threads and job postings — each with a distinct communicative purpose that a regular community member would immediately recognize. This community has also been personally meaningful — over several years of my own career as a woman in tech, it has been a source of perspective, solidarity, and practical guidance, which makes the project feel grounded in something real.

**Why it fits a classification task:** The variation is driven by intent, not just topic. Two posts can both be about salary negotiation — one asking "how do I negotiate my first offer?" (advice_request) and one sharing "here's the script I used" (sharing_resource_or_info). That intent-level distinction is learnable from surface text and is the kind of signal a community moderation or recommendation tool would actually need.

---

## 2. Label Taxonomy

**Taxonomy — Communicative Intent (one label per post)**

| Label | Definition |
|---|---|
| `advice_request` | The poster describes their own situation and wants actionable guidance for a decision or problem they face. There is a question the community can answer, and a recommendation would resolve it. |
| `vent_or_solidarity` | The poster shares a frustrating, painful, or unfair experience to be heard, to process, or to ask "does anyone else feel this?" No actionable ask — removing every question still leaves a complete emotional or pattern-naming narrative. |
| `sharing_resource_or_info` | The payload is information, analysis, a resource, or advice directed at others rather than a request for the self. The poster is supplying value, not seeking it. |
| `solicitation` | The post recruits or promotes: job listings, co-founder searches, surveys, app/product promotion, paid research participants, event hosting, self-referral for hiring. The poster wants the reader to take an action external to the discussion. |

### Example posts per label

**`advice_request`**
1. "I recently found out my boss' boss takes the guys on my team out for lunch all the time... Idk what to do." — describes a situation, ends with a genuine ask about what action to take.
2. "Hybrid 2 days vs fully remote — which would you choose at this stage of your career?" — real decision, community input resolves it.

**`vent_or_solidarity`**
1. "I cried in a one-on-one with my manager today. I'm so tired of feeling invisible on this team." — no ask, pure processing.
2. "Is it just me or did AI adoption become a pink-collar job? We're the ones doing all the prompt engineering grunt work." — rhetorical question, pattern-naming, not seeking a personal recommendation.

**`sharing_resource_or_info`**
1. "Document document document. This is the key to life. Keep a journal of every time this happens... HR has a fetish for the written word." — advice directed outward, no personal ask.
2. "New study: remote work reduces gender pay gap by ~8% for women in senior roles [link]" — informational payload for the community.

**`solicitation`**
1. "We're hiring senior engineers at [Company] — DM me if interested, happy to refer." — external action requested.
2. "Running a 10-min survey on women's experiences with performance reviews — would love your input [link]." — recruits participants.

---

## 3. Hard Edge Cases

**Hardest boundary: `advice_request` vs. `vent_or_solidarity`**

This is the highest-traffic ambiguous zone. Posts that describe a difficult situation and include a question can belong to either label.

*Ambiguous example:* "I was humiliated by my manager in front of the whole team. I don't know if I'm being too sensitive. Does this kind of thing happen to everyone?"

- Reads like a vent (emotional, no clear action needed).
- But "am I too sensitive" and "does this happen" could be interpreted as seeking validation or a verdict.

**Decision rule:** Is there a genuine, answerable question about what the poster should *do*? If yes → `advice_request`. If the only questions are rhetorical, self-questioning ("am I wrong?"), or seeking solidarity ("anyone else?") → `vent_or_solidarity`.

**Reassurance-seeking sub-case:** "Help me feel better about not negotiating my salary" contains an explicit ask (validate my choice). Rule: if the poster requests a response that changes their *state* (reassurance, a verdict, a recommendation), classify as `advice_request`. Pure "I just needed to put this somewhere" → `vent_or_solidarity`.

**Success announcements:** "After a 4-year search I finally landed a job!" — folds into `sharing_resource_or_info` when the intent is to encourage others, or `vent_or_solidarity` if purely celebratory with no payload for readers. Distinguishing signal: does the post contain information others can use, or is it purely expressive?

---

## 4. Data Collection Plan

**Source:** Posts will be scraped from r/womenintech manually, saved to a CSV for annotation.

**Target total:** 200 labeled examples minimum.

**Target distribution:**

| Label | Target count | Rationale |
|---|---|---|
| `advice_request` | ~65 | Expected to be highest volume in this community |
| `vent_or_solidarity` | ~65 | Co-dominant with advice_request |
| `sharing_resource_or_info` | ~40 | Clearly present but less frequent |
| `solicitation` | ~30 | Least frequent but distinct and classifiable |

**If a label is underrepresented after 200 examples:**
- For `solicitation` or `sharing_resource_or_info` < 20 examples: scrape additional posts filtering by signal phrases ("we're hiring", "survey", "here's a resource") to bootstrap underrepresented classes.
- Do not oversample by weakening label definitions — maintain annotation integrity.
- If `solicitation` stays < 15 after targeted scraping, consider merging into a broader "other" label or treating it as a binary detection task separate from the 3-class problem.

**Annotation process:** [To be filled — single annotator, annotation tool, time estimate]

---

## 5. Evaluation Metrics

**Primary metrics:**

- **Macro-averaged F1:** The primary single-number summary. Computed as the unweighted mean of per-class F1 scores, so each label contributes equally regardless of how many examples it has. This prevents a skewed distribution from hiding failures on minority classes. Reported on a held-out test set of at least 40 examples (20% of 200), stratified so each class is proportionally represented.
- **Per-class precision and recall:** Reported for every label alongside F1. These are necessary to distinguish two failure modes that have the same F1 but opposite practical consequences: a `solicitation` classifier with low recall (misses spam) is a different problem than one with low precision (flags real posts as spam). The per-class table will make this visible.
- **Confusion matrix:** Reported as a 4×4 count matrix on the test set. The off-diagonal cells between `advice_request` and `vent_or_solidarity` are the primary diagnostic target — if those two classes are systematically swapped, it means the model has not learned the actionability boundary, and the failure is interpretable and improvable.

**What I am not using and why:**

- *Accuracy alone:* With ~33% of examples in each of the two dominant classes, a majority-class baseline achieves roughly 33% accuracy. A model that learns nothing useful could score higher than that just by predicting `advice_request` everywhere. Accuracy is not reported as a success metric.
- *Weighted F1:* Weighted F1 scales each class by its support, which reintroduces majority-class bias. Macro F1 is the right choice when all four classes need to work.

---

## 6. Definition of Success

The following thresholds are objective and checkable from the test-set evaluation output. At the end of the project, success or failure is determined by comparing the reported numbers to these thresholds — no interpretation required.

**"Genuinely useful" (target):**
- Macro F1 ≥ 0.75
- No individual class F1 < 0.65
- `solicitation` recall ≥ 0.80 (spam detection must be high-recall)
- `advice_request` / `vent_or_solidarity` confusion rate < 25% (no more than 1 in 4 examples from either class misclassified as the other)

At this level, the classifier is consistent enough for a community tool — auto-routing posts to weekly digests or flagging solicitations for mod review — without requiring human review of every prediction.

**"Acceptable" (deployment floor):**
- Macro F1 ≥ 0.70
- No individual class F1 < 0.60
- `solicitation` recall ≥ 0.75

Below this floor, the classifier introduces more noise than signal for automated use. It could still serve as a soft signal in a human-in-the-loop workflow, but not as a standalone decision-maker.

**Named failure condition (not acceptable regardless of macro F1):**
- If both `advice_request` F1 < 0.65 AND `vent_or_solidarity` F1 < 0.65, the model has failed to learn the core boundary of this taxonomy. This is a classifier failure, not a tuning problem — the result is not deployable and the label definitions or annotation process need re-examination.

---

## 7. AI Tool Plan

AI tools will be used at three specific points in the workflow, each with a defined purpose and verification step.

### 7.1 Label Stress-Testing (before annotation begins)

**When:** Before annotating any examples.

**What:** Give an LLM (Claude) the four label definitions and the `advice_request` / `vent_or_solidarity` decision rule, and ask it to generate 8–10 posts that sit at the boundary between those two labels. Also ask it to generate 3–4 posts that could plausibly be `sharing_resource_or_info` or `vent_or_solidarity` (the success-announcement edge case).

**Prompt structure:** "Here are four labels for classifying r/womenintech posts: [definitions]. Generate 10 posts that would be genuinely difficult to classify — posts where a careful reader could reasonably assign either of two labels. For each post, name the two labels it sits between."

**What to do with the output:** Try to classify each generated post using the written decision rules. If any post cannot be cleanly resolved in under 30 seconds, the decision rule for that boundary is underspecified — revise the rule before annotating. The goal is to surface ambiguity in the taxonomy, not in the examples.

**Disclosure:** Generated posts are for taxonomy validation only and will not appear in the labeled dataset.

### 7.2 Annotation Assistance (during annotation)

**Whether to use it:** Yes — an LLM will be used to pre-label a first-pass batch of examples to speed up annotation.

**Tool:** Claude (claude.ai or API).

**Process:**
1. Feed each post with the label definitions and ask for a predicted label and a one-sentence rationale.
2. Review every pre-label before accepting it — do not accept a label without reading the post and the rationale.
3. Overrule freely: if the rationale doesn't match the decision rule, apply the correct label manually.

**Tracking:** The annotation CSV will include a `pre_labeled` column (yes/no) and a `human_overruled` column (yes/no). This allows post-hoc analysis of how often the LLM's pre-label was accepted vs. corrected, and ensures full disclosure.

**Disclosure in final writeup:** Report the pre-label acceptance rate and note which tool was used for pre-labeling.

### 7.3 Failure Analysis (after model evaluation)

**When:** After computing test-set metrics and generating the confusion matrix.

**What:** Export the list of all misclassified examples (predicted label, true label, post text) and give it to an LLM with the prompt: "Here are posts my classifier got wrong. Each entry shows the true label, the predicted label, and the post text. Identify the most common patterns in the errors — are there surface features (length, question marks, specific phrases) that correlate with misclassification? Are there edge cases my label definitions don't handle well?"

**What to look for:**
- Systematic confusion between two specific labels (expected: `advice_request` ↔ `vent_or_solidarity`)
- Posts that are consistently misclassified because they match a surface pattern of one label but have the intent of another (e.g., posts that start with a story but end with a genuine question)
- Any class where errors cluster around a single sub-type of post

**Verification:** For every pattern the LLM identifies, manually read at least 3 examples it cites and confirm the pattern holds. Do not report a pattern as a finding unless it can be verified by reading the actual text.
