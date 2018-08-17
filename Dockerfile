FROM ubuntu

# Install Google Cloud SDK (gcloud)
RUN set -ex \
  && apt-get update \
  && apt-get install -y --no-install-recommends wget lsb-release gnupg2 \
  && export CLOUD_SDK_REPO=cloud-sdk-$(lsb_release -c -s) \
  && echo Using Google Cloud SDK $CLOUD_SDK_REPO \
  && echo deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main \
     | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
  && wget https://packages.cloud.google.com/apt/doc/apt-key.gpg -O /tmp/apt-key.gpg --no-check-certificate \
  && apt-key add /tmp/apt-key.gpg \
  && apt-get update \
  && apt-get install -y --no-install-recommends google-cloud-sdk

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

RUN export PATH="$PATH":/app/bin \
  && npm install \
  && bower --allow-root install \
  && npm rebuild node-sass \
  && grunt build

ENV PATH $PATH:/app/bin

EXPOSE 8000 8080 8081 8082 8083 8084

COPY ./docker-entrypoint.sh /app
CMD ["/app/docker-entrypoint.sh"]
