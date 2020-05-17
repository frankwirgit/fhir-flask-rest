# REST API Service Class

"""
Patient Membership Data Set

Paths:
------
GET /pats - Returns a list all of the patients
GET /pats/{id} - Returns the patient with a given id number
POST /pats - creates a new patient record in the database
PUT /pats/{id} - updates a patient record in the database
DELETE /pats/{id} - deletes a patient record in the database
"""

#import os
#import sys
#import logging
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes

# For this example we'll use SQLAlchemy, a popular ORM that supports a
# variety of backends including SQLite, MySQL, and PostgreSQL
#from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import NotFound
from service.models import Pprofile, Pname, Paddress, DataValidationError, Gender


# Import Flask application
from . import app

######################################################################
# Error Handlers
######################################################################
@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)


@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST, error="Bad Request", message=message
        ),
        status.HTTP_400_BAD_REQUEST,
    )

@app.errorhandler(status.HTTP_401_UNAUTHORIZED)
def access_unauthorized(error):
    """ Handles bad reuests with 401_UNAUTHORIZED """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_401_UNAUTHORIZED, error="Access Unauthorized", message=message
        ),
        status.HTTP_401_UNAUTHORIZED,
    )

@app.errorhandler(status.HTTP_403_FORBIDDEN)
def access_forbidden(error):
    """ Handles bad reuests with 403_FORBIDDEN """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_403_FORBIDDEN, error="Access Forbidden", message=message
        ),
        status.HTTP_403_FORBIDDEN,
    )

@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(status=status.HTTP_404_NOT_FOUND, error="Not Found", message=message),
        status.HTTP_404_NOT_FOUND,
    )


@app.errorhandler(status.HTTP_405_METHOD_NOT_ALLOWED)
def method_not_supported(error):
    """ Handles unsuppoted HTTP methods with 405_METHOD_NOT_SUPPORTED """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
            error="Method not Allowed",
            message=message,
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )

@app.errorhandler(status.HTTP_409_CONFLICT)
def resource_state_conflict(error):
    """ Handles bad reuests with 409_CONFLICT """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_409_CONFLICT, error="Resource State Conflict", message=message
        ),
        status.HTTP_409_CONFLICT,
    )

@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error="Unsupported media type",
            message=message,
        ),
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    )


@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    """ Handles unexpected server error with 500_SERVER_ERROR """
    message = str(error)
    app.logger.error(message)
    return (
        jsonify(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=message,
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    return (
        jsonify(
            name="Patient FHIR REST API Service",
            version="1.0",
            paths=url_for("list_pats", _external=True),
        ),
        status.HTTP_200_OK,
    )

#---------------------------------------------------------------------
# PROFILE METHODS
#---------------------------------------------------------------------

######################################################################
# LIST ALL PATIENTS
######################################################################
@app.route("/pats", methods=["GET"])
def list_pats():
    """ Returns all of the Pats """
    app.logger.info("Request for patient list")

    #create profile, name and address list
    pats = []

    phone_home = request.args.get("phone_home")
    email = request.args.get("email")
    active_str = request.args.get("active")
    gender = request.args.get("gender")

    family = request.args.get("family")
    given_1 = request.args.get("given")
    postalCode = request.args.get("postalCode")


    if phone_home:
        pats = Pprofile.find_by_phone(phone_home)
    elif email:
        pats = Pprofile.find_by_email(email)
    elif active_str:
        pats = Pprofile.find_by_acive(bool(active_str))
    elif gender:
        pats = Pprofile.find_by_gender(getattr(Gender, gender))
    elif postalCode:
        pats = Pprofile.find_by_zip(postalCode)
    elif family and (not given_1):
        pats = Pprofile.find_by_lname(family)
    elif given_1 and (not family):
        pats = Pprofile.find_by_fname(given_1)
    elif given_1 and family:
        pats = Pprofile.find_by_name(given_1, family)
    else:
        pats = Pprofile.all()

    #serialize the convert to json
    results = [pat.serialize() for pat in pats]
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE A PATIENT
######################################################################
@app.route("/pats/<int:pat_id>", methods=["GET"])
def get_pats(pat_id):
    """
    Retrieve a single Pat

    This endpoint will return a Pat based on his id
    """
    app.logger.info("Request for patient with id: %s", pat_id)
    pat = Pprofile.find(pat_id)
    if not pat:
        raise NotFound("Patient with id '{}' was not found.".format(pat_id))
    return make_response(jsonify(pat.serialize()), status.HTTP_200_OK)


######################################################################
# ADD A NEW PATIENT
######################################################################
@app.route("/pats", methods=["POST"])
def create_pats():
    """
    Creates a Pat
    This endpoint will create a Pat based the data in the body that is posted
    """
    app.logger.info("Request to create a patient")
    check_content_type("application/json")
    pat = Pprofile()
    pat.deserialize(request.get_json())
    pat.create()
    message = pat.serialize()
    location_url = url_for("get_pats", pat_id=pat.id, _external=True)
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


######################################################################
# UPDATE AN EXISTING PATIENT
######################################################################
@app.route("/pats/<int:pat_id>", methods=["PUT"])
def update_pats(pat_id):
    """
    Update a Pat

    This endpoint will update a Pat based the body that is posted
    """
    app.logger.info("Request to update patient with id: %s", pat_id)
    check_content_type("application/json")
    pat = Pprofile.find(pat_id)
    if not pat:
        raise NotFound("Patient with id '{}' was not found.".format(pat_id))
    pat.deserialize(request.get_json())
    pat.id = pat_id
    pat.save()
    return make_response(jsonify(pat.serialize()), status.HTTP_200_OK)


######################################################################
# DELETE A PATIENT
######################################################################
@app.route("/pats/<int:pat_id>", methods=["DELETE"])
def delete_pats(pat_id):
    """
    Delete a Pat

    This endpoint will delete a Pat based the id specified in the path
    """
    app.logger.info("Request to delete the patient with id: %s", pat_id)
    pat = Pprofile.find(pat_id)
    if pat:
        pat.delete()
    return make_response("", status.HTTP_204_NO_CONTENT)

#---------------------------------------------------------------------
# ADDRESS METHODS
#---------------------------------------------------------------------

######################################################################
# LIST ADDRESSES
######################################################################
@app.route("/pats/<int:pat_id>/address", methods=["GET"])
def list_address(pat_id):
    """ Returns all of the Addresses for a patient """
    app.logger.info("Request for Patient's Addresses...")
    pat = Pprofile.find_or_404(pat_id)
    results = [addr.serialize() for addr in pat.address]
    return make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# ADD AN ADDRESS TO A PATIENT
######################################################################
@app.route('/pats/<int:pat_id>/address', methods=['POST'])
def create_address(pat_id):
    """
    Create an Address on a patient
    This endpoint will add an address to a patient
    """
    app.logger.info("Request to add an address to a patient")
    check_content_type("application/json")
    pat = Pprofile.find_or_404(pat_id)
    addr = Paddress()
    addr.deserialize(request.get_json())
    pat.address.append(addr)
    pat.save()
    message = addr.serialize()
    return make_response(jsonify(message), status.HTTP_201_CREATED)

######################################################################
# RETRIEVE AN ADDRESS FROM PATIENT
######################################################################
@app.route('/pats/<int:pat_id>/address/<int:address_id>', methods=['GET'])
def get_address(pat_id, address_id):
    """
    Get an Address
    This endpoint returns just an address
    """
    app.logger.info("Request to get an address with id: %s", address_id)
    #look for a patient first
    pat = Pprofile.find_or_404(pat_id)
    #look for the address of the patient found
    addr = Paddress.find_or_404(address_id)
    return make_response(jsonify(addr.serialize()), status.HTTP_200_OK)

######################################################################
# UPDATE AN ADDRESS
######################################################################
@app.route("/pats/<int:pat_id>/address/<int:address_id>", methods=["PUT"])
def update_address(pat_id, address_id):
    """
    Update an Address
    This endpoint will update an Address based the body that is posted
    """
    app.logger.info("Request to update address with id: %s", address_id)
    check_content_type("application/json")
    #look for a patient
    pat = Pprofile.find_or_404(pat_id)
    #look for the address to be updated
    addr = Paddress.find_or_404(address_id)
    addr.deserialize(request.get_json())
    addr.id = address_id
    addr.save()
    return make_response(jsonify(addr.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE AN ADDRESS
######################################################################
@app.route("/pats/<int:pat_id>/address/<int:address_id>", methods=["DELETE"])
def delete_address(pat_id, address_id):
    """
    Delete an Address
    This endpoint will delete an Address based the id specified in the path
    """
    app.logger.info("Request to delete address with id: %s", address_id)
    #look for a patient
    pat = Pprofile.find_or_404(pat_id)
    #look for the address to be updated
    addr = Paddress.find(address_id)
    if addr:
        addr.delete()
    return make_response("", status.HTTP_204_NO_CONTENT)



#---------------------------------------------------------------------
# NAME METHODS
#---------------------------------------------------------------------

######################################################################
# LIST NAMES
######################################################################
@app.route("/pats/<int:pat_id>/name", methods=["GET"])
def list_name(pat_id):
    """ Returns all of the Names for a patient """
    app.logger.info("Request for Patient's Names...")
    pat = Pprofile.find_or_404(pat_id)
    results = [name_item.serialize() for name_item in pat.name]
    return make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# ADD A NAME TO A PATIENT
######################################################################
@app.route('/pats/<int:pat_id>/name', methods=['POST'])
def create_name(pat_id):
    """
    Create a name on a patient
    This endpoint will add a name to a patient
    """
    app.logger.info("Request to add a name to a patient")
    check_content_type("application/json")
    pat = Pprofile.find_or_404(pat_id)
    name_new = Pname()
    name_new.deserialize(request.get_json())
    pat.name.append(name_new)
    pat.save()
    message = name_new.serialize()
    return make_response(jsonify(message), status.HTTP_201_CREATED)

######################################################################
# RETRIEVE A NAME FROM PATIENT
######################################################################
@app.route('/pats/<int:pat_id>/name/<int:name_id>', methods=['GET'])
def get_name(pat_id, name_id):
    """
    Get a name
    This endpoint returns just a name
    """
    app.logger.info("Request to get a name with id: %s", name_id)
    #look for a patient first
    pat = Pprofile.find_or_404(pat_id)
    #look for the name of the patient found
    name = Pname.find_or_404(name_id)
    return make_response(jsonify(name.serialize()), status.HTTP_200_OK)

######################################################################
# UPDATE A NAME
######################################################################
@app.route("/pats/<int:pat_id>/name/<int:name_id>", methods=["PUT"])
def update_name(pat_id, name_id):
    """
    Update a name
    This endpoint will update a name based the body that is posted
    """
    app.logger.info("Request to update name with id: %s", name_id)
    check_content_type("application/json")
    #look for a patient
    pat = Pprofile.find_or_404(pat_id)
    #look for the name to be updated
    name = Pname.find_or_404(name_id)
    name.deserialize(request.get_json())
    name.id = name_id
    name.save()
    return make_response(jsonify(name.serialize()), status.HTTP_200_OK)

######################################################################
# UPDATE THE LATEST NAME OF THE PATIENT 
######################################################################
@app.route("/pats/<int:pat_id>/latest_name", methods=["PUT"])
def update_latest_name(pat_id):
    """
    Update the latest record of name of a patient
    This endpoint will update a name based the body that is posted
    """
    app.logger.info("Request to update latest name of patient with id: %s", pat_id)
    check_content_type("application/json")
    #look for a patient
    pat = Pprofile.find_or_404(pat_id)
    #look for the latest name to be updated
    latest_name = Pname()
    latest_name = pat.name[len(pat.name)-1]
    latest_name.deserialize(request.get_json())
    latest_name.save()
    #db.session.commit()

    return make_response(jsonify(latest_name.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE A NAME
######################################################################
@app.route("/pats/<int:pat_id>/name/<int:name_id>", methods=["DELETE"])
def delete_name(pat_id, name_id):
    """
    Delete a name
    This endpoint will delete a name based the id specified in the path
    """
    app.logger.info("Request to delete name with id: %s", name_id)
    #look for a patient
    pat = Pprofile.find_or_404(pat_id)
    #look for the name to be updated
    name = Pname.find(name_id)
    if name:
        name.delete()
    return make_response("", status.HTTP_204_NO_CONTENT)



######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def init_db():
    """ Initialies the SQLAlchemy app """
    global app
    Pprofile.init_db(app)


def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    #HTTP 415 Unsupported Media Type
    abort(415, "Content-Type must be {}".format(content_type))


'''
    In models.py:

    class Patient(db.Model, PatBase):
            #...
    class Address(db.Model, PatBase):
            #...

    #if the find_by_zip() is defined in the Address() class
    @classmethod
    def find_by_zip(cls, postalCode):
        """ Returns all of the Pats having the zip code
        """
        logger.info("Processing zip code query for %s ...", postalCode)
        
        return cls.query.filter(cls.postalCode == postalCode)
   

    In service.py:

    postalCode = request.args.get("postalCode")

    pats = []
    addr_list = Address.find_by_zip(postalCode)
    for addr in addr_list:
        pat = Patient.find_by_id(addr.pat_id)
        pats.append(pat)
'''