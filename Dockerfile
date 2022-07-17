# FROM python:3.7-slim
FROM ubuntu

# set TZ so that build continues
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

### Deps + Utils
# build and graphics
RUN apt-get update && apt-get install -y gcc git make build-essential libgl-dev

# python + oldfartpython ppa
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    rm -rf /var/lib/apt/lists/*
RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y python3.7 python3-pip python3.7-dev 

WORKDIR inspectorcell
COPY . .
# CMD /bin/bash

# InspectorCell + Orange3
RUN python3.7 -m pip install --upgrade pip && \
    python3.7 -m pip install -r requirements.txt && \
    python3.7 -m pip install . --force-reinstall --no-deps

CMD python3.7 -m Orange.canvas
# CMD /bin/bash
