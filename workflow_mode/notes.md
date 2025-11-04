# Development Notes

## Step 1: Mock Search
Used Mock Search (Path A)
- Fastest way to test pipeline
- Replace with real search later

## Step 2: Built fetch()
- Handles PDF → /abs/ redirect
- Strips scripts, cleans text
- Skips if < 800 chars (I'll add later)

### PDF → Abstract Redirect
- PDFs are binary; abstract pages are clean HTML
- PDFs would require PyPDF - leads to losing quality text
- `.replace('/pdf/', '/abs/').replace('.pdf', '')`
- fetch() returns readable text every time

## Step 3: Built summarize()
- summarizing one article at a time
- processing chunks independently prevents hidden truncation or API errors.
- Token usage logged for cost tracking

## Step 4: Built persist() in io_utils.py
- Saves .md (human) + .jsonl (machine)
- Timestamped filenames
- main.py will call this

## What happens when URL doesn't work?
- LLM returns message summary
- Fetch part returns an error and main script only selects valid docs
- Add filter in main.py so summary from LLM isn't created for invalid docs

