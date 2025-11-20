# ⚡ Quick Setup Guide (Copy-Paste Ready)

```bash
# 1. Clone the project
git clone https://github.com/notminhaj/agenticAI.git
cd agenticAI

# 2. Create & activate Python 3.12 virtual environment
# ── Windows
py -3.12 -m venv venv
venv\Scripts\activate

# ── macOS / Linux
# python3.12 -m venv venv
# source venv/bin/activate

# 3. Install all dependencies (CPU-only, works everywhere)
pip install --upgrade pip
pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu

# 4. Set up your API keys
cp .env.example .env
# Now open .env in any editor and add your keys:
# OPENAI_API_KEY=sk-...
# BRAVE_API_KEY=BRAVE_...       # free at https://brave.com/search/api/

# 5. Run the tutor
python chatbot.py