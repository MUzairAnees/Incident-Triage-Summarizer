# Incident-Triage-Summarizer
An intelligent log analysis API that uses AI to detect incidents and provide actionable summaries.

## Overview
This service ingests app logs, detects patterns within those logs(errors, timeouts, database issues), and provides AI-powered explanations and recommendations for incident resolution.

## Tech Stack
- **Backend**: Python 3.11(Min), FastAPI
- **Database**: SQLite (dev env), AWS RDS PostgreSQL (prod env)
- **AI**: OpenAI GPT for intelligent analysis
- **Cloud**: AWS (S3, Lambda, RDS, CloudWatch)
- **Container**: Docker
- **Testing**: Pytest
