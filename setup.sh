#!/bin/bash
# setup.sh - One‑time environment setup and launch script

set -e  # exit on error

# Change to the script's directory (project root)
cd "$(dirname "$0")"

# ---------- Check for uv ----------
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed."
    echo "Please install it first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "Then restart your shell and run this script again."
    exit 1
fi

# ---------- Sync dependencies ----------
echo "📦 Installing / syncing dependencies with uv..."
uv sync

# ---------- Check / create .env ----------
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Let's create one."

    # If .env.example exists, copy it as a starting point
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Copied .env.example to .env"
    else
        touch .env
    fi

    # Prompt for each required variable
    echo "Please enter your API credentials:"

    read -p "PROVIDER_API_KEY: " api_key
    read -p "MODEL_NAME (default: gpt-4o): " model_name
    model_name=${model_name:-gpt-4o}
    read -p "BASE_URL (default: https://api.openai.com/v1): " base_url
    base_url=${base_url:-https://api.openai.com/v1}

    # Write to .env (overwrites any existing values)
    cat > .env <<EOF
PROVIDER_API_KEY=$api_key
MODEL_NAME=$model_name
BASE_URL=$base_url
EOF

    echo "✅ .env file created successfully."
else
    echo "✅ .env already exists. Using it as is."
fi

# ---------- Ask to run main.py ----------
read -p "🚀 Do you want to run main.py now? (y/N) " run_now
if [[ "$run_now" =~ ^[Yy]$ ]]; then
    echo "▶️  Running main.py..."
    uv run python main.py
else
    echo "You can run it later with: uv run python main.py"
fi