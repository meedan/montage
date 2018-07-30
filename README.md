# Montage

## Development notes and must have things

-   [EditorConfig](http://editorconfig.org) plugin for your editor. Find one [here](http://editorconfig.org/#download).
-   [JSHint](http://www.jshint.com/) will be run on all javascript files upon save. Please check your terminal for errors.
-   It's highly recommended to have a proper linter for Javascript, Sass and Python files to get warned about the errors while you write code. If you are using Sublime Text, there's this awesome plugin: [Sublime Linter for ST2](https://github.com/SublimeLinter/SublimeLinter-for-ST2) - [Sublime Linter for ST3](https://github.com/SublimeLinter/SublimeLinter3). **LINTERS ARE NOT INCLUDED WITH SUBLIMELINTER 3. [Please read the installation documentation](http://sublimelinter.readthedocs.org/en/latest/installation.html)!**
-   Grunt tasks lives in `grunt/tasks` folder in `yaml` format.
-   We use [glue](http://glue.readthedocs.org/en/latest/) for creating sprites.
-   [Autoprefixer](https://github.com/nDmitry/grunt-autoprefixer) will be running along with [Sass](http://sass-lang.com/) task, so you don't need to add vendor prefixes to scss files.
-   [ngAnnotate](https://github.com/olov/ng-annotate) is used to make Angular's dependency injection easy and to keep our code clean. [A Grunt task](https://www.npmjs.org/package/grunt-ng-annotate) is run at the build step to automatically inject the dependencies. ngAnnotate is quite clever, HOWEVER, you still need to annotate your code with `/** @ngInject */` for consistency. Please see [here](https://github.com/johnpapa/angularjs-styleguide#minification-and-annotation) for more information.
-   We use [uglify](https://github.com/gruntjs/grunt-contrib-uglify) Grunt task in build process to concatenate and mangle our js code.
-   We use [Angular-Material](https://material.angularjs.org) for FE things. Why, you say? Because it's awesome!

## Development Environment

### Prerequisites

*   Python >= 2.7
*   MySQL 5.5
*   Sass
*   pip
*   Virtualenv
*   Node.js, npm
*   Bower
*   Buildout
*   Grunt

#### Installation on Mac OSx

*   Install [Homebrew](https://brew.sh/).

    ```bash
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew doctor
    ```

*   Install Xcode.

    Use App Store.

*   Install [Git](https://git-scm.com/).

    ```bash
    brew install git
    ```

*   Install [Python](https://www.python.org/).

    ```bash
    brew install python
    ```

*   Install [MySQL](https://www.mysql.com/).

    ```bash
    brew install mysql
    ```

*   Pillow 3.3.2 dependencies

    ```bash
    brew tap homebrew/dupes
    brew install zlib
    brew link zlib --force
    ```

    Start MySQL.

    ```
    mysql.server start
    ```

*   Create database.

    ```bash
    ./syncdb.sh
    ```

*   Install [Sass](http://sass-lang.com/).

    ```bash
    gem install sass
    ```

*   Install [pip](https://pypi.python.org/pypi/pip).

    ```bash
    curl https://bootstrap.pypa.io/ez_setup.py -o - | sudo python
    sudo easy_install pip
    ```

    > If you can't run easy_install, download [extern](https://pypi.python.org/pypi/extern/0.1.0) from  [here](https://pypi.python.org/packages/3d/33/c0a11b3ccf79e784a813bb52804c96d8ddb718f6f20379915e49279d9ef7/extern-0.1.0.tar.gz) and run:
    >
    > ```bash
    > tar zxf extern-0.1.0.tar.gz
    > cd extern-0.1.0
    > sudo python setup.py install
    > ```

*   Install [Virtualenv](https://virtualenv.pypa.io/).

    ```bash
    sudo pip install virtualenv
    ```

*   Setup Virtualenv.

    ```bash
    virtualenv GREENDAY # to create it
    source ./GREENDAY/bin/activate
    ```

*   Install requirements.

    ```bash
    pip install -r requirements.txt
    ```

*   Install [Node.js](https://nodejs.org/) and [npm](https://www.npmjs.com/).

    ```bash
    brew install node
    ```

*   Install [Bower](https://bower.io/).

    ```bash
    sudo npm install -g bower
    ```

*   Run `buildout`.

    ```bash
    buildout
    ```

*   Install [Grunt](https://gruntjs.com/).

    ```bash
    sudo npm install -g grunt
    ```

*   Copy the configuration file and update the settings (SECRET_KEY, OAUTH_SETTINGS, YOUTUBE_API_DEVELOPER_KEY…)

    ```bash
    cp ./appengine/src/greenday_core/settings/local.py.sample ./appengine/src/greenday_core/settings/local.py
    ```

#### Installation on Ubuntu

*   Install Git.

    ```
    sudo apt-get install git
    ```

*   Clone the project.

    ```
    git clone git@github.com:storyful/montage.git
    ```

*   Install MySQL.

    ```
    sudo apt-get install libmysqlclient-dev
    sudo apt-get install mysql-server-5.5
    ```
    ```
    sudo service mysql start
    ```

*   Create database.

    ```
    ./syncdb.sh
    ```

*   Install [Sass](http://sass-lang.com/).

    ```
    gem install sass
    ```

*   Install pip.

    ```
    sudo apt-get install python-pip python-dev build-essential
    ```

*   Install Virtualenv and Virtualenvwrapper.

    ```
    sudo pip install virtualenv virtualenvwrapper
    source /usr/local/bin/virtualenvwrapper.sh
    source ~/.bashrc
    ```

*   Pillow 3.3.2 dependencies
    ```
    sudo apt-get install zlib1g-dev
    ```

*   Install requirements.

    ```
    mkvirtualenv GREENDAY
    workon GREENDAY
    pip install -r requirements.txt
    ```

*   Install Buildout.

    ```
    sudo pip install zc.buildout
    buildout
    ```

*   Install Node.js and npm.

    ```
    sudo apt-get install curl
    curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
    sudo apt-get install -y nodejs
    ```

*   Install Grunt.

    ```
    sudo npm install -g grunt
    ```

*   Install Bower.

    ```
    sudo npm install bower -g
    ```

*   Copy the configuration file and update the settings (SECRET_KEY, OAUTH_SETTINGS, YOUTUBE_API_DEVELOPER_KEY…)

    ```
    cp ./appengine/src/greenday_core/settings/local.py.sample ./appengine/src/greenday_core/settings/local.py
    ```

### Running locally

To run both `grunt` and the `dev_appserver` in one go:

    grunt server

**NOTE:** `pdb` won't work with the above. If you need `pdb` you need to run grunt and dev_appserver separately like this:

    grunt

and then on a separate terminal window:

    ./serve.sh

If you find that your machine can't handle the number of threads that the 4 modules runs then you can run `./bin/dev_appserver appengine`. This will run the app and API but some of the background processes such as denormalising and search indexing will fail.

The application runs on [localhost:8080](http://localhost:8080/).

### Running tests

#### BE tests

Tests can be run using the run tests shell script

    ./run_tests.sh

#### FE tests

Tests are automatically run when you save/add/delete a javascript source/test file. But if you want to run the FE tests in a single run, then:

    grunt karma:unitSingle

### Building and running docs

Documentation can be built and run using the run docs shell script.

    ./run_docs.sh

To rebuild your buildout environment you can run

    ./rebuild_env.sh

### Setting up DB access to staging and prod databases

All connections to the Cloud SQL instances are made over SSL. You will need to set yourself up with a private key to access this.

1.  Go to the [project console](https://console.developers.google.com/project/greenday-project-v02-dev/sql/instances/greenday/access-control)
2.  Under "SSL Certificates" click "Add new"
3.  Enter a name you can be identified by as the cert name (your LDAP would be appropriate)
4.  Download client-key.pem, client-cert.pem and ca-cert.pem (this is named server-ca when you download it from the console. You will need to rename it to ca-cert.pm when you store it locally) and save them in {project root}/keys/staging/ *DO NOT STAGE THESE FILES - THEY ARE GIT IGNORED FOR A REASON*
6.  Click "Restart and Close". This RESTARTS the SQL instance but is necessary for the certificate to be usable.
7.  Repeat for the [prod project](https://console.developers.google.com/project/greenday-project/sql/instances/greenday/access-control) and save keys to {project root}/keys/prod/
8.  Test connection using ./bin/manage.py dbshell --settings=greenday_core.settings.(staging|prod)
9.  If you use any other type of UI to connect to Cloud SQL (Sequel Pro) you will have to add these key files to the connection details for each connection.

### Deployment

#### To staging

Staging should mirror the master branch

1.  Build the docs (./run_docs.sh)
2.  OPTIONAL: update ERM diagram (see separate section)
3.  Increment version in app.yaml, long-poller.yaml, worker.yaml, publisher.yaml and commit
4.  Tag the commit with the version number
5.  Merge develop into master and push
6.  If there are migrations run `grunt migrateDev`
7.  Run `grunt deploy`
8.  Change the default version on all modules
9.  Spudgun it
10. OPTIONAL: run data tasks at /admin/denormalisers/, /admin/search/ and /admin/yt_videos/. Run these on https://worker-dot-greenday-project-v02-dev.appspot.com

#### To production

Prod should mirror the stable branch

1.  Build the docs (`cd docs && make html`)
2.  OPTIONAL: update ERM diagram (see separate section)
3.  If the version needs changing then complete steps 2-4 of the staging process.
4.  Merge master into stable and push
5.  Run `grunt deployProd`
6.  If there are migrations to run then run `grunt migrate`
7.  Change the default version on all modules
8.  Spudgun it
9.  OPTIONAL: run data tasks at /admin/denormalisers/, /admin/search/ and /admin/yt_videos/. Run these on https://worker-dot-greenday-project.appspot.com

### Generating ERD diagram

Ensure you have Graphviz installed on your system: `brew install graphviz`. Then install pygraphviz (`pip install pygraphviz`).

Run `./bin/manage.py graph_models greenday_core -o greenday-erd.png`

***

## Sphinx documentation

### Built docs

Built documentation is in docs/\_build/html, appengine/built_docs symlinks to here.

To access the docs when deployed go to /docs/index.html

### Building docs

To build the docs run sphinx:

    ./run_docs.sh

### Altering docs

The sphinx config is all in the /docs dir.

conf.py configures the build environment and sets various settings for the builder

The \*.rst files define the documentation pages. Generally we use one page per package. New packages should have a new rst file created for them.

Within the rst files each module is defined. We use automodule to discover all members within given modules. When new modules are created they should be manually added to the package's rst file.

Why can't we autogenerate the rst files...? They were originally autogenerated using sphinx-apidoc but have been adjusted manually as the autogenerated ones add in a lot of things that obscure our docs such as members of the endpoints API service classes.

If you are missing any packages try `pip install -r requirements.txt`. TODO: get rid of dependencies in here and only use buildout
