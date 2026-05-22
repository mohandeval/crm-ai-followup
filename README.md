# AI CRM Follow-Up Workflow

End-to-end AI-powered sales follow-up system using PostgreSQL, LangGraph, OpenAI, and Pinecone.

## Architecture

```
Postgres CRM Data (sales_raw schema)
        ↓  src/db/queries.py
Flatten + Normalize Activities
        ↓  src/graph/nodes/format_activities.py   [Part 3]
Retrieve Lead By Owner Email
        ↓  src/graph/nodes/retrieve_leads.py      [Part 2]
Analyze Lead With LLM
        ↓  src/agents/llm_analyzer.py             [Part 4]
Retrieve Relevant Nurture Content
        ↓  src/vector/pinecone_client.py           [Part 5]
Select Best Content
        ↓  src/agents/content_selector.py         [Part 6]
Generate Personalized Follow-Up Email
        ↓  src/agents/email_generator.py          [Part 7]
Store Output (Postgres)
```

## Module Map

| Part | Description | Location |
|------|-------------|----------|
| Part 1 | DB Modeling | `src/db/` |
| Part 2 | Lead Retrieval | `src/db/queries.py` |
| Part 3 | Activity Formatting | `src/graph/nodes/format_activities.py` |
| Part 4 | LLM Analysis Engine | `src/agents/llm_analyzer.py` |
| Part 5 | Embedding + Retrieval | `src/vector/` |
| Part 6 | Content Selection Agent | `src/agents/content_selector.py` |
| Part 7 | Email Generation | `src/agents/email_generator.py` |
| Part 8 | LangGraph Workflow | `src/graph/workflow.py` |
| Part 9 | Evaluation | `src/utils/evaluator.py` |

## Quick Start

```bash
# 1. Clone & enter
cd D:\AiCode\AICRMCode\crm-ai-followup

# 2. Create virtual environment
python -m venv .crmai_venv
.crmai_venv\Scripts\activate          # Windows
# source .crmai_venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env — add your OPENAI_API_KEY and PINECONE_API_KEY

# 5. Verify connections
python scripts/test_connections.py
```

## Database (Provided)

- **Host:** dea.cgyi97rb4alr.us-east-1.rds.amazonaws.com
- **DB:** dea_analytics_dev
- **Schema:** sales_raw
- **Tables:** leads_raw, lead_activites_raw, close_crm_users_raw, custom_activites_raw, fathom_recordings_raw, ai_nurturing_content

## External Services to Set Up

1. **OpenAI API** — https://platform.openai.com/api-keys
2. **Pinecone Serverless** — https://www.pinecone.io/ (free tier)
3. **LangSmith** (optional tracing) — https://smith.langchain.com/

## Pipeline Schedule

Runs twice daily via scheduler (07:30 AM and 7:30 PM EST).
