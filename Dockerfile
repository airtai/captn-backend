ARG BASE_IMAGE=ubuntu:22.04

FROM $BASE_IMAGE


SHELL ["/bin/bash", "-c"]


# needed to suppress tons of debconf messages
ENV DEBIAN_FRONTEND noninteractive

RUN apt update --fix-missing && apt upgrade --yes \
    && apt install -y software-properties-common apt-utils build-essential git wget curl \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt update \
    && apt install -y --no-install-recommends python3.10-dev python3.10-distutils python3-pip python3-apt \
    && apt purge --auto-remove \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Install node and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y --no-install-recommends nodejs \
    && apt purge --auto-remove && apt clean && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --set python3 /usr/bin/python3.10
RUN python3 -m pip install --upgrade pip

COPY migrations ./migrations
COPY application.py scripts/* fastapi_requirements.txt schema.prisma ./
RUN pip install -r fastapi_requirements.txt
RUN pip install airt_service-*-py3-none-any.whl

EXPOSE ${PORT}

ENTRYPOINT []
CMD [ "/usr/bin/bash", "-c", "./start_webservice.sh" ]
