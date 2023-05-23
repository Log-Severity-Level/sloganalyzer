FROM ubuntu:20.04

COPY . /app
#COPY ./domain /domain

WORKDIR /app

RUN apt update
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install -y python3.9
RUN apt-get install -y python3-pip
RUN apt install -y ./external/srcml_1.0.0-1_ubuntu20.04.deb
RUN apt install -y git postgresql postgresql-contrib graphviz

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install setuptools==57.4.0

RUN python3 -m pip install --no-cache-dir -r requirements.txt
# RUN psql -U postgres log

RUN cp config/.env_docker config/.env

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "config.wsgi:application"]
