# FROM python:3.7-slim
FROM ubuntu

# Deps + Utils
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y gcc git make build-essential
RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y python3.7 python3-pip python3.7-dev 

WORKDIR inspectorcell
COPY . .
# CMD /bin/bash

# InspectorCell + Orange3
RUN python3.7 -m pip install --upgrade pip && \
    python3.7 -m pip install -r requirements.txt && \
    python3.7 -m pip install . --force-reinstall --no-deps

CMD python -m Orange.canvas
