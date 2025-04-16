# Taurbull Website Scraper

A Python application that scrapes content from Taurbull website and uploads it to ElevenLabs knowledge base via API.

## Features

- Scrapes FAQ content from Taurbull website
- Parses structured JSON-LD data
- Tracks content changes using MD5 hashing
- Uploads content to ElevenLabs knowledge base via API
- Scheduled execution for automatic updates

## Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/taurbull_scraper_v2.git
cd taurbull_scraper_v2
```

2. Create and activate virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your credentials
```bash
cp .env.example .env
# Edit .env with your ElevenLabs API key
```

## Usage

Run the scraper manually:
```bash
python src/main.py
```

## Deployment

The application can be deployed to Heroku for automatic scheduling.

## Testing

Run tests with pytest:
```bash
pytest
```

## License

MIT 