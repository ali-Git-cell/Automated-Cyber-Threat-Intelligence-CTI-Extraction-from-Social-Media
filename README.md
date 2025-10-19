# Automated Cyber Threat Intelligence (CTI) Extraction from Social Media Platforms

## Overview

This project implements an **AI-driven framework** for automated **Cyber Threat Intelligence (CTI) extraction**, classification, and validation from social media platforms — primarily **Telegram** — and open-source intelligence repositories via **Exa.ai**.  

The system integrates:
- **GDPR-compliant Telegram scraping**  
- **Machine Learning (ML)-based CTI classification**  
- **AI multi-agent orchestration (CrewAI)**  
- **Automated cross-validation and report generation**

Two pipelines are implemented:
1. **Pipeline 1:** Extracts Telegram messages, classifies CTI content, validates findings against Exa.ai, and generates a cross-validation intelligence report.
2. **Pipeline 2:** Independently queries Exa.ai for global cybersecurity trends, summarises results, and produces a comparative report.
---


---

## Tech Stack
- CrewAI for Multi-agent orchestration
- Python
- Exa API for Real-time Cyber Threat data retrieval
- LLMs is OpenAI GPT
- Telegram API

---

## Project Structure
cybersecurity_intelligence/
- utils/                       # Utility functions
- ml/                          # Ml code
- scrapers/                    # Scrapers for telegram
- reports/                     # Generated Cyber Threat Intelligence Reports
- crew.py                      # CrewAI agents and tasks orchestration
- main.py                      # Entry point → runs full pipeline
- .env/                        # Environment variables for secure usage
- requirements.txt             # Python dependencies
- README.md                    

--

## How to Run Locally

### Install Python & dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Set environment variables
```bash
cp .env.example .env
# Edit .env → add your EXA_API_KEY and OPENAI_API_KEY and GROQ_API_KEY
```

### To Run the app
```bash
python main.py
```

#### The Final Cyber Threat Intelligence Reports will be saved to `reports/` folder.

---

