# Teams Meeting Transcript Helper - Implementation Plan

## Context

Build a single AI agent (Azure Function + Kimi-K2.5 via `azure-ai-inference` SDK) that processes Teams meeting transcripts and writes structured markdown summaries to GitHub. Triggered primarily via Power Automate. The project folder `D:\Repositories\Reply\transript_helper` already has a git repo. User will provide secrets/config data after coding is complete.

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

Single agent pipeline — no multi-agent orchestration needed.

## Project Structure

```
transript_helper/
├── function_app.py                  # Azure Function HTTP trigger entry point
├── services/
│   ├── __init__.py
│   ├── summarizer.py                # Kimi-K2.5 via azure-ai-inference
│   ├── github_writer.py             # PyGithub file create/update
│   └── transcript_parser.py         # WebVTT parsing + speaker consolidation
├── prompts/
│   ├── __init__.py
│   └── system_prompt.py             # System prompt for meeting summaries
├── models/
│   ├── __init__.py
│   └── request_models.py            # Pydantic request validation
├── infra/
│   ├── main.tf                      # Terraform root module
│   ├── variables.tf                 # Input variables with defaults
│   ├── outputs.tf                   # Outputs (function URL, resource IDs)
│   ├── providers.tf                 # AzureRM provider config
│   └── modules/
│       ├── function_app/
│       │   ├── main.tf              # Function App + App Service Plan + Storage
│       │   ├── variables.tf
│       │   └── outputs.tf
│       └── monitoring/
│           ├── main.tf              # Application Insights + Log Analytics
│           ├── variables.tf
│           └── outputs.tf
├── tests/
│   ├── __init__.py
│   ├── test_transcript_parser.py
│   ├── test_summarizer.py
│   ├── test_github_writer.py
│   ├── test_function_app.py
│   └── fixtures/
│       └── sample_transcript.vtt
├── host.json                        # Azure Functions config (5min timeout)
├── local.settings.json.example      # Template for local dev settings
├── requirements.txt                 # Python dependencies
├── bootstrap.bat                    # Azure CLI commands not covered by Terraform
├── .funcignore
├── .gitignore
├── .env.example
├── SETUP_GUIDE.md                   # Bootstrap checklist: automated vs manual
└── README.md                        # Full docs with all trigger alternatives
```

## Implementation Steps

### Step 1: Scaffold project (automated by Claude)
- Create all config files: `.gitignore`, `.funcignore`, `requirements.txt`, `host.json`
- Create `local.settings.json.example` and `.env.example`

### Step 2: Core services (automated by Claude)
- `services/transcript_parser.py` — Parse WebVTT, consolidate consecutive speakers
- `services/summarizer.py` — ChatCompletionsClient singleton, call Kimi-K2.5
- `services/github_writer.py` — PyGithub create/update with sanitized filenames
- `prompts/system_prompt.py` — Detailed system prompt for structured summaries
- `models/request_models.py` — Pydantic validation for incoming requests

### Step 3: Azure Function entry point (automated by Claude)
- `function_app.py` — HTTP trigger, orchestrates parse → summarize → write → respond

### Step 4: Terraform infrastructure (automated by Claude)
- Resource Group
- Storage Account (for Azure Functions)
- App Service Plan (Consumption/Linux)
- Function App (Python 3.11)
- Application Insights + Log Analytics Workspace
- App Settings placeholders for secrets (user fills in later)

### Step 5: bootstrap.bat (automated by Claude)
- Deploy function code (`func azure functionapp publish`)
- Retrieve function keys
- Set app settings from user-provided values
- Entra ID app registration via `az ad app create`
- Grant API permissions via `az ad app permission`
- Create application access policy for Teams transcripts
- Test the endpoint with a sample POST

### Step 6: Tests (automated by Claude)
- Unit tests with mocked external services
- Sample VTT fixture file

### Step 7: Documentation (automated by Claude)
- `README.md` with architecture, config reference, all trigger alternatives
- `SETUP_GUIDE.md` with bootstrap checklist clearly marking automated vs manual

## What's Automated vs Manual

### Automated (Claude creates code/scripts/definitions):
- All Python source code (agent, services, models, prompts)
- Terraform for all Azure infrastructure
- bootstrap.bat for Azure CLI operations (deploy, configure, register app)
- Unit tests
- Documentation with step-by-step guides

### Manual (user must do):
- Provide: Kimi-K2.5 endpoint URL + API key from Foundry
- Provide: GitHub PAT + target repo name
- Provide: Azure subscription ID + desired region
- Run: `terraform apply` (after reviewing the plan)
- Run: `bootstrap.bat` (after filling in variables)
- Admin consent: Grant Entra ID API permissions in Azure Portal
- Admin action: Create Teams application access policy (PowerShell)
- Configure: Power Automate flow (UI-based, documented with screenshots description)
- Generate: GitHub Personal Access Token

## Key Design Decisions

- **API Key auth** for Kimi-K2.5 (Foundry provides key)
- **temperature=0.3** for factual, consistent summaries
- **File path convention**: `meeting-notes/YYYY-MM-DD/safe-meeting-title.md`
- **Idempotent writes**: update existing file if re-run for same meeting
- **Function auth level**: FUNCTION (key in URL) for Power Automate
- **5-minute timeout** in host.json for long transcripts
- **Terraform modules**: separated into function_app and monitoring for clarity
- **bootstrap.bat**: covers the "gap" between Terraform and fully working system

## Verification

1. Local: `func start` → POST sample transcript → verify markdown output
2. Tests: `pytest tests/ -v`
3. Deploy: `terraform apply` + `bootstrap.bat` → verify resources in Azure Portal
4. E2E: Power Automate trigger → verify GitHub file + Teams notification
