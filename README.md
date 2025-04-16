# Taurbull Website Scraper

A Python application that scrapes content from Taurbull website and uploads it to ElevenLabs knowledge base via API.

## Features

- Scrapes FAQ content from Taurbull website
- Scrapes legal pages (Legal Notice, Privacy Policy, Terms of Service)
- Parses structured JSON-LD data
- Extracts formatted text from legal documents
- Tracks content changes using MD5 hashing
- Uploads content to ElevenLabs knowledge base via API
- Assigns documents to specific ElevenLabs agents
- Scheduled execution for automatic updates

## ElevenLabs Knowledge Base Integration

This application uses the ElevenLabs Conversational AI Knowledge Base API to keep your AI assistant up-to-date with your website content. The integration works by:

1. Scraping content from your website
2. Checking for changes using content hashing
3. Uploading changed content to your ElevenLabs knowledge base

### Requirements

To use this application with ElevenLabs, you need:

- An ElevenLabs account with access to Conversational AI features (Creator tier or higher)
- An ElevenLabs API key with knowledge base access
- At least one conversational agent created in your ElevenLabs account

### Troubleshooting

If you encounter issues with the ElevenLabs integration, use the diagnostic tool:

```bash
python diagnose_elevenlabs_knowledge_base.py
```

This will check your API access and help identify any issues with your account or setup.

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

5. Run the diagnostic tool to verify your ElevenLabs access
```bash
python diagnose_elevenlabs_knowledge_base.py
```

## Usage

Run the scraper manually (one-time):
```bash
python -m src.main --once
```

Force update all pages regardless of content changes:
```bash
python -m src.main --once --force
```

For scheduled execution:
```bash
python -m src.main
```

With forced updates at each scheduled run:
```bash
python -m src.main --force
```

### Testing the Legal Pages Scraper

To test the legal pages scraper without uploading to ElevenLabs:
```bash
python -m src.test_legal_scraper
```

This will scrape the legal pages and save the extracted content to the `test_output` directory for review.

## Deployment

The application can be deployed to Heroku for automatic scheduling:

1. Create a Heroku app
```bash
heroku create your-app-name
```

2. Set environment variables
```bash
heroku config:set ELEVENLABS_API_KEY=your_api_key_here
```

3. Deploy the application
```bash
git push heroku main
```

4. Set up the Heroku Scheduler
   - Install the Heroku Scheduler add-on
   - Create a scheduled job to run `python -m src.main --once`

## Testing

Run tests with pytest:
```bash
pytest
```

## License

MIT 