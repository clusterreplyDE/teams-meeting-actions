@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM Teams Transcript Helper - Bootstrap Script
REM
REM Covers Azure CLI operations that Terraform doesn't handle:
REM   1. Deploy function code
REM   2. Retrieve function key
REM   3. Register Entra ID app (for future Teams Graph API access)
REM   4. Test the endpoint
REM
REM Prerequisites:
REM   - Azure CLI installed and logged in (az login)
REM   - Azure Functions Core Tools installed (npm i -g azure-functions-core-tools@4)
REM   - Terraform has been applied (infra resources exist)
REM ============================================================================

REM --- Configuration (edit these before running) ---
set RESOURCE_GROUP=rg-transcript-helper-dev
set FUNCTION_APP_NAME=func-transcript-helper-dev
set APP_DISPLAY_NAME=TranscriptHelper

echo.
echo ============================================================
echo  Teams Transcript Helper - Bootstrap
echo ============================================================
echo.

REM --- Step 1: Deploy function code ---
echo [1/4] Deploying function code to %FUNCTION_APP_NAME%...
pushd "%~dp0"
func azure functionapp publish %FUNCTION_APP_NAME% --python
if %ERRORLEVEL% neq 0 (
    echo ERROR: Function deployment failed. Ensure func CLI is installed and you are logged in.
    exit /b 1
)
popd
echo       Deploy complete.
echo.

REM --- Step 2: Retrieve function key ---
echo [2/4] Retrieving function key...
for /f "delims=" %%k in ('az functionapp keys list -g %RESOURCE_GROUP% -n %FUNCTION_APP_NAME% --query "functionKeys.default" -o tsv 2^>nul') do set FUNC_KEY=%%k
if defined FUNC_KEY (
    echo       Function key: %FUNC_KEY%
    echo       Endpoint:     https://%FUNCTION_APP_NAME%.azurewebsites.net/api/summarize?code=%FUNC_KEY%
) else (
    echo       WARNING: Could not retrieve function key. You may need to get it from the Azure Portal.
)
echo.

REM --- Step 3: Register Entra ID application (for future Graph API access) ---
echo [3/4] Registering Entra ID application: %APP_DISPLAY_NAME%...
for /f "delims=" %%a in ('az ad app create --display-name %APP_DISPLAY_NAME% --query "appId" -o tsv 2^>nul') do set APP_ID=%%a
if defined APP_ID (
    echo       App ID: %APP_ID%

    REM Request Graph API permissions for reading meeting transcripts
    REM OnlineMeetingTranscript.Read.All (application) = a]4a08bf-dc32-4845-ac37-05f258c52570
    echo       Adding Graph API permission: OnlineMeetingTranscript.Read.All...
    az ad app permission add --id %APP_ID% --api 00000003-0000-0000-c000-000000000000 --api-permissions a4a08bf-dc32-4845-ac37-05f258c52570=Role >nul 2>&1

    echo.
    echo       MANUAL STEP REQUIRED:
    echo       Grant admin consent in Azure Portal:
    echo       https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/%APP_ID%
    echo.
    echo       Then create an application access policy for Teams:
    echo         Install-Module Microsoft.Graph -Scope CurrentUser
    echo         Connect-MgGraph -Scopes "OnlineMeetingTranscript.Read.All"
    echo         New-CsApplicationAccessPolicy -Identity "TranscriptReaderPolicy" ^
    echo           -AppIds "%APP_ID%" -Description "Allow reading meeting transcripts"
) else (
    echo       WARNING: Entra ID app registration failed. You may need to register manually.
)
echo.

REM --- Step 4: Test the endpoint ---
echo [4/4] Testing endpoint...
if defined FUNC_KEY (
    echo       Sending test request...
    curl -s -X POST "https://%FUNCTION_APP_NAME%.azurewebsites.net/api/summarize?code=%FUNC_KEY%" ^
         -H "Content-Type: application/json" ^
         -d "{\"transcript\": \"WEBVTT\n\n00:00:00.000 --^> 00:00:05.000\n<v Test User>Hello, this is a test meeting.</v>\", \"meeting_title\": \"Bootstrap Test\"}"
    echo.
) else (
    echo       Skipping test (no function key available).
)

echo.
echo ============================================================
echo  Bootstrap complete!
echo.
echo  Next steps:
echo    1. Grant admin consent for Entra ID app (see URL above)
echo    2. Create Teams application access policy (PowerShell)
echo    3. Configure Power Automate flow (see SETUP_GUIDE.md)
echo ============================================================

endlocal
