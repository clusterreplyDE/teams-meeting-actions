# Setup Guide - Teams Transcript Helper

Step-by-step checklist to go from code to a working deployment. Items marked **[Auto]** are handled by scripts/Terraform; items marked **[Manual]** require your action.

## Prerequisites

- [x] **[Auto]** Code is written and ready to deploy
- [ ] **[Manual]** Azure CLI installed and authenticated (`az login`)
- [ ] **[Manual]** Azure Functions Core Tools v4 installed (`npm i -g azure-functions-core-tools@4`)
- [ ] **[Manual]** Terraform >= 1.5 installed
- [ ] **[Manual]** Python 3.11 installed locally (for `func start`)
- [ ] **[Manual]** Git installed

## Step 1: Gather Configuration Values

You'll need these before proceeding:

| Value | Where to get it | Used in |
|-------|-----------------|---------|
| Azure Subscription ID | Azure Portal → Subscriptions | `terraform.tfvars` |
| Kimi-K2.5 Endpoint URL | Azure AI Foundry → Model Deployments | `terraform.tfvars` |
| Kimi-K2.5 API Key | Azure AI Foundry → Model Deployments | `terraform.tfvars` |
| GitHub PAT | GitHub → Settings → Developer Settings → Tokens | `terraform.tfvars` |
| GitHub Repo (owner/repo) | Your target repository for meeting notes | `terraform.tfvars` |

### Create `infra/terraform.tfvars`

```hcl
subscription_id = "your-subscription-id"
kimi_endpoint   = "https://your-endpoint.models.ai.azure.com"
kimi_api_key    = "your-api-key"
kimi_model_name = "DeepSeek-R1"
github_token    = "ghp_your_token"
github_repo     = "your-org/meeting-notes"
github_branch   = "main"
```

> **Note:** Add `terraform.tfvars` to `.gitignore` (already included).

## Step 2: Deploy Infrastructure **[Auto]**

```bash
cd infra
terraform init
terraform plan -out=tfplan
# Review the plan, then:
terraform apply tfplan
```

This creates:
- Resource Group
- Storage Account
- App Service Plan (Consumption/Linux)
- Function App (Python 3.11)
- Log Analytics Workspace
- Application Insights

## Step 3: Deploy Function Code **[Auto]**

```bash
# From the project root:
func azure functionapp publish func-transcript-helper-dev --python
```

Or use `bootstrap.bat` which does this and more.

## Step 4: Run Bootstrap Script **[Semi-Auto]**

Edit the variables at the top of `bootstrap.bat`, then run it:

```bash
bootstrap.bat
```

This will:
1. Deploy function code
2. Retrieve the function key
3. Register an Entra ID app (for future Teams Graph API)
4. Test the endpoint with a sample request

## Step 5: Grant Admin Consent **[Manual]**

After `bootstrap.bat` registers the Entra ID app:

1. Go to Azure Portal → App Registrations → TranscriptHelper
2. Navigate to API Permissions
3. Click "Grant admin consent for [your tenant]"

## Step 6: Create Teams Application Access Policy **[Manual]**

Run in PowerShell:

```powershell
Install-Module Microsoft.Graph -Scope CurrentUser
Connect-MgGraph -Scopes "OnlineMeetingTranscript.Read.All"

# Replace <APP_ID> with the App ID from bootstrap output
New-CsApplicationAccessPolicy -Identity "TranscriptReaderPolicy" `
  -AppIds "<APP_ID>" `
  -Description "Allow reading meeting transcripts"
```

## Step 7: Create GitHub PAT **[Manual]**

1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
2. Create a token with:
   - **Repository access**: Only the target meeting-notes repo
   - **Permissions**: Contents → Read and write
3. Copy the token into your `terraform.tfvars`

## Step 8: Configure Power Automate Flow **[Manual]**

Create a new Power Automate flow:

1. **Trigger**: "When a Teams meeting ends" (or scheduled recurrence)
2. **Action**: Get meeting transcript (Graph API)
3. **Action**: HTTP POST to your Function endpoint
   - URL: `https://func-transcript-helper-dev.azurewebsites.net/api/summarize?code=<FUNCTION_KEY>`
   - Body:
     ```json
     {
       "transcript": "<transcript content>",
       "meeting_title": "<meeting subject>",
       "meeting_date": "<meeting date YYYY-MM-DD>"
     }
     ```
4. **Action**: Post message to Teams channel with the `file_url` from the response

## Step 9: Test End-to-End **[Manual]**

### Local testing:

```bash
# Copy local.settings.json.example → local.settings.json and fill in values
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your values

func start

# In another terminal:
curl -X POST http://localhost:7071/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"transcript": "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\n<v Test>Hello world</v>", "meeting_title": "Test Meeting"}'
```

### Run tests:

```bash
pip install -r requirements.txt
pip install pytest
pytest tests/ -v
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `func start` fails | Ensure Python 3.11 is active, run `pip install -r requirements.txt` |
| 502 from summarize | Check KIMI_ENDPOINT and KIMI_API_KEY in App Settings |
| GitHub write fails | Verify GITHUB_TOKEN has write access to the target repo |
| Terraform fails | Run `az login` and verify subscription ID |
| Function key not found | Check Azure Portal → Function App → App Keys |
