# Montage

## Quick start using Docker Compose

- Create a new API key and a new OAuth 2.0 client ID in the Credentials section of the Google Cloud APIs & Services. Make sure the client ID is restricted to `http://localhost:8080`.
- Enable APIs for YouTube, Google+, Maps.
- Create a settings file `appengine/src/greenday_core/settings/local.py` based on `appengine/src/greenday_core/settings/local.py.sample` and fill the API keys as per above.
- `docker-compose build`
- `docker-compose up`
- Navigate to [http://localhost:8080](http://localhost:8080) for the app
- Navigate to [http://localhost:8000](http://localhost:8000) for the admin UI
- `docker-compose exec montage bash` to get inside the running container
- `. ./GREENDAY/bin/activate` inside the running container to activate the Python environment
- `python bin/manage.py shell` inside the running container to enter the Python shell
- Editing the Python code from your code editor will automatically reflect in the app backend
- Editing the JavaScript code from your code editor and refreshing the browser page will reflect on the frontend

## Running tests

### BE tests

Tests can be run using the run tests shell script

    ./run_tests.sh

### FE tests

Tests are automatically run when you save/add/delete a javascript source/test file. But if you want to run the FE tests in a single run, then:

    grunt karma:unitSingle

## Deployment

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

### To staging

Staging should mirror the master branch

1.  OPTIONAL: Build the docs (`cd docs && make html`)
2.  OPTIONAL: Update ERM diagram (see separate section)
3.  Increment version in app.yaml, long-poller.yaml, worker.yaml, publisher.yaml and commit
4.  Tag the commit with the version number
5.  Merge develop into master and push
6.  If there are migrations run `grunt migrateDev`
7.  Run `grunt deploy`
8.  Change the default version on all modules
9.  OPTIONAL: run data tasks at /admin/denormalisers/, /admin/search/ and /admin/yt_videos/. Run these on https://worker-dot-greenday-project-v02-dev.appspot.com

### To production

Prod should mirror the stable branch

1.  OPTIONAL: Build the docs (`cd docs && make html`)
2.  OPTIONAL: Update ERM diagram (see separate section)
3.  If the version needs changing then complete steps 2-4 of the staging process.
4.  Merge master into stable and push
5.  Run `npm run grunt-deploy-prod` (be aware if running this in a remote server or Docker container, because you need an X server - the deployment task opens the browser for authentication on Google)
6.  If there are migrations to run then run `grunt migrate`
7.  Change the default version on all modules
8.  On Google Cloud side, migrate all traffic to the deployed version: https://console.cloud.google.com/appengine/versions?project=greenday-project&serviceId=default&versionssize=50
9.  OPTIONAL: run data tasks at /admin/denormalisers/, /admin/search/ and /admin/yt_videos/. Run these on https://worker-dot-greenday-project.appspot.com

## Documentation

### Built docs

Built documentation is in `docs/\_build/html`, he path `appengine/built_docs` symlinks to here.

To access the docs when deployed navigate to [http://localhost:8080/docs/](http://localhost:8080/docs/)

### Building docs

To build the docs run sphinx:

    cd docs && make html

### Altering docs

The sphinx config is all in the `/docs` dir.

`conf.py` configures the build environment and sets various settings for the builder

The `\*.rst` files define the documentation pages. Generally we use one page per package. New packages should have a new rst file created for them.

Within the rst files each module is defined. We use automodule to discover all members within given modules. When new modules are created they should be manually added to the package's rst file.

Why can't we autogenerate the rst files...? They were originally autogenerated using `sphinx-apidoc` but have been adjusted manually as the autogenerated ones add in a lot of things that obscure our docs such as members of the endpoints API service classes.
