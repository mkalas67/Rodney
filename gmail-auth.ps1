# Gmail OAuth token fetcher - uses Web App client, listens on port 8080/callback

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("gmail-marta","gmail-opencpd")]
    [string]$Server
)

# Load credentials from config file (not committed to git)
. "$PSScriptRoot\gmail-auth-config.ps1"
$Port         = 8080
$CredFile     = "D:\Users\Marta\.claude\.credentials.json"

$Resource        = "https://gmailmcp.googleapis.com/mcp"
$ScopesEncoded   = "openid+email+https%3A%2F%2Fmail.google.com%2F+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.compose+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.metadata+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.labels"
$ResourceEncoded = "https%3A%2F%2Fgmailmcp.googleapis.com%2Fmcp"
$RedirectEncoded = "http%3A%2F%2Flocalhost%3A8080%2Fcallback"

# Build auth URL
$State   = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(16)).Replace("+","-").Replace("/","_").TrimEnd("=")
$AuthUrl = "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=$ClientId&redirect_uri=$RedirectEncoded&scope=$ScopesEncoded&state=$State&access_type=offline&prompt=consent&resource=$ResourceEncoded"

Write-Host ""
Write-Host "=== Gmail OAuth for $Server ===" -ForegroundColor Cyan
Write-Host "Opening browser... Sign in as:" -ForegroundColor Yellow
if ($Server -eq "gmail-marta") {
    Write-Host "  marta@martakalas.com" -ForegroundColor Green
} else {
    Write-Host "  info@open-cpd.com" -ForegroundColor Green
}
Write-Host ""

# Open browser
Start-Process $AuthUrl

# Start local HTTP listener
$Listener = [System.Net.HttpListener]::new()
$Listener.Prefixes.Add("http://localhost:$Port/callback/")
$Listener.Start()
Write-Host "Waiting for OAuth callback on port $Port/callback..." -ForegroundColor Gray

$Context  = $Listener.GetContext()
$Request  = $Context.Request
$Response = $Context.Response

# Send success page
$Html = "<html><body><h2>Auth complete - you can close this tab.</h2></body></html>"
$Bytes = [System.Text.Encoding]::UTF8.GetBytes($Html)
$Response.ContentLength64 = $Bytes.Length
$Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
$Response.Close()
$Listener.Stop()

# Parse callback params
$Query      = $Request.Url.Query.TrimStart("?")
$Params     = @{}
foreach ($pair in $Query.Split("&")) {
    $kv = $pair.Split("=", 2)
    if ($kv.Length -eq 2) { $Params[$kv[0]] = [System.Web.HttpUtility]::UrlDecode($kv[1]) }
}

if ($Params["error"]) {
    Write-Host "ERROR from Google: $($Params['error'])" -ForegroundColor Red
    exit 1
}

$Code = $Params["code"]
if (-not $Code) {
    Write-Host "No code received in callback." -ForegroundColor Red
    exit 1
}

Write-Host "Got auth code. Exchanging for tokens..." -ForegroundColor Gray

# Exchange code for tokens
$Body = "grant_type=authorization_code&code=$([Uri]::EscapeDataString($Code))&redirect_uri=$RedirectEncoded&client_id=$([Uri]::EscapeDataString($ClientId))&client_secret=$([Uri]::EscapeDataString($ClientSecret))"

try {
    $TokenResponse = Invoke-RestMethod -Method Post -Uri "https://oauth2.googleapis.com/token" -ContentType "application/x-www-form-urlencoded" -Body $Body
} catch {
    Write-Host "Token exchange failed: $_" -ForegroundColor Red
    exit 1
}

$AccessToken  = $TokenResponse.access_token
$RefreshToken = $TokenResponse.refresh_token
$ExpiresIn    = $TokenResponse.expires_in
$ExpiresAt    = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + ($ExpiresIn * 1000)

if (-not $AccessToken) {
    Write-Host "No access token in response." -ForegroundColor Red
    Write-Host ($TokenResponse | ConvertTo-Json)
    exit 1
}

Write-Host "Tokens received! Writing to credentials file..." -ForegroundColor Green

# Read credentials file
$Creds = Get-Content $CredFile -Raw | ConvertFrom-Json

# Find the key for this server (format: "gmail-marta|<deviceid>")
$Key = ($Creds.mcpOAuth.PSObject.Properties | Where-Object { $_.Name -like "$Server|*" }).Name

if (-not $Key) {
    Write-Host "Could not find key for '$Server' in credentials file." -ForegroundColor Red
    Write-Host "Existing keys: $($Creds.mcpOAuth.PSObject.Properties.Name -join ', ')"
    exit 1
}

Write-Host "Updating key: $Key" -ForegroundColor Gray

# Update the token fields
$Creds.mcpOAuth.$Key.accessToken  = $AccessToken
$Creds.mcpOAuth.$Key | Add-Member -NotePropertyName "refreshToken" -NotePropertyValue $RefreshToken -Force
$Creds.mcpOAuth.$Key | Add-Member -NotePropertyName "expiresAt"    -NotePropertyValue $ExpiresAt    -Force

# Write back
$Creds | ConvertTo-Json -Depth 10 | Set-Content $CredFile -Encoding utf8

Write-Host ""
Write-Host "=== Done! $Server is authenticated ===" -ForegroundColor Cyan
Write-Host "Access token expires in $ExpiresIn seconds (~$([math]::Round($ExpiresIn/3600,1)) hours)"
Write-Host "Refresh token stored: $(if($RefreshToken){'YES'}else{'NO - re-auth will be needed'})"
