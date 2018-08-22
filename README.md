# Montage

## Quick start using Docker Compose

- Create a new API key and a new OAuth 2.0 client ID in the Credentials section of the Google Cloud APIs & Services. Make sure the client ID is restricted to `http://localhost:8080`.
- Enable APIs for YouTube, Google+, Maps.
- Create a settings file `appengine/src/greenday_core/settings/local.py` based on `appengine/src/greenday_core/settings/local.py.sample` and fill the API keys as per above.
- `docker-compose build`
- `docker-compose up`
- Navigate to [http://localhost:8080](http://localhost:8080) for the app
- Navigate to [http://localhost:8000](http://localhost:8000) for the admin UI

## Development using Docker Compose

`docker-compose exec montage bash` to get inside the running container

### Backend

- `. ./GREENDAY/bin/activate`
- `python bin/manage.py shell` and other Python / Django commands are available
- Editing the Python code from your code editor will automatically reflect in the running service
- `./run_tests.sh` to run backend tests

### Frontend

- `grunt watch` to watch code changes in JavaScript / HTML and rebuild the package
- `grunt karma:unitSingle` to run all unit tests

## Deployment

### Setting up DB access to QA and live databases

All connections to the Cloud SQL instances are made over SSL. You will need to set yourself up with a private key to access this.

1.  Go to the [project console](https://console.cloud.google.com/sql/instances?project=greenday-project) and choose a database
2.  Under "SSL" click "Create a client certificate"
3.  Enter a name you can be identified by as the cert name
4.  Download client-key.pem, client-cert.pem and ca-cert.pem (this is named server-ca when you download it from the console. You will need to rename it to ca-cert.pm when you store it locally) and save them in {project root}/keys/(qa|live)/
5.  Click "Restart and Close". This RESTARTS the SQL instance but is necessary for the certificate to be usable.
6.  Test connection using ./bin/manage.py dbshell --settings=greenday_core.settings.(qa|live)

### To QA

QA should mirror the `develop` branch. QA has a fixed version, called "qa".

1.  Copy `appengine/auth.json.example` to `appengine/auth.json`
2.  Run `npm run full-deploy-qa`

PS: At Meedan, a deployment to QA happens automatically when a push happens to `develop`. You can also call it from Jenkins (job `montage-develop`) or from Slack using Hubot: `@hu deploy-montage-qa`.

### To Live

Live should mirror the `master` branch.

1.  If the version needs changing then update file `VERSION`
2.  Merge develop into master and push
3.  Copy `appengine/auth.json.example` to `appengine/auth.json`
4.  Run `npm run full-deploy-live`

PS: At Meedan, you can deploy from Jenkins (job `montage-master`) or from Slack using Hubot: `@hu deploy-montage-live`.

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
