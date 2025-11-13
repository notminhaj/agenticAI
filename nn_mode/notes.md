## ISSUE: facebook/bart-large-mnli is a garbage model
- Zero-shot classification model
- Classifies 1 piece of text between multiple categories
- Gives sim-score 1 paper at a time
- Doesn't help with ranking, can't compare papers
- Enter intfloat/e5-base-v2
- Can rank multiple papers based on single topic

## Note: Copied code straight from hf model page
- Using cursor's agent mode to configure package versions
- Modified code for my use case

## ISSUE: When fetching returns blank documents, scoring them using NN breaks
- Added guardrails
- Now returns 0, as a result, better documents receive higher ranking
