#!/bin/bash

# Variables configurables
REGION="us-east-1"
FUNC="finance-news-scraper"
ROLENAME="lambda-scrape-and-summarize-role"
ROLE_ARN=$(aws iam get-role --role-name $ROLENAME --query "Role.Arn" --output text)
ZIP="lambda_package.zip"
# APIKEY debe ser configurado como variable de entorno
APIKEY="${OPENAI_API_KEY:-}"

if [ -z "$ROLE_ARN" ] || [ "$ROLE_ARN" == "None" ]; then
  echo "No encuentro el rol '$ROLENAME'. Crealo o revisa el nombre."
  exit 1
fi

if [ -z "$APIKEY" ]; then
  echo "Error: OPENAI_API_KEY no está configurada. Exporta la variable de entorno antes de ejecutar."
  exit 1
fi

# Crear entorno virtual e instalar dependencias
if [ -d "package" ]; then
  rm -rf package
fi
mkdir package
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt --target package/
deactivate

# Crear archivo ZIP con dependencias y código
cd package
zip -r ../$ZIP .
cd ..
zip -g $ZIP src/scraper/scrape_and_summarize.py config/logger_utils.py src/scraper/save_bucket.py config/config.py

# Crear Lambda (si ya existe, pasa a update)
created=true
aws lambda create-function \
  --function-name $FUNC \
  --runtime python3.12 \
  --role $ROLE_ARN \
  --handler scrape_and_summarize.lambda_handler \
  --zip-file fileb://$ZIP \
  --timeout 60 \
  --memory-size 1024 \
  --region $REGION > /dev/null 2>&1 || created=false

if [ "$created" = false ]; then
  echo "create-function falló (probablemente ya existe). Sigo con update..."

  # Esperar a que no haya operaciones pendientes antes de actualizar el código
  while [ "$(aws lambda get-function --function-name $FUNC --query 'Configuration.LastUpdateStatus' --output text)" != "Successful" ]; do
    echo "Esperando a que se complete la operación anterior..."
    sleep 5
  done

  aws lambda update-function-code \
    --function-name $FUNC \
    --zip-file fileb://$ZIP \
    --region $REGION > /dev/null

  # Esperar a que no haya operaciones pendientes antes de actualizar la configuración
  while [ "$(aws lambda get-function --function-name $FUNC --query 'Configuration.LastUpdateStatus' --output text)" != "Successful" ]; do
    echo "Esperando a que se complete la operación anterior..."
    sleep 5
  done
fi

# Variables de entorno
aws lambda update-function-configuration \
  --function-name $FUNC \
  --environment Variables="{OPENAI_API_KEY=$APIKEY}" \
  --region $REGION > /dev/null

# Invocar y mostrar salida
aws lambda invoke --function-name $FUNC --region $REGION out.json > /dev/null
cat out.json

echo "Deployment completado!"
