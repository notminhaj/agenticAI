# Analysis Report: Why Only 3 Articles Are Summarized

**Date:** 2025-10-29  
**Issue:** Program searches for 20 articles but only summarizes the same 3 articles repeatedly

---

## Executive Summary

The issue has been identified in `workflow_mode/main.py`. The program is hardcoded to only process and summarize the **first 3 articles** from the search results, even though the search function is configured to retrieve 20 articles.

---

## Root Cause Analysis

### 1. **Location of the Limitation**

**File:** `workflow_mode/main.py`  
**Line:** 39

```python
for i, d in enumerate(docs[:3], 1):
```

This line uses Python slicing `[:3]` to limit processing to only the first 3 documents from the `docs` list.

---

### 2. **Supporting Evidence**

**A. Hardcoded Display Message (Line 40)**
```python
print(f"   [{i}/3] {d['title'][:50]}...")
```
This clearly shows the program is designed to display "3" as the total count.

**B. Comment in Code (Line 36-37)**
```python
# 3. Summarize (limit to 3)
print("3. Summarizing with LLM...")
```
The comment explicitly states the intention to "limit to 3".

---

### 3. **Search Function Behavior**

**File:** `workflow_mode/search.py`

The search function itself is configured correctly:
- **Line 10:** `def search(topic: str = "Agentic AI", limit: int = 20)`
- The default limit is set to 20 articles
- **Note:** The docstring (line 17) incorrectly states "default: 5" but the actual default is 20

**File:** `workflow_mode/main.py`  
**Line 12:**
```python
candidates = search(topic="trending AI papers 2025 site:arxiv.org/abs/")
```
The search is called without specifying a limit, so it retrieves 20 articles by default.

---

## Why the Same Articles Appear Every Time

The arXiv API returns results in a **consistent, sorted order** based on:
1. Publication/submission date (most recent first)
2. Paper ID (alphabetical for same date)

Because the program always takes `docs[:3]` (the first 3 results), it will always process:
- The 3 most recent papers matching the search query
- Unless new papers are published that push older ones out of the top 3 positions

---

## Current Program Flow

```
1. search() → Returns 20 articles from arXiv
2. fetch() → Downloads content for all 20 articles  
3. Summarization → Only processes docs[:3] (first 3 articles)
4. Output → 3 summaries are saved to report
```

---

## Impact

- **Search retrieves:** 20 articles
- **Content fetched:** 20 documents (17 are wasted time/resources)
- **Summarized:** Only 3 articles
- **Same results:** Yes, because arXiv sorts results consistently

---

## Observed Results

From `report_2025-10-29.md`:
1. **2504.16153v1** - Leveraging Social Media Analytics for Sustainability Trend Detection
2. **2502.16871v1** - Utilizing Social Media Analytics to Detect Trends  
3. **2502.16740v1** - Investigating Task Delegation Trend of Author-AI Co-Creation

These will remain the same until new papers with matching criteria are published.

---

## Recommendations

1. **Remove the hardcoded limit** in `main.py` line 39
2. **Make the summarization limit configurable** via a parameter
3. **Consider randomizing or paginating** the results if you want different articles each run

---

## Proposed Fix

Change line 39 in `workflow_mode/main.py` from:
```python
for i, d in enumerate(docs[:3], 1):
```

To one of these options:

**Option A: Process all articles**
```python
for i, d in enumerate(docs, 1):
    print(f"   [{i}/{len(docs)}] {d['title'][:50]}...")
```

**Option B: Make it configurable**
```python
NUM_SUMMARIES = 10  # or any number you want
for i, d in enumerate(docs[:NUM_SUMMARIES], 1):
    print(f"   [{i}/{min(NUM_SUMMARIES, len(docs))}] {d['title'][:50]}...")
```

---

**Report Generated:** 2025-10-29  
**Analysis Completed:** Yes  
**Issue Status:** Identified ✅

