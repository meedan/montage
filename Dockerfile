FROM ubuntu

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  python-pip \
  python-dev \
  build-essential \
  libpng-dev \
  libjpeg-dev \
  libmysqlclient-dev \
  mysql-client \
  graphviz \
  git \
  libncurses5-dev \
  pkg-config \
  libgraphviz-dev \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

COPY . /app/
RUN pip install virtualenv \
  && virtualenv GREENDAY \
  && . ./GREENDAY/bin/activate \
  && pip install -r requirements.txt \
  && pip install zc.recipe.egg==2.0.3 \
  && buildout

ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin:/app/bin

EXPOSE 8000 8080 8081 8082 8083 8084

COPY ./docker-entrypoint.sh /app
CMD ["/app/docker-entrypoint.sh"]
