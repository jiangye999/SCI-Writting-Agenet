# Journal Writing Style Extraction Skill

## Purpose

This document defines a reusable AI skill for systematically extracting
**journal-specific writing styles** at the section level, enabling
faithful replication of structure, language, and academic stance.

------------------------------------------------------------------------

## Input Requirements

-   Multiple peer-reviewed research articles from the **same academic
    journal**
-   Article types: Original research articles only (exclude editorials,
    reviews, comments)
-   Texts must be **segmented by section**:
    -   Abstract
    -   Introduction
    -   Methods
    -   Results
    -   Discussion
    -   Conclusion

------------------------------------------------------------------------

## Global Journal-Level Analysis

### Objectives

Analyze the journal as a whole to infer:

-   Overall academic tone (cautious / assertive / neutral)
-   Theory-driven vs application-driven orientation
-   Tolerance for speculative interpretation
-   Typical strength of claims
-   Assumed reader expertise

------------------------------------------------------------------------

## Section-Level Style Extraction Framework

Apply **all analyses below to each section independently**.

------------------------------------------------------------------------

## Section: {{Section Name}}

### 1. Rhetorical Function

-   Primary communicative purpose of the section
-   Role in the manuscript's logical progression
-   Expected contribution to the overall argument

------------------------------------------------------------------------

### 2. Sentence-Level Analysis

Report:

-   Average sentence length (words per sentence)
-   Sentence length distribution:
    -   Short (\<15 words): %
    -   Medium (15--25 words): %
    -   Long (\>25 words): %
-   Sentence structures:
    -   Simple
    -   Compound
    -   Complex
-   Use of:
    -   Subordinate clauses
    -   Relative clauses
    -   Parenthetical structures

------------------------------------------------------------------------

### 3. Voice and Tense

Analyze:

-   Active vs Passive voice ratio (%)
-   Dominant tense usage:
    -   Present simple
    -   Past simple
    -   Present perfect
-   Typical alignment between tense and section function

------------------------------------------------------------------------

### 4. Part-of-Speech Usage (Top 20)

For the current section, extract **Top 20 words** for each category:

-   Nouns (Top 20)
-   Verbs (Top 20)
-   Adjectives (Top 20)
-   Adverbs (Top 20)

Constraints: - Use lemma forms - Exclude stopwords - Mark academic vs
general vocabulary

------------------------------------------------------------------------

### 5. Verb Function and Epistemic Role

Classify frequent verbs into:

-   Reporting verbs (e.g., show, indicate)
-   Cognitive verbs (e.g., suggest, assume)
-   Procedural verbs (e.g., measure, calculate)
-   Evaluative verbs (e.g., improve, outperform)

Explain: - Dominant verb category - Implications for epistemic stance

------------------------------------------------------------------------

### 6. Hedging and Certainty

Analyze:

-   Modal verbs (may, might, could, must)
-   Hedging expressions:
    -   suggests that
    -   is likely to
-   Strengthening expressions:
    -   clearly demonstrate
    -   strongly indicate

Provide: - Hedging density - Typical claim strength

------------------------------------------------------------------------

### 7. Reusable Sentence Templates

Extract 5--10 high-frequency, reusable sentence patterns.

Format: - Abstracted templates with variable slots

Example: - "The results indicate that {{X}} is significantly associated
with {{Y}}."

------------------------------------------------------------------------

### 8. Implicit Constraints and Red Flags

Identify prohibited or discouraged practices:

-   Overclaiming
-   Excessive speculation
-   Informal or narrative language
-   Unsupported causal inference

------------------------------------------------------------------------

### 9. One-Sentence Style Rule

Summarize the section style as a strict rule.

Example: - "The Discussion section favors cautious interpretation
tightly anchored to empirical results."

------------------------------------------------------------------------

## Final Output Requirements

### A. Section-by-Section Style Checklist

-   Actionable checklist for manuscript self-review

### B. Write-Like-This Micro Guide

-   3--5 hard rules per section for direct imitation

------------------------------------------------------------------------

## Design Rationale

-   **POS Top 20** reveals lexical ecology
-   **Sentence length distribution** captures rhythm beyond averages
-   **Verb categorization** exposes epistemic positioning
-   **Red flag analysis** mirrors reviewer rejection logic

------------------------------------------------------------------------

## End of Document
