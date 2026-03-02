# Teams Meeting Transcript Helper

An Azure Function that processes Microsoft Teams meeting transcripts, generates structured markdown summaries using an AI model (Kimi-K2.5 / DeepSeek-R1 via Azure AI Foundry), and writes them to a GitHub repository.

## Architecture

```
Power Automate (trigger: meeting ends)
  → Azure Function (HTTP POST with transcript)
    → Parse WebVTT transcript (Python)
    → Summarize via Kimi-K2.5 (azure-ai-inference SDK)
    → Write markdown to GitHub (PyGithub)
    → Return summary URL
  → Power Automate posts link to Teams channel
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and fill in local settings
cp local.settings.json.example local.settings.json

# 3. Run locally
func start

# 4. Test
curl -X POST http://localhost:7071/api/summarize \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "transcript": "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\n<v Alice>Hello, let's discuss the roadmap.</v>\n\n00:00:05.000 --> 00:00:10.000\n<v Bob>Sure, I have updates on the backend migration.</v>",
  "meeting_title": "Roadmap Discussion",
  "meeting_date": "2024-01-15"
}
EOF
```

## API Reference

### POST `/api/summarize`

**Auth**: Function key (passed as `?code=` query parameter)

**Request body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | string | Yes | WebVTT transcript content |
| `meeting_title` | string | Yes | Meeting title (max 200 chars) |
| `meeting_date` | string | No | Date in `YYYY-MM-DD` format (defaults to today UTC) |

**Success response** (200):

```json
{
  "status": "success",
  "file_url": "https://github.com/owner/repo/blob/main/meeting-notes/2024-01-15/roadmap-discussion.md",
  "meeting_title": "Roadmap Discussion",
  "speakers": ["Alice", "Bob"]
}
```

**Error responses**:

| Code | Reason |
|------|--------|
| 400 | Invalid JSON or unparseable transcript |
| 422 | Validation failed (missing/invalid fields) |
| 502 | AI model or GitHub API error |

## Project Structure

```
transript_helper/
├── function_app.py              # HTTP trigger entry point
├── services/
│   ├── transcript_parser.py     # WebVTT parsing + speaker consolidation
│   ├── summarizer.py            # Kimi-K2.5 via azure-ai-inference
│   └── github_writer.py         # PyGithub file create/update
├── prompts/
│   └── system_prompt.py         # System prompt for meeting summaries
├── models/
│   └── request_models.py        # Pydantic request validation
├── infra/                       # Terraform infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── modules/
│       ├── function_app/        # Function App + Plan + Storage
│       └── monitoring/          # App Insights + Log Analytics
├── tests/                       # pytest unit tests
├── host.json                    # Azure Functions config (5min timeout)
├── requirements.txt
├── bootstrap.bat                # Azure CLI setup commands
├── SETUP_GUIDE.md               # Full deployment checklist
└── plan.md                      # Implementation plan
```

## Configuration

All configuration is via environment variables / Azure Function App Settings:

| Variable | Description |
|----------|-------------|
| `KIMI_ENDPOINT` | Azure AI Foundry model endpoint URL |
| `KIMI_API_KEY` | API key for the model endpoint |
| `KIMI_MODEL_NAME` | Model deployment name (default: `DeepSeek-R1`) |
| `GITHUB_TOKEN` | GitHub Personal Access Token with repo write access |
| `GITHUB_REPO` | Target repo in `owner/repo` format |
| `GITHUB_BRANCH` | Branch to write to (default: `main`) |

## Deployment

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for the full deployment checklist.

Summary:

1. Fill in `infra/terraform.tfvars`
2. `cd infra && terraform init && terraform apply`
3. Run `bootstrap.bat` to deploy code and configure Entra ID
4. Grant admin consent in Azure Portal
5. Configure Power Automate flow

## Testing

```bash
pip install -r requirements.txt
pip install pytest
pytest tests/ -v
```

## Output Format

Generated meeting notes follow this structure:

```markdown
# {Meeting Title}

**Date:** YYYY-MM-DD
**Participants:** Speaker1, Speaker2, ...

## Summary
2-4 sentence overview.

## Key Discussion Points
- **Topic:** Description

## Decisions Made
- Decision item

## Action Items
| Owner | Action | Due Date |
|-------|--------|----------|
| Name  | Task   | Date     |

## Open Questions
- Unresolved question
```

Files are written to: `meeting-notes/YYYY-MM-DD/{sanitized-title}.md`

Idempotent: re-running for the same meeting updates the existing file.

## Trigger Alternatives

While Power Automate is the primary trigger, you can also invoke the function from:

- **Logic Apps**: Same HTTP POST, useful if Power Automate isn't available
- **Graph API Webhooks**: Subscribe to `callRecords` change notifications
- **Manual/CLI**: `curl` or any HTTP client for testing or ad-hoc summaries
- **Azure Event Grid**: Route events from Teams to the function

## Future: Azure AI Foundry Hosted Agent Migration

This project is designed with a migration path to Azure AI Foundry Hosted Agents:

### Current Architecture (Azure Function)
- Direct HTTP trigger → synchronous processing → response
- Function manages its own compute, scaling, and lifecycle

### Future Architecture (Foundry Hosted Agent)
- Agent registered in Azure AI Foundry
- Tools defined as OpenAPI specs (GitHub write, transcript parse)
- Model orchestration handled by Foundry runtime
- Benefits: built-in conversation memory, tool routing, observability

### Migration Steps
1. Convert `services/` functions to Foundry tool definitions (OpenAPI)
2. Register agent in Foundry with the system prompt from `prompts/system_prompt.py`
3. Configure Foundry agent endpoint as the Power Automate target
4. Decommission the Azure Function (or keep as fallback)

The service layer (`services/`) is intentionally decoupled from the function trigger to make this migration straightforward.
