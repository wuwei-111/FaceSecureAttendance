param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$TeacherUsername = "teacher1",
  [string]$TeacherPassword = "123456",
  [string]$StudentUsername = "student1",
  [string]$StudentPassword = "123456",
  [int]$TimeoutSec = 8
)

$ErrorActionPreference = "Stop"

function Write-Section {
  param([string]$Title)
  Write-Host ""
  Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Get-StatusCode {
  param(
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers,
    [object]$Body
  )

  # Windows PowerShell 5.1：不加 -UseBasicParsing 会弹出“脚本执行风险”确认框，
  # 选“否”或默认回车会导致请求未发出，状态码变为 0，教师/学生登录结果不一致。
  $iwrParams = @{ UseBasicParsing = $true; TimeoutSec = $TimeoutSec }
  try {
    if ($Method -eq "POST") {
      $payload = $Body | ConvertTo-Json
      $iwrParams["Method"] = "POST"
      $iwrParams["Uri"] = $Url
      $iwrParams["ContentType"] = "application/json"
      $iwrParams["Body"] = $payload
      if ($Headers) { $iwrParams["Headers"] = $Headers }
      $resp = Invoke-WebRequest @iwrParams
    } else {
      $iwrParams["Method"] = "GET"
      $iwrParams["Uri"] = $Url
      if ($Headers) { $iwrParams["Headers"] = $Headers }
      $resp = Invoke-WebRequest @iwrParams
    }
    return [int]$resp.StatusCode
  } catch {
    if ($_.Exception.Response) {
      return [int]$_.Exception.Response.StatusCode.value__
    }
    return 0
  }
}

function Login-And-GetToken {
  param([string]$Username, [string]$Password)
  $resp = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/auth/login" -ContentType "application/json" -Body (@{
    username = $Username
    password = $Password
  } | ConvertTo-Json) -TimeoutSec $TimeoutSec
  return $resp.data.access_token
}

function Check {
  param([string]$Name, [int]$Expected, [int]$Actual)
  if ($Expected -eq $Actual) {
    Write-Host "[PASS] $Name => $Actual" -ForegroundColor Green
    return $true
  }
  Write-Host "[FAIL] $Name => expected $Expected, got $Actual" -ForegroundColor Red
  return $false
}

$results = @()

Write-Section "0) Health"
$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/health"
$ok = Check -Name "GET /health" -Expected 200 -Actual $s
$results += $ok
if (-not $ok) {
  Write-Host "Backend is not running. Start backend first." -ForegroundColor Yellow
  exit 1
}

Write-Section "1) Login"
$teacherLoginStatus = Get-StatusCode -Method "POST" -Url "$BaseUrl/api/auth/login" -Body @{ username = $TeacherUsername; password = $TeacherPassword }
$results += (Check -Name "POST /api/auth/login teacher" -Expected 200 -Actual $teacherLoginStatus)

$studentLoginStatus = Get-StatusCode -Method "POST" -Url "$BaseUrl/api/auth/login" -Body @{ username = $StudentUsername; password = $StudentPassword }
$results += (Check -Name "POST /api/auth/login student" -Expected 200 -Actual $studentLoginStatus)

if ($teacherLoginStatus -ne 200 -or $studentLoginStatus -ne 200) {
  Write-Host "Login failed. Stop verification." -ForegroundColor Yellow
  exit 1
}

$teacherToken = Login-And-GetToken -Username $TeacherUsername -Password $TeacherPassword
$studentToken = Login-And-GetToken -Username $StudentUsername -Password $StudentPassword
$teacherHeaders = @{ Authorization = "Bearer $teacherToken" }
$studentHeaders = @{ Authorization = "Bearer $studentToken" }

Write-Section "2) Core Auth"
$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/auth/me"
$results += (Check -Name "GET /api/auth/me no token" -Expected 401 -Actual $s)

$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/auth/me" -Headers $teacherHeaders
$results += (Check -Name "GET /api/auth/me teacher" -Expected 200 -Actual $s)

$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/auth/me" -Headers $studentHeaders
$results += (Check -Name "GET /api/auth/me student" -Expected 200 -Actual $s)

Write-Section "3) Teacher-only"
$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/students" -Headers $teacherHeaders
$results += (Check -Name "GET /api/students teacher" -Expected 200 -Actual $s)

$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/students" -Headers $studentHeaders
$results += (Check -Name "GET /api/students student" -Expected 403 -Actual $s)

$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/emotion/stats" -Headers $teacherHeaders
$results += (Check -Name "GET /api/emotion/stats teacher" -Expected 200 -Actual $s)

$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/emotion/stats" -Headers $studentHeaders
$results += (Check -Name "GET /api/emotion/stats student" -Expected 403 -Actual $s)

Write-Section "4) Attendance"
$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/attendance/records?page=1&page_size=2"
$results += (Check -Name "GET /api/attendance/records no token" -Expected 401 -Actual $s)

$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/attendance/records?page=1&page_size=2" -Headers $teacherHeaders
$results += (Check -Name "GET /api/attendance/records teacher" -Expected 200 -Actual $s)

$s = Get-StatusCode -Method "GET" -Url "$BaseUrl/api/attendance/records?page=1&page_size=2" -Headers $studentHeaders
$results += (Check -Name "GET /api/attendance/records student" -Expected 200 -Actual $s)

Write-Section "Summary"
$total = $results.Count
$passed = ($results | Where-Object { $_ -eq $true }).Count
$failed = $total - $passed
Write-Host "Total: $total, Passed: $passed, Failed: $failed"

if ($failed -gt 0) {
  exit 1
}
