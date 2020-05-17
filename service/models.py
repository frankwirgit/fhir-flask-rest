# FHIR Data Model Class

"""
Models for Patient Membership Data

All of the models are stored in this module

Models
------
Pat - A patient in membership list

Attributes:
-----------
Profile = a top-level model injerated from base model
    resourceType (string) - the resource type, i.e. "Patient"
    active (boolean) - True or False
    gender (enum) - male, female or unknown
    birthDate (DateTime) - the date of birth of a patient, use datetime() to validate

    name [] =  name list
        use - name usage type
        family - last name
        given [] = first name list: given_1 (required), give_2 (optional)
        prefix [] = name prefix list: prefix_1 (optional), prefix_2 (optional)

    telecom [] = contract list
        system - contact type
        value - contact value, i.e. phone number or email
        use - contact type

    phone_home <- telecom[]
    phone_office <- telecom[]
    phone_cell <-telcome[]
    email <- telecom[]


    address [] = address list
        use - location type
        type - mail type
        text - complete address context
        line = street address list: line_1 (required), line_2 (optional)
        city - city
        state - state
        postalCode - zip code
        country - country

"""
import logging
from enum import Enum
import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
#pip install email_validator
from email_validator import validate_email, EmailNotValidError


logger = logging.getLogger("gunicorn.error")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()

# Zip code mapping with regular expression
zipCode = re.compile(r"^[0-9]{5}(?:-[0-9]{4})?$")
phoneNumb = re.compile(r"^[0-9]{10}$")


class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """
    pass

class Gender(Enum):
    """ Enumeration of valid Genders """
    male = 1
    female = 2
    unknown = 3

######################################################################
# BASE MODEL
######################################################################

class PatBase():
    """
    Base class that represents a Patient

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """
    def create(self):
        """
        Creates a new Pat to the database
        """
        logger.info("Creating %s %s %s", self.name[0].given_1, self.name[0].family, self.name[0].pprofile_id)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def save(self):
        """
        Updates an existing Pat to the database
        """
        #logger.info("Saving %s %s", self.name[0].given_1, self.name[0].family)
        db.session.commit()

    def delete(self):
        """ Removes a Pat from the data store """
        logger.info("Deleting %s %s with pid=%s and pprofile_id=%s", self.name[0].given_1, self.name[0].family, self.id, self.name[0].pprofile_id)
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push() #push application context to enable dbase creation
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """ Returns all of the Pats in the database """
        logger.info("Processing all Pats")
        return cls.query.all()

    @classmethod
    def find(cls, pat_id):
        """ Finds a Pat by the ID """
        logger.info("Processing lookup for id %s ...", pat_id)
        return cls.query.get(pat_id)

    @classmethod
    def find_or_404(cls, pat_id):
        """ Find a Pat by the ID and return Not Found status code """
        logger.info("Processing lookup or 404 for id %s ...", pat_id)
        return cls.query.get_or_404(pat_id)

    #@classmethod
    #def find_by_pat_id(cls, pat_id):
        #""" Find all addresses or names by the pprofile ID and return a list """
        #logger.info("Processing lookup or 404 for profile id %s ...", pat_id)
        ##return cls.query.join(Pprofile).filter(Pprofile.id == pat_id).all()
        #return cls.query.filter(cls.pprofile_id == pat_id)


######################################################################
# PROFILE MODEL
######################################################################

class Pprofile(db.Model, PatBase):
    """
    Class that represents patient's profile record

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    resourceType = db.Column(db.String(20), nullable=True)
    active = db.Column(db.Boolean(), nullable=False, default=False)

    name = db.relationship('Pname', backref='pprofile', cascade="all, delete-orphan", lazy=True)
    
    # based on telecom contents
    phone_home = db.Column(db.String(10), nullable=True)
    phone_office = db.Column(db.String(10), nullable=True)
    phone_cell = db.Column(db.String(10), nullable=True)
    email = db.Column(db.String(60), nullable=True)
    
    address = db.relationship('Paddress', backref='pprofile', cascade="all, delete-orphan", lazy=True)

    DOB = db.Column(db.DateTime, nullable=False)
    #DOB = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    gender = db.Column(db.Enum(Gender), nullable=False, server_default=(Gender.unknown.name))

    def __repr__(self):
        return "<Pat fname=%r lname=%r id=[%s] pprofile_id=[%s]>" % (self.name[0].given_1, self.name[0].family, self.id, self.name[0].pprofile_id)


    def serialize(self):
        """ Serializes a profile into a dictionary """
        pprofile = {
            "id": self.id,
            "resourceType": self.resourceType,
            "active": self.active,
            "birthDate": self.DOB.strftime("%Y-%m-%d"),
            "gender": self.gender.name, # convert enum to string
            "phone_home": self.phone_home,
            "phone_office": self.phone_office,
            "phone_cell": self.phone_cell,
            "email": self.email,
            "name": [],
            "address": []
        }

        #prepare name list
        for _nm in self.name:
            pprofile["name"].append(_nm.serialize())

        #prepare address list
        for addr in self.address:
            pprofile["address"].append(addr.serialize())

        return pprofile

    def deserialize(self, data):
        """
        Deserializes a Pat from a dictionary

        Args:
            data (dict): A dictionary containing the Pat data
        """
        try:
            self.resourceType = data.get("resourceType")
            self.active = data["active"]

            #validate the DOB
            self.DOB = datetime.strptime(data["birthDate"], "%Y-%m-%d")

            self.gender = getattr(Gender, data["gender"])   # create enum from

            #parse name
            name_list = data["name"]
            for json_name in name_list:
                _name = Pname()
                _name.deserialize(json_name)
                self.name.append(_name)

            #assign phone number and email address by parsing telecom jason
            telecom_list = data["telecom"]
            for json_telecom in telecom_list:
                ptcom = PTelecom()
                _telecom = ptcom.deserialize(json_telecom)
                if _telecom.system == "phone":
                    #validate the phone number
                    if phoneNumb.match(_telecom.value):
                        if _telecom.use == "home":
                            self.phone_home = _telecom.value
                        elif _telecom.use == "office":
                            self.phone_office = _telecom.value
                        elif _telecom.use == "cell":
                            self.phone_cell = _telecom.value
                        else: #assign the phone to the home phone if no telecom.use value
                            self.phone_home = _telecom.value

                    else:
                        raise DataValidationError("Invalid home phone")
                elif _telecom.system == "email":
                    #validate the email address
                    self.email = None
                    if _telecom.value:
                        self.email = validate_email(_telecom.value).email

            #parse address
            addr_list = data["address"]
            for json_addr in addr_list:
                _addr = Paddress()
                _addr.deserialize(json_addr)
                self.address.append(_addr)

        except KeyError as error:
            raise DataValidationError("Invalid patient: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError("Invalid patient: body of request contained bad or no data")
        except EmailNotValidError as error:
            raise DataValidationError("Invalid email address")
        except ValueError as error:
            raise DataValidationError("Invalid date value or format")
        return self



    @classmethod
    def find_by_phone(cls, phone_home):
        """ Returns the Pat having the home phone number

        Args:
            phone_home (string): the home phone of the Pat you want to match
        """
        logger.info("Processing phone query for %s ...", phone_home)
        return cls.query.filter(cls.phone_home == phone_home)


    @classmethod
    def find_by_email(cls, email):
        """ Returns all of the Pats with the same email

        Args:
            email (string): the email of the Pats you want to match
        """
        logger.info("Processing email query for %s ...", email)
        return cls.query.filter(cls.email == email)

    @classmethod
    def find_by_active(cls, active=True):
        """ Returns all Pats by their active status

        Args:
            active (boolean): True for Pats that are active
        """
        logger.info("Processing active query for %s ...", active)
        return cls.query.filter(cls.active == active)


    @classmethod
    def find_by_gender(cls, gender=Gender.unknown):
        """ Returns all Pats by their Gender

        Args:
            Gender (enum): Options are ['male', 'female', 'unknown']
        """
        logger.info("Processing gender query for %s ...", gender.name)
        return cls.query.filter(cls.gender == gender)

    @classmethod
    def find_by_lname(cls, family):
        """ Returns all Pats with the family name

        Args:
            family (string): the last name of Pats you want to match
        """
        logger.info("Processing family name query for %s ...", family)
        #return cls.query.filter(cls.family == family)
        return cls.query.join(Pname).filter(Pname.family == family).all()


    @classmethod
    def find_by_fname(cls, given_1):
        """ Returns all Pats with the given name

        Args:
            given_1 (string): the first name of Pats you want to match
        """
        logger.info("Processing first name query for %s ...", given_1)
        #return cls.query.filter(cls.given_1 == given_1)
        return cls.query.join(Pname).filter(Pname.given_1 == given_1).all()

    @classmethod
    def find_by_name(cls, given_1, family):
        """ Returns all Pats with the given name and family name

        Args:
            given_1 (string): the first name of Pats you want to match
            family (string): the last name of Pats you want to match
        """
        logger.info("Processing first name query for %s ...", given_1)
        return cls.query.join(Pname).filter(Pname.given_1 == given_1, Pname.family==family).all()


    @classmethod
    def find_by_zip(cls, postalCode):
        """ Returns all of the Pats having the zip code

        Args:
            postalCode (string): the zip code of the Pat you want to match
        """
        logger.info("Processing zip code query for %s ...", postalCode)
        #return cls.query.filter(cls.postalCode == postalCode)
        #return Paddress.query.filter( Paddress.postalCode == postalCode, Paddress.pat_id == cls.id ).all()
        return cls.query.join(Paddress).filter(Paddress.postalCode == postalCode).all()




######################################################################
# NAME MODEL
######################################################################

class Pname(db.Model, PatBase):
    """
    Class that represents patient's name record

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """


    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    pprofile_id = db.Column(db.Integer, db.ForeignKey('pprofile.id'), nullable=False)
    #pprofile_id = db.Column(db.Integer, db.ForeignKey('pprofile.id', ondelete='cascade'))
    #pprofile = db.relationship('Pprofile', db.backref('pnames', cascade="all, delete-orphan"), foreign_keys=[pprofile_id], lazy='joined')
    use = db.Column(db.String(20), nullable=True)
    family = db.Column(db.String(60), nullable=False)
    given_1 = db.Column(db.String(60), nullable=False)
    given_2 = db.Column(db.String(60), nullable=True)
    prefix_1 = db.Column(db.String(60), nullable=True)
    prefix_2 = db.Column(db.String(60), nullable=True)

    def __repr__(self):
        return "<Pat fname=%r lname=%r id=[%s] profile=[%s]>" % (self.given[0], self.family, self.id, self.pat_id)


    def serialize(self):
        """ Serializes a patient name into a dictionary """
        pname = {
            "id": self.id,
            "pad_id": self.pprofile_id,
            "use": self.use,
            "family": self.family,
            "given": [],
            "prefix": []
        }

        #prepare first name list
        pname["given"].append(self.given_1)
        if self.given_2:
            pname["given"].append(self.given_2)

        #prepare prefix list
        if self.prefix_1:
            pname["prefix"].append(self.prefix_1)
        if self.prefix_2:
            pname["prefix"].append(self.prefix_2)

        return pname

    def deserialize(self, data):
        """
        Deserializes a patient name from a dictionary

        Args:
            data (dict): A dictionary containing the Pat data
        """
        try:
            self.use = data.get("use")
            self.family = data["family"]

            #parse first name list
            fname_list = data["given"]
            self.given_1 = fname_list[0]
            if len(fname_list) >1:
                self.given_2 = fname_list[1]

            #parse prefix list
            prefix_list = data["prefix"]
            self.prefix_1 = prefix_list[0]
            if len(prefix_list) > 1:
                self.prefix_2 = prefix_list[1]

        except KeyError as error:
            raise DataValidationError("Invalid patient: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError("Invalid patient: body of request contained bad or no data")
        except ValueError as error:
            raise DataValidationError("Invalid date value or format")
        return self



######################################################################
# TELECOME CLASS
######################################################################

class PTelecom(object):
    """
    Class that represents patient's telcommunication json
    """
    def __init__(self, system=None, value=None, use=None):
        self.system = system
        self.value = value
        self.use = use

    def serialize(self):
        """ Serializes a patient telecom into a dictionary """
        return {

            "system": self.system,
            "value": self.value,
            "use" : self.use
        }


    def deserialize(self, data):
        """
        Deserializes a patient telecom from a dictionary

        Args:
            data (dict): A dictionary containing the Telecom data
        """
        try:
            self.system = data.get("system")
            if self.system:
                self.value = data["value"]
                self.use = data.get("use")

        except KeyError as error:
            raise DataValidationError("Invalid patient: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError("Invalid patient: body of request contained bad or no data")
        except ValueError as error:
            raise DataValidationError("Invalid date value or format")
        return self


######################################################################
# NAME ADDRESS
######################################################################

class Paddress(db.Model, PatBase):
    """
    Class that represents patient's address record

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    pprofile_id = db.Column(db.Integer, db.ForeignKey('pprofile.id'), nullable=False)
    use = db.Column(db.String(20), nullable=False)
    Type = db.Column(db.String(20), nullable=True)
    text = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(60), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    postalCode = db.Column(db.String(10), nullable=False)
    country = db.Column(db.String(60), nullable=False)

    #street address 1 (required) and 2 (optional)
    line_1 = db.Column(db.String(80), nullable=False)
    line_2 = db.Column(db.String(80), nullable=True)

    def __repr__(self):
        return "<Pat city=%r state=%r zip=%r id=[%s] profile=[%s]>" % (self.city, self.state, self.postalCode, self.id, self.pat_id)


    def serialize(self):
        """ Serializes a patient address into a dictionary """
        paddress = {
            "id": self.id,
            "pat_id": self.pprofile_id,
            "use": self.use,
            "type": self.Type,
            "text": self.text,
            "line": [],
            "city": self.city,
            "state": self.state,
            "postalCode": self.postalCode,
            "country": self.country
        }

        #prepare line list
        paddress["line"].append(self.line_1)
        if self.line_2:
            paddress["line"].append(self.line_2)

        return paddress

    def deserialize(self, data):
        """
        Deserializes a patient address from a dictionary

        Args:
            data (dict): A dictionary containing the Pat data
        """
        try:
            self.use = data["use"]
            self.Type = data.get("type")
            self.text = data.get("text")
            self.city = data["city"]
            self.state = data["state"]
            self.country = data["country"]
            #validate the zip code
            if zipCode.match(data["postalCode"]):
                self.postalCode = data["postalCode"]
            else:
                raise DataValidationError("Invalid postal code")

            #parse line address
            line_list = data["line"]
            self.line_1 = line_list[0]
            if len(line_list) > 1:
                self.line_2 = line_list[1]

        except KeyError as error:
            raise DataValidationError("Invalid patient: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError("Invalid patient: body of request contained bad or no data")
        except ValueError as error:
            raise DataValidationError("Invalid date value or format")
        return self

