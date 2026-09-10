# Build the Lambda deployment package.
$ErrorActionPreference = "Stop"

$BuildDir = "build/lambda"
$ZipPath = "infra/lambda.zip"

if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null

# Dependencies (boto3 is provided by the Lambda runtime).
pip install `
    --target $BuildDir `
    --only-binary=:all: `
    --platform manylinux2014_x86_64 `
    --python-version 3.12 `
    requests python-dotenv tenacity pydantic

# Application code.
Copy-Item -Path "src" -Destination "$BuildDir/src" -Recurse

Compress-Archive -Path "$BuildDir/*" -DestinationPath $ZipPath -Force

$size = (Get-Item $ZipPath).Length / 1MB
Write-Host ("built {0} ({1:N1} MB)" -f $ZipPath, $size)