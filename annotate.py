"""
Annotation assistance script (planning.md §7.2).

Reads posts from the CSV, calls Claude (claude-haiku-4-5) to produce a
pre-label and one-sentence rationale for each unlabeled row, then writes the
results back in-place. Adds three columns:
  - pre_labeled     : "yes" for every row touched by this script
  - human_overruled : left blank — the human fills this in during review
  - ai_rationale    : the model's one-sentence reason, shown during review

Run:
    python3 annotate.py

Review workflow:
    Open the CSV, read each post alongside ai_rationale, accept or correct the
    label, and set human_overruled to "yes" wherever you changed it.
"""

import csv
import json
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path(__file__).parent / "r_women_in_tech_classifier.csv"
MODEL = "claude-haiku-4-5-20251001"
VALID_LABELS = {"advice_request", "vent_or_solidarity", "sharing_resource_or_info", "solicitation"}

SYSTEM_PROMPT = """You are an annotation assistant classifying posts from the r/womenintech subreddit.

Assign exactly one label per post using the definitions and decision rules below.

LABELS
------
advice_request
  The poster describes their own situation and wants actionable guidance for a
  decision or problem they face. There is a question the community can answer,
  and a recommendation would resolve it.

vent_or_solidarity
  The poster shares a frustrating, painful, or unfair experience to be heard,
  to process, or to ask "does anyone else feel this?" No actionable ask —
  removing every question still leaves a complete emotional or pattern-naming
  narrative.

sharing_resource_or_info
  The payload is information, analysis, a resource, or advice directed at
  others rather than a request for the self. The poster is supplying value,
  not seeking it.

solicitation
  The post recruits or promotes: job listings, co-founder searches, surveys,
  app/product promotion, paid research participants, event hosting,
  self-referral for hiring. The poster wants the reader to take an action
  external to the discussion.

KEY DECISION RULES
------------------
advice_request vs vent_or_solidarity (the hardest boundary):
  Ask: is there a genuine, answerable question about what the poster should DO?
  - Yes → advice_request
  - Only rhetorical questions, "am I wrong?", or "anyone else?" → vent_or_solidarity
  - If the poster explicitly requests a response that changes their state
    (reassurance, a verdict, a recommendation) → advice_request
  - "I just needed to put this somewhere" → vent_or_solidarity

sharing_resource_or_info vs vent_or_solidarity:
  Is the post addressed outward with information others can use, or inward
  toward the poster's own processing? Stated poster intent is the tiebreaker.

sharing_resource_or_info vs solicitation:
  Does the poster want the reader to take an action external to the discussion
  (apply, DM, fill out, attend)? If yes → solicitation, even if the content
  is genuinely useful or non-commercial.

OUTPUT FORMAT
-------------
Respond with valid JSON only — no markdown, no explanation outside the JSON:
{"label": "<one of the four labels>", "rationale": "<one sentence explaining the key signal>"}"""


def classify(client: anthropic.Anthropic, text: str, retries: int = 5) -> dict:
    for attempt in range(retries):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=150,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {"role": "user", "content": f"Classify this post:\n\n{text}"}
                ],
            )
            raw = response.content[0].text.strip()
            # strip markdown code fences the model adds despite instructions
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            result = json.loads(raw)
            if result.get("label") not in VALID_LABELS:
                raise ValueError(f"Unexpected label: {result.get('label')}")
            return result
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Failed to parse model response after {retries} attempts: {e}")
            time.sleep(1)
        except anthropic.RateLimitError:
            wait = 2 ** attempt
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except anthropic.InternalServerError as e:
            wait = 2 ** attempt
            print(f"  API 500 error, waiting {wait}s (attempt {attempt+1}/{retries})...")
            if attempt == retries - 1:
                raise
            time.sleep(wait)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def main():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    existing_fields = list(rows[0].keys()) if rows else []
    new_fields = ["pre_labeled", "human_overruled", "ai_rationale"]
    fieldnames = existing_fields + [f for f in new_fields if f not in existing_fields]

    unlabeled = [i for i, r in enumerate(rows) if not r.get("label", "").strip()]
    print(f"Rows to label: {len(unlabeled)} / {len(rows)}")

    skipped = 0
    for count, i in enumerate(unlabeled, 1):
        text = rows[i]["text"].strip()
        if not text:
            rows[i]["pre_labeled"] = "yes"
            rows[i]["human_overruled"] = ""
            rows[i]["ai_rationale"] = "empty post"
            rows[i]["label"] = ""
        else:
            try:
                result = classify(client, text)
                rows[i]["label"] = result["label"]
                rows[i]["pre_labeled"] = "yes"
                rows[i]["human_overruled"] = ""
                rows[i]["ai_rationale"] = result["rationale"]
                print(f"[{count}/{len(unlabeled)}] {result['label']:<30} {text[:60].replace(chr(10), ' ')}...")
            except Exception as e:
                print(f"[{count}/{len(unlabeled)}] SKIPPED (error: {e}) — {text[:60].replace(chr(10), ' ')}...")
                rows[i]["pre_labeled"] = "yes"
                rows[i]["human_overruled"] = ""
                rows[i]["ai_rationale"] = f"skipped: {e}"
                rows[i]["label"] = ""
                skipped += 1

        # Save after every row so progress is never lost
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    if skipped:
        print(f"\nWarning: {skipped} row(s) skipped due to API errors — label left blank for manual review.")

    label_counts = {}
    for r in rows:
        lbl = r.get("label", "").strip()
        if lbl:
            label_counts[lbl] = label_counts.get(lbl, 0) + 1

    print("\nDone. Label distribution:")
    for lbl, count in sorted(label_counts.items()):
        print(f"  {lbl:<30} {count}")
    print(f"\nCSV written to: {CSV_PATH}")
    print("Next step: open the CSV, review each row, and set human_overruled=yes where you change a label.")


if __name__ == "__main__":
    main()
