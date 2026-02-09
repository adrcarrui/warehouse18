$zip = "warehouse18_code.zip"

if (Test-Path $zip) {
    Remove-Item $zip
}

Compress-Archive `
  -Path * `
  -DestinationPath $zip `
  -CompressionLevel Optimal `
  -Exclude ".git\*", ".venv\*", "__pycache__\*"

Write-Host "ZIP listo para revisión: $zip"
