param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 5173
)

$rootLauncher = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'scripts\run.ps1'
& $rootLauncher -ApiPort $ApiPort -WebPort $WebPort
