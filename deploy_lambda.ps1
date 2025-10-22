# Variables configurables
$REGION   = "us-east-1"
$FUNC     = "finance-news-scraper"
$ROLENAME = "lambda-scrape-and-summarize-role"
$ROLE_ARN = $(aws iam get-role --role-name $ROLENAME --query "Role.Arn" --output text)
$ZIP      = "lambda_package.zip"
$APIKEY   = "TU_OPENAI_API_KEY"

if (-not $ROLE_ARN -or $ROLE_ARN -eq "None") {
  throw "No encuentro el rol '$ROLENAME'. Crealo o revisá el nombre."
}

# Crear Lambda (si ya existe, pasa a update)
$created = $true
try {
  aws lambda create-function `
    --function-name $FUNC `
    --runtime python3.12 `
    --role $ROLE_ARN `
    --handler scrape_and_summarize.lambda_handler `
    --zip-file fileb://$ZIP `
    --timeout 60 `
    --memory-size 1024 `
    --region $REGION | Out-Null
} catch {
  $created = $false
  Write-Host "create-function falló (probablemente ya existe). Sigo con update..."
}

# Actualizar código si ya existía
if (-not $created) {
  aws lambda update-function-code `
    --function-name $FUNC `
    --zip-file fileb://$ZIP `
    --region $REGION | Out-Null
}

# Variables de entorno
aws lambda update-function-configuration `
  --function-name $FUNC `
  --environment Variables="{OPENAI_API_KEY=$APIKEY}" `
  --region $REGION | Out-Null

# Invocar y mostrar salida
aws lambda invoke --function-name $FUNC --region $REGION out.json | Out-Null
Get-Content .\out.json
