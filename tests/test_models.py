# Tests for Data Models

"""
Test cases for Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convinient to use this:
    nosetests --stop tests/test_models.py:TestPatModel

"""
import os
import logging
import unittest
from datetime import datetime
import json
from werkzeug.exceptions import NotFound
from service.models import Pprofile, Pname, Paddress, Gender, DataValidationError, db
from service import app
import copy
#from .factories import PatFactory


#read the sample jason to dictionary list and provide for test
with open('tests/fhir-patient-post.json') as jsonfile:
    sample_data = json.load(jsonfile)

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres1@localhost:5432/postgres"
)

######################################################################
#  MODEL TEST CASES
######################################################################
class TestPatModel(unittest.TestCase):
    """ Test Cases for Model """

    @classmethod
    def setUpClass(cls):
        """ These run once per Test suite """
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Pprofile.init_db(app)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_update_a_pat(self):
        """ Update a patient """
        pat = Pprofile()
        pat = pat.deserialize(sample_data)
        logging.debug(pat)
        pat.create()
        logging.debug(pat)
        self.assertEqual(pat.id, 1)
        # Change it an save it
        pat.address[0].postalCode = "97600"
        original_id = pat.id
        pat.save()
        self.assertEqual(pat.id, original_id)
        self.assertEqual(pat.address[0].postalCode, "97600")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        pats = Pprofile.all()
        self.assertEqual(len(pats), 1)
        self.assertEqual(pats[0].id, 1)
        self.assertEqual(pats[0].address[0].postalCode, "97600")

    def test_create_a_pat(self):
        """ Create a patient and assert that it exists """
        pat = Pprofile(resourceType="Patient", active=True, phone_home="5107939896", email="dog@us.ibm.com", DOB=datetime.strptime('2010-10-09', "%Y-%m-%d"), gender=Gender.female)
        pname = Pname(given_1="Daisy", family="Dog")
        paddr = Paddress(use="home", line_1="2000 Highland", postalCode="98765", city="Hayward", state="CA")
        pat.name.append(pname)
        pat.address.append(paddr)

        self.assertTrue(pat != None)
        self.assertEqual(pat.id, None)
        self.assertEqual(pat.name[0].given_1, "Daisy")
        self.assertEqual(pat.address[0].postalCode, "98765")
        self.assertEqual(pat.address[0].city, "Hayward")
        self.assertEqual(pat.gender, Gender.female)
        self.assertEqual(pat.DOB, datetime.strptime('2010-10-09', "%Y-%m-%d"))
        

    def test_add_a_pat(self):
        """ Create a patient and add it to the database """

        pats = Pprofile.all()
        self.assertEqual(pats, [])
        pat = Pprofile(resourceType="Patient", active=True, phone_home="3108939845", email="cat@us.ibm.com", DOB=datetime.strptime('2019-12-31', "%Y-%m-%d"), gender=Gender.male)
        pname = Pname(prefix_1="Mr", given_1="Sweetheart", family="Cat")
        paddr = Paddress(use="home", line_1="2001 Highland", postalCode="98764", city="Los Angeles", state="CA", country="USA")
        pat.name.append(pname)
        pat.address.append(paddr)

        self.assertTrue(pat != None)
        self.assertEqual(pat.id, None)
        pat.create()
        # Asert that it was assigned an id and shows up in the database
        self.assertEqual(pat.id, 1)
        pats = Pprofile.all()
        self.assertEqual(len(pats), 1)

    def test_update_a_pat(self):
        """ Update a patient """
        pat = Pprofile()
        pat = pat.deserialize(sample_data)
        logging.debug(pat)
        pat.create()
        logging.debug(pat)
        self.assertEqual(pat.id, 1)
        # Change it an save it
        pat.address[0].postalCode = "97600"
        original_id = pat.id
        pat.save()
        self.assertEqual(pat.id, original_id)
        self.assertEqual(pat.address[0].postalCode, "97600")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        pats = Pprofile.all()
        self.assertEqual(len(pats), 1)
        self.assertEqual(pats[0].id, 1)
        self.assertEqual(pats[0].address[0].postalCode, "97600")
        
    def test_delete_a_pat(self):
        """ Delete a patient """
        #pat = PatFactory()
        pat = Pprofile()
        pat = pat.deserialize(sample_data)
        logging.debug(pat)
        pat.create()
        logging.debug(pat)
        pats = Pprofile.all()
        self.assertEqual(len(pats), 1)
        # delete the patient and make sure doesn't exist in the database
        pat = pats[0]
        logging.debug(pat)
        pat.delete()
        logging.debug(pat)
        pats = Pprofile.all()
        self.assertEqual(len(Pprofile.all()), 0)


    def test_serialize_a_pat(self):
        """ Test serialization of a patient """
        #pat = PatFactory()
        pat = Pprofile()
        pat = pat.deserialize(sample_data)
        data = pat.serialize()
        
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], pat.id)
        self.assertEqual(data["phone_home"], pat.phone_home)
        self.assertEqual(data["email"], pat.email)
        self.assertIn("birthDate", data)
        self.assertEqual(data["birthDate"], pat.DOB.strftime("%Y-%m-%d"))
        self.assertIn("gender", data)
        self.assertEqual(data["gender"], pat.gender.name)
        
        self.assertIn("name", data)
        self.assertEqual(len(data["name"]), 1)
        name_data = data["name"][0]
        self.assertIn("family", name_data)
        self.assertEqual(name_data["family"], pat.name[0].family)
        self.assertEqual(len(name_data["given"]), 2)
        self.assertEqual(name_data["given"][0], pat.name[0].given_1)

        self.assertIn("address", data)
        self.assertEqual(len(data["address"]), 1)
        address_data = data["address"][0]
        self.assertEqual(address_data["postalCode"], pat.address[0].postalCode)
        self.assertEqual(address_data["line"][0], pat.address[0].line_1)
        self.assertEqual(address_data["city"], pat.address[0].city)


    def test_deserialize_a_pat(self):
        """ Test deserialization of a patient """
        
        pat = Pprofile()
        pat.deserialize(sample_data)
        self.assertNotEqual(pat, None)
        self.assertEqual(pat.id, None)
        self.assertEqual(pat.name[0].given_1, "Nedward")
        self.assertEqual(pat.name[0].given_2, "Ned")
        self.assertEqual(pat.name[0].prefix_1, "Mr")
        self.assertEqual(pat.name[0].family, "Flanders")

        self.assertEqual(pat.address[0].line_1, "744 Evergreen Terrace")
        self.assertEqual(pat.address[0].state, "IL")
        self.assertEqual(pat.phone_home, "5555551112")
        self.assertEqual(pat.email, "ned.flanders@email.com")
        self.assertEqual(pat.gender, Gender.male)


    def test_deserialize_bad_data(self):
        """ Test deserialization of a patient with bad data """
        #assign a wrong zip code
        pat = Pprofile()
        #s1 = sample_data.copy()
        s1 = copy.deepcopy(sample_data)
        s1["address"][0]["postalCode"]="902109"
        pat = Pprofile()
        self.assertRaises(DataValidationError, pat.deserialize, s1)


    def test_deserialize_missing_data(self):
        """ Test deserialization of a patient with missing required value """
        #miss the required gender
        pat = Pprofile()
        s1 = copy.deepcopy(sample_data)
        del s1["gender"]
        self.assertRaises(DataValidationError, pat.deserialize, s1)
        
        #miss the required last name
        pat = Pprofile()
        s2 = copy.deepcopy(sample_data)
        del s2["name"][0]["family"]
        self.assertRaises(DataValidationError, pat.deserialize, s2)

        #miss the required city
        pat = Pprofile()
        s3 = copy.deepcopy(sample_data)
        del s3["address"][0]["city"]
        self.assertRaises(DataValidationError, pat.deserialize, s3)


    def test_find_pat(self):
        """ Find a patient by ID """
        #pats = PatFactory.create_batch(3)
        pats = [Pprofile() for i in range(1)]
        for idx, _pat in enumerate(pats):
            pat = _pat.deserialize(sample_data)
            pat.create()
        logging.debug(pats)
        # make sure they got saved
        self.assertEqual(len(Pprofile.all()), 1)
        # find the 1st patient in the list
        pat = Pprofile.find(pats[0].id)
        self.assertIsNot(pat, None)
        self.assertEqual(pat.id, pats[0].id)
        self.assertEqual(pat.email, pats[0].email)
        self.assertEqual(pat.name[0].given_1, pats[0].name[0].given_1)
        self.assertEqual(pat.address[0].state, pats[0].address[0].state)

    def test_find_by_phone(self):
        """ Find patients by home phone number """
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()

        pats = Pprofile.find_by_phone("5555551112")
        self.assertEqual(pats[0].name[0].given_1, "Nedward")
        self.assertEqual(pats[0].name[0].family, "Flanders")
        self.assertEqual(pats[0].phone_home, "5555551112")

    def test_find_by_email(self):
        """ Find patients by email """
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()

        pats = Pprofile.find_by_email("ned.flanders@email.com")
        self.assertEqual(pats[0].name[0].given_1, "Nedward")
        self.assertEqual(pats[0].name[0].family, "Flanders")
        self.assertEqual(pats[0].email, "ned.flanders@email.com")

    def test_find_by_active(self):
        """ Find patients by email """
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()

        pats = Pprofile.find_by_active(pat.active)
        self.assertEqual(pats[0].name[0].given_1, "Nedward")
        self.assertEqual(pats[0].name[0].family, "Flanders")
        self.assertEqual(pats[0].active, True)

    def test_find_by_gender(self):
        """ Find patients by gender """
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()

        pats = Pprofile.find_by_gender(Gender.female)
        pat_list = [pat for pat in pats]
        self.assertEqual(len(pat_list), 0)

        pats = Pprofile.find_by_gender(Gender.male)
        pat_list = [pat for pat in pats]
        self.assertEqual(len(pat_list), 1)
        self.assertEqual(pats[0].name[0].given_1, "Nedward")
        self.assertEqual(pats[0].name[0].family, "Flanders")
        self.assertEqual(pats[0].gender.name, Gender.male.name)

    def test_find_by_lname(self):
        """ Find patients by last name """
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()

        pats = Pprofile.find_by_lname("Flanders")
        self.assertEqual(pats[0].name[0].given_1, "Nedward")
        self.assertEqual(pats[0].name[0].family, "Flanders")
        self.assertEqual(pats[0].phone_home, "5555551112")

    def test_find_by_fname(self):
        """ Find patients by first name """
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()

        pats = Pprofile.find_by_fname("Nedward")
        self.assertEqual(pats[0].name[0].given_1, "Nedward")
        self.assertEqual(pats[0].name[0].family, "Flanders")
        self.assertEqual(pats[0].email, "ned.flanders@email.com")

    def test_find_by_zip(self):
        """ Find patients by zip code """
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()

        pats = Pprofile.find_by_zip("90210")
        self.assertEqual(pats[0].name[0].given_1, "Nedward")
        self.assertEqual(pats[0].name[0].family, "Flanders")
        self.assertEqual(pats[0].address[0].postalCode, "90210")


    def test_find_or_404_found(self):
        """ Find or return 404 found """
        pats = []
        for i in range(1):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)
            pat.create()
            pats.append(pat)
        
        pat = Pprofile.find_or_404(pats[0].id)
        self.assertIsNot(pat, None)
        self.assertEqual(pat.id, pats[0].id)
        self.assertEqual(pat.name[0].family, pats[0].name[0].family)
        self.assertEqual(pat.name[0].given_1, pats[0].name[0].given_1)
        self.assertEqual(pat.DOB, pats[0].DOB)


    def test_find_or_404_not_found(self):
        """ Find or return 404 NOT found """
        self.assertRaises(NotFound, Pprofile.find_or_404, 0)
