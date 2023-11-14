#!/bin/bash


if test -z "$TAG"
then
	echo "ERROR: TAG variable must be defined, exiting"
	exit -1
fi

if test -z "$GITHUB_USERNAME"
then
	echo "ERROR: GITHUB_USERNAME variable must be defined, exiting"
	exit -1
fi

if test -z "$GITHUB_PASSWORD"
then
	echo "ERROR: GITHUB_PASSWORD variable must be defined, exiting"
	exit -1
fi


if [ ! -f key.pem ]; then
    echo "ERROR: key.pem file not found"
    exit -1
fi


if test -z "$DOMAIN"
then
	echo "ERROR: DOMAIN variable must be defined, exiting"
	exit -1
fi

if test -z "$PORT"
then
	echo "ERROR: PORT variable must be defined, exiting"
	exit -1
fi

if test -z "$DATABASE_URL"
then
	echo "ERROR: DATABASE_URL variable must be defined, exiting"
	exit -1
fi

if test -z "$CLIENT_SECRET"
then
	echo "ERROR: CLIENT_SECRET variable must be defined, exiting"
	exit -1
fi

if test -z "$AZURE_OPENAI_API_KEY"
then
	echo "ERROR: AZURE_OPENAI_API_KEY variable must be defined, exiting"
	exit -1
fi

if test -z "$AZURE_API_VERSION"
then
	echo "ERROR: AZURE_API_VERSION variable must be defined, exiting"
	exit -1
fi

if test -z "$AZURE_API_ENDPOINT"
then
	echo "ERROR: AZURE_API_ENDPOINT variable must be defined, exiting"
	exit -1
fi

if test -z "$AZURE_MODEL"
then
	echo "ERROR: AZURE_MODEL variable must be defined, exiting"
	exit -1
fi

if test -z "$DEVELOPER_TOKEN"
then
	echo "ERROR: DEVELOPER_TOKEN variable must be defined, exiting"
	exit -1
fi

if test -z "$AZURE_OPENAI_API_KEY_SWEEDEN"
then
	echo "ERROR: AZURE_OPENAI_API_KEY_SWEEDEN variable must be defined, exiting"
	exit -1
fi

if test -z "$AZURE_OPENAI_API_KEY_CANADA"
then
	echo "ERROR: AZURE_OPENAI_API_KEY_CANADA variable must be defined, exiting"
	exit -1
fi

if test -z "$OPENAI_API_KEY"
then
	echo "ERROR: OPENAI_API_KEY variable must be defined, exiting"
	exit -1
fi

echo "INFO: stopping already running docker container"
ssh -o StrictHostKeyChecking=no -i key.pem azureuser@"$DOMAIN" "docker stop rba-backend || echo 'No containers available to stop'"
ssh -o StrictHostKeyChecking=no -i key.pem azureuser@"$DOMAIN" "docker container prune -f || echo 'No stopped containers to delete'"

echo "INFO: pulling docker image"
ssh -o StrictHostKeyChecking=no -i key.pem azureuser@"$DOMAIN" "echo $GITHUB_PASSWORD | docker login -u '$GITHUB_USERNAME' --password-stdin '$REGISTRY'"
ssh -o StrictHostKeyChecking=no -i key.pem azureuser@"$DOMAIN" "docker pull ghcr.io/$GITHUB_REPOSITORY:'$TAG'"
sleep 10

echo "Deleting old image"
ssh -o StrictHostKeyChecking=no -i key.pem azureuser@"$DOMAIN" "docker system prune -f || echo 'No images to delete'"

echo "INFO: starting docker container"
ssh -o StrictHostKeyChecking=no -i key.pem azureuser@"$DOMAIN" "docker run --name rba-backend -p $PORT:$PORT -e PORT='$PORT' -e DATABASE_URL='$DATABASE_URL' -e CLIENT_SECRET='$CLIENT_SECRET' -e DEVELOPER_TOKEN='$DEVELOPER_TOKEN' -e AZURE_OPENAI_API_KEY='$AZURE_OPENAI_API_KEY' -e AZURE_API_VERSION='$AZURE_API_VERSION' -e AZURE_API_ENDPOINT='$AZURE_API_ENDPOINT' -e AZURE_MODEL='$AZURE_MODEL' -e AZURE_OPENAI_API_KEY_SWEEDEN='$AZURE_OPENAI_API_KEY_SWEEDEN' -e AZURE_OPENAI_API_KEY_CANADA='$AZURE_OPENAI_API_KEY_CANADA' -e OPENAI_API_KEY='$OPENAI_API_KEY' -d ghcr.io/$GITHUB_REPOSITORY:$TAG"
