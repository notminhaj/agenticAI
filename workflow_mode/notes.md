[Step 1] Used Mock Search (Path A)
[Why] Fastest way to test pipeline
[Next] Replace with real search later
[Step 2] Built fetch()
[Feature] Handles PDF → /abs/ redirect
[Feature] Strips scripts, cleans text
[Guard] Skips if < 800 chars (I'll add later)
[Deep Dive] PDF → Abstract Redirect
[Why] PDFs are binary; abstract pages are clean HTML
[How] .replace('/pdf/', '/abs/').replace('.pdf', '')
[Result] fetch() returns readable text every time
[Step 3] Built summarize()
[Feature] Truncates text, retries on error
[Note] Token usage logged for cost tracking
[Step 4] Built persist() in io_utils.py
[Feature] Saves .md (human) + .jsonl (machine)
[Feature] Timestamped filenames
[Next] main.py will call this