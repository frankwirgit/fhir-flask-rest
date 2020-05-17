# fhir_flask_rest

It's a programming exercise for storing data through rest api in a relational database

## Application objectives

- Implement a REST API that stores data in a DB.
- Implement a Docker Compose configuration, docker-compose.yml, which brings up the REST API system.
- Create an end to end test with a README containing startup and testing instructions.
  
## Development tools

This exercise demonstrates how to create a simple REST service using Python Flask and SQLite.
The resource model is persistenced using SQLAlchemy to keep the application simple. SQLAlchemy is an Object Relational Mapper (ORM) that will allow developers to work with classes instead of database records.

## Implemention list

The REST API include the basic service methods - POST, PUT, GET and DELETE to show the corresponding API and return codes that should be used for. 

A relational database (POSTGRES) is chosen to store the data. Data model with associated data schemas is designed based on the sample data given. 

Note that the service api and data model are written and tested as two separated components on application layer.

Docker compose is configured to support putting REST API (port 5001:5000) and POSTGRES database services (port 5433:5432) in their corresponding containers with the ports forwarding to the host.

Separate test programs are designed and written to validate service api and data model respectively.

README is written with instructions on how to start up and test the application as well as how to conduct the test cases. 

## Development environment

The VScode (version 1.44) with Python 3 intepreter is downloaded and setup for development api. The Docker community edition (version 18.06.1) is used for building the docker image and hosting the REST API and database services. 

This exercise contains a `.devcontainer` folder that will set up a Docker environment in VSCode for testing and debugging directly.  

Add VSCode to the system path on host so that it can be invoked from the command line. To do this, open VSCode and type `Shift+Command+P` on Mac or `Shift+Ctrl+P` on Windows to open the command palete and then search for "shell" and select the option **Shell Command: Install 'code' command in Path**. This will install VSCode in the current path.

Then start development environment setup with:

```bash
    git clone https://github.com/.../fhir_flask_rest.git
    cd fhir_flask_rest
    code .
```

The first time it will build the Docker image and after that it will just create a container and place you inside of it in your `/workspace` folder which actually contains the repo shared from your computer. It will also install all of the VSCode extensions needed for Python development.

In case it does not automatically open the application in a container, you can select the green icon at the bottom left of your VSCode UI and select: **Remote Containers: Reopen in Container**.

Extra Python packages and tool used for testing (nose) are included in the  `/requirements.txt` file under the root which is used for pip install by Dockerfile.  

Docker is needed in order to run a container for the POSTGRES database. 

## Model

The underlying data model is constructed based on the given data sample (`tests/fhir-patient-post.json`) with the FHIR HL7 format to support the FHIR uuid/id in API responses. There are 3 relational tables established, including a based table (`pprofile`) and its two extended one-to-many relationship sub-tables (`pname` and `paddress`), where `pprofile` is the table to store distinct patient records (uuid/id), `pname` to store patient's names and `paddress` to store patient's addresses. The `pname` and `paddress` tables use foreign key `pprofile_id` to link to the base table `pprofile`. The table schema details are described in the program of model.py. 

## Rest API

The service APIs includes basic methods - GET, POST, UPDATE and DELETE. The GET is branched to different functionalities, such as listing all patients based on different request arguments (different search keys) to retreive an individual or specific group of patients. POST is for creating new patients record as well as appending new name or address for an existing patient. UPDATE is used for changing the existing records. Based on different request routes, the UPDATE can be done directly by passing the related ids (profile, name or address) or in-directly by passing the patients ID only, which by default the "latest" name or address will be updated. The DELETE method is used for delete patient's single name or address, or the distinct record with names and addresses associated with. The service detail are included in the program of service.py.

## Tests

Run the tests using `nosetests`

```bash
  $ nosetests --with-spec --spec-color
```

**Notes:** the parameter flags `--with-spec --spec-color` add color so that red-green-refactor is meaningful. If you are in a command shell that supports colors, passing tests will be green while failing tests will be red. The flag `--with-coverage` is automatcially specified in the `setup.cfg` file so that code coverage is included in the tests.

The Code Coverage tool runs with `nosetests` so to see how well your test cases exercise your code just run the report:

```bash
  $ coverage report -m
```

This is particularly useful because it reports the line numbers for the code that is not covered so that you can write more test cases.

To run the service use `flask run` (Press Ctrl+C to exit):

```bash
  $ FLASK_APP=service:app flask run -h 0.0.0.0
```

You must pass the parameters `-h 0.0.0.0` to have it listed on all network adapters to that the post can be forwarded by `vagrant` to your host computer so that you can open the web page in a local browser at: http://localhost:5001

Tests can also be conducted manually to check up intermediate results, such as checking the table records in database and check the request and response contents on web browser. To do that:
POSTGRES database can be connected inside the database service container by using 
 `psql -d <postgres dbname> -U <postgres dbuser> -W`  Then use those basic database commands and SQL query to help with the tests

Postman can be used to help with the tests by manually cut/paste json formatted sample data to validate REST API operations. 
