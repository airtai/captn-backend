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
check_variable "AZURE_OPENAI_API_KEY_SWEDEN"
check_variable "INFOBIP_BASE_URL"
check_variable "INFOBIP_API_KEY"


if [ ! -f key.pem ]; then
    echo "ERROR: key.pem file not found"
    exit -1
fi


ssh_command="ssh -o StrictHostKeyChecking=no -i key.pem azureuser@$DOMAIN"

echo "INFO: stopping already running docker container"
$ssh_command "docker stop captn-backend || echo 'No containers available to stop'"
$ssh_command "docker container prune -f || echo 'No stopped containers to delete'"

echo "INFO: pulling docker image"
$ssh_command "echo $GITHUB_PASSWORD | docker login -u '$GITHUB_USERNAME' --password-stdin '$REGISTRY'"
$ssh_command "docker pull ghcr.io/$GITHUB_REPOSITORY:'$TAG'"
sleep 10

echo "Deleting old image"
$ssh_command "docker system prune -f || echo 'No images to delete'"

echo "INFO: starting docker container"
$ssh_command "docker run --name captn-backend \
	-p 8080:8080 -p $PORT:$PORT -v /etc/letsencrypt:/letsencrypt -e PORT='$PORT' -e DATABASE_URL='$DATABASE_URL' -e CLIENT_SECRET='$CLIENT_SECRET' \
	-e DEVELOPER_TOKEN='$DEVELOPER_TOKEN' \
	-e AZURE_API_VERSION='$AZURE_API_VERSION' -e AZURE_API_ENDPOINT='$AZURE_API_ENDPOINT' \
	-e AZURE_GPT4_MODEL='$AZURE_GPT4_MODEL' -e AZURE_GPT35_MODEL='$AZURE_GPT35_MODEL' \
	-e AZURE_OPENAI_API_KEY_SWEDEN='$AZURE_OPENAI_API_KEY_SWEDEN' \
	-e INFOBIP_BASE_URL='$INFOBIP_BASE_URL' -e INFOBIP_API_KEY='$INFOBIP_API_KEY' -e REACT_APP_API_URL='$REACT_APP_API_URL' \
	-e REDIRECT_DOMAIN='$REDIRECT_DOMAIN' \
	-d ghcr.io/$GITHUB_REPOSITORY:$TAG"
