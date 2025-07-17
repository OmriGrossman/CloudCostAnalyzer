# CloudCostAnalyzer

## Overview

CloudCostAnalyzer is a data-driven solution that performs comprehensive analysis and ranking of cloud infrastructure architectures based on cost-efficiency and structural features.

The system consists of two main components:

- **Data Analysis Engine**: Parses and analyzes AWS pricing-related tables to extract actionable insights about service usage and structural patterns.
- **Architecture Ranking Engine**: Uses an LLM (via OpenRouter API) to score and rank architecture JSONs based on custom criteria.

This project is designed to demonstrate data engineering capabilities, from SQL data parsing to LLM-assisted evaluations.

---

## Setup Instructions

### ✅ Requirements

- **Python Version**: 3.9+
- **Libraries** (see `requirements.txt`):
  - `sqlalchemy`
  - `pandas`
  - `openai` or `requests`
  - `python-dotenv`

Install dependencies via:

```bash
pip install -r requirements.txt
```

---

### 🔐 Environment Variables

Create a `.env` file at the root with the following keys:

```env
DB_USER=your_user
DB_PASSWORD=your_password
DB_READ=your_db_host
DB_NAME=your_db_name
OPENROUTER_API_KEY=your_openrouter_api_key
```

---

## Usage

Run the main script to:
- Analyze key tables and extract statistics, features, and duplication patterns
- Export data samples to Excel (optional)
- Score multiple architecture candidates using a GPT-based API

```bash
python main.py
```

---

## Project Structure

- `main.py`: Orchestrates full analysis and ranking pipeline
- `database/`: Contains database session and query logic
- `api/`: Contains LLM evaluation code via OpenRouter
- `architectures.json`: Sample architecture candidates to evaluate

---

## Notes

- You can use your own architecture candidates by editing the `architectures.json` file.
- This project is fully modular, and can be extended to support other cloud providers or ranking criteria.

