# install Python packages in virtual environment
# python3.11 -m venv .venv-3.11
# source .venv-3.11/bin/activate
# python -m pip install --upgrade pip

# needed to make sure default python is 3.9 instead of 3.11
# sudo ln -s -f /usr/local/bin/python3.9 /usr/bin/python3

# update pip
pip install --upgrade pip

# install dev packages
pip install -e .[dev]

# install pre-commit hook if not installed already
pre-commit install

# install prisma
prisma generate

echo '{
    "web": {
        "client_id": "571449075812-2ehtrjb3k2vsqh6fl10mu3d3oruau1t2.apps.googleusercontent.com",
        "project_id": "captn-chat-prod",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "'${GOOGLE_ADS_CLIENT_SECRET}'",
        "redirect_uris": [
            "http://localhost:9000/login/callback"
        ]

    }
}' > client_secret.json
