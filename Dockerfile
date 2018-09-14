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
    && apt-key add /tmp/apt-key.gpg

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      google-cloud-sdk \
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

# TODO Copy the minimal set of files needed to avoid rebuilding each time any file changes.
#COPY requirements.txt buildout.cfg gaetools.cfg appengine/ /app/
COPY . /app/
RUN pip install virtualenv \
    && virtualenv GREENDAY \
    && . ./GREENDAY/bin/activate \
    && pip install -r requirements.txt \
    && pip install zc.recipe.egg==2.0.3 \
    && buildout

ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 8.11.4
RUN mkdir /usr/local/nvm \
    && wget -qO- https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

# TODO Copy the minimal set of files needed to avoid rebuilding each time any file changes.
#COPY package.json package-lock.json bower.json .bowerrc .jshintrc .scss-lint.yml Gruntfile.js grunt/ /app/
ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH
RUN npm -g install grunt-cli karma-cli bower jshint \
    && npm install \
    && bower --allow-root install \
    && grunt build

ENV PATH /app/bin:$PATH

EXPOSE 8000 8080 8081 8082 8083 8084

COPY ./docker-entrypoint.sh /app
RUN cat .bashrc | tee -a /root/.bashrc
CMD ["/app/docker-entrypoint.sh"]
