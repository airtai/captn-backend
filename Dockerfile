ARG BASE_IMAGE=ubuntu:22.04

FROM $BASE_IMAGE

SHELL ["/bin/bash", "-c"]

# needed to suppress tons of debconf messages
ENV DEBIAN_FRONTEND noninteractive

RUN apt update --fix-missing && apt upgrade --yes \
    && apt install -y software-properties-common apt-utils build-essential git wget curl \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt update \
    && apt install -y --no-install-recommends python3.11-dev python3.11-distutils python3-pip python3-apt \
    && apt purge --auto-remove \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Install node and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y --no-install-recommends nodejs \
    && apt purge --auto-remove && apt clean && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN python3 -m pip install --upgrade pip

COPY migrations ./migrations
COPY google_ads ./google_ads
COPY openai_agent ./openai_agent
COPY captn ./captn
COPY etc ./etc
COPY templates ./templates
COPY application.py ws_application.py scripts/* schema.prisma pyproject.toml uvicorn-log-config.json ./
RUN pip install -e ".[dev]"

EXPOSE ${PORT}

ENTRYPOINT []
CMD [ "/usr/bin/bash", "-c", "./start_webservice.sh" ]
