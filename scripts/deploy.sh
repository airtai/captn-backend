#!/bin/bash


check_variable() {
    if [[ -z "${!1}" ]]; then
        echo "ERROR: $1 variable must be defined, exiting"
        exit -1
    fi
}

check_variable "TAG"
check_variable "GITHUB_USERNAME"
check_variable "GITHUB_PASSWORD"
check_variable "DOMAIN"
check_variable "PORT"
check_variable "DATABASE_URL"
check_variable "CLIENT_SECRET"
check_variable "AZURE_API_VERSION"
check_variable "AZURE_API_ENDPOINT"
check_variable "AZURE_GPT4_MODEL"
check_variable "AZURE_GPT35_MODEL"
check_variable "DEVELOPER_TOKEN"
check_variable "AZURE_OPENAI_API_KEY"
check_variable "AZURE_API_ENDPOINT_GPT4O"
check_variable "AZURE_GPT4O_MODEL"
check_variable "AZURE_OPENAI_API_KEY_GPT4O"
check_variable "INFOBIP_BASE_URL"
check_variable "INFOBIP_API_KEY"
check_variable "GOOGLE_SHEETS_OPENAPI_URL"


if [ ! -f key.pem ]; then
    echo "ERROR: key.pem file not found"
    exit -1
fi


ssh_command="ssh -o StrictHostKeyChecking=no -i key.pem azureuser@$DOMAIN"

container_name="captn-backend"
log_file="${container_name}.log"

echo "INFO: Capturing docker container logs"
$ssh_command "docker logs $container_name >> $log_file 2>&1 || echo 'No container logs to capture'"

# Check if log file size exceeds 1GB (1073741824 bytes) and trim if necessary
$ssh_command "if [ \$(stat -c%s \"$log_file\") -ge 1073741824 ]; then echo 'Log file size exceeds 1GB, trimming...'; tail -c 1073741824 \"$log_file\" > \"$log_file.tmp\" && mv \"$log_file.tmp\" \"$log_file\"; fi"

echo "INFO: stopping already running docker containers"
$ssh_command "export PORT='$PORT' && docker-compose down || echo 'No containers available to stop'"
$ssh_command "docker container prune -f || echo 'No stopped containers to delete'"

echo "INFO: SCPing docker-compose.yaml"
scp -i key.pem ./docker-compose.yaml azureuser@$DOMAIN:/home/azureuser/docker-compose.yaml
envsubst '${INFOBIP_API_KEY}' < ./etc/grafana.ini > tmp.ini && mv tmp.ini ./etc/grafana.ini
scp -i key.pem -r ./etc azureuser@$DOMAIN:/home/azureuser

echo "INFO: pulling docker image"
$ssh_command "echo $GITHUB_PASSWORD | docker login -u '$GITHUB_USERNAME' --password-stdin '$REGISTRY'"
$ssh_command "docker pull ghcr.io/$GITHUB_REPOSITORY:'$TAG'"
sleep 10

echo "Deleting old image"
$ssh_command "docker system prune -f || echo 'No images to delete'"

echo "INFO: starting docker containers"

$ssh_command "export GITHUB_REPOSITORY='$GITHUB_REPOSITORY' TAG='$TAG' container_name='$container_name' \
	PORT='$PORT' DATABASE_URL='$DATABASE_URL' CLIENT_SECRET='$CLIENT_SECRET' \
	DEVELOPER_TOKEN='$DEVELOPER_TOKEN' \
	AZURE_API_VERSION='$AZURE_API_VERSION' AZURE_API_ENDPOINT='$AZURE_API_ENDPOINT' \
	AZURE_GPT4_MODEL='$AZURE_GPT4_MODEL' AZURE_GPT35_MODEL='$AZURE_GPT35_MODEL' \
	AZURE_OPENAI_API_KEY='$AZURE_OPENAI_API_KEY' \
	AZURE_API_ENDPOINT_GPT4O='$AZURE_API_ENDPOINT_GPT4O' AZURE_OPENAI_API_KEY_GPT4O='$AZURE_OPENAI_API_KEY_GPT4O' \
	AZURE_GPT4O_MODEL='$AZURE_GPT4O_MODEL' \
	INFOBIP_BASE_URL='$INFOBIP_BASE_URL' INFOBIP_API_KEY='$INFOBIP_API_KEY' REACT_APP_API_URL='$REACT_APP_API_URL' \
	REDIRECT_DOMAIN='$REDIRECT_DOMAIN' \
	DOMAIN='$DOMAIN' \
	GOOGLE_SHEETS_OPENAPI_URL='$GOOGLE_SHEETS_OPENAPI_URL' \
	&& docker-compose up -d"
