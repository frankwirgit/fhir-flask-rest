# Tests for REST API Service

"""
REST API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convinient to use this:
    nosetests --stop tests/test_service.py:TestPatServer
"""

import os
import logging
import unittest
import json
import copy
from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus
from flask_api import status  # HTTP Status Codes
from service.models import Pprofile, Pname, Paddress, db
from service.service import app, init_db
#from .factories import PatFactory


# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres1@localhost:5432/postgres"
)

with open('tests/fhir-patient-post.json') as jsonfile:
    sample_data = json.load(jsonfile)

######################################################################
#  SERVICE TEST CASES
######################################################################
class TestPatServer(unittest.TestCase):
    """ REST Server Tests """

    @classmethod
    def setUpClass(cls):
        """ Run once before all tests """
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        """ Runs before each test """
        db.drop_all()  # clean up the last tests
        db.create_all()  # create new tables
        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def _create_pats(self, count):
        """ create patients based on sample data """

        pats = []
        #there is only one record in the sample data
        for i in range(count):
            pat = Pprofile()
            pat = pat.deserialize(sample_data)

            #call of the POST method to create pat
            #note: deserialize()+serialize() will not work, because
            #deserialize() breaks the original json in sample_data, 
            #for example, no "telecom" block with "system","value" and "use"
            #but with "phone_home","phone_office"..."email", etc.
            #after serialize(), the json is NOT equal to the sample_data

            #therefore the following call can not get a patient created
            #resp = self.app.post("/pats", json=pat.serialize(), content_type="application/json")
            
            #instead, pass the sample_data json directly to the call of the POST method
            resp = self.app.post("/pats", json=sample_data, content_type="application/json")
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED, "Could not create test patient")
            
            new_pat = resp.get_json()
            pat.id = new_pat["id"]

            #note: pat is not the "created" object
            #no pat.create() has been called. And to verifly, the following assert prints out:
            #root: DEBUG: <Pat fname='Nedward' lname='Flanders' id=[1] pprofile_id=[None]>
            #id is assigned from new_pat["id"], profile_id is None
            logging.debug(pat)
            self.assertEqual(new_pat["address"][0]["pat_id"], 1)
            self.assertEqual(pat.address[0].postalCode, "90210")
            pats.append(pat)

        return pats


    def test_index(self):
        """ Test the Home Page """
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], "Patient FHIR REST API Service")

    def test_get_pat_list(self):
        """ Get a list of patients """
        self._create_pats(1)
        resp = self.app.get("/pats")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)

    def test_get_pat(self):
        """ Get a single patient """
        test_pat = self._create_pats(1)[0]
        # get the id of a patient
        resp = self.app.get(
            "/pats/{}".format(test_pat.id), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["phone_home"], test_pat.phone_home)

    def test_get_pat_by_name(self):
        """ Get a single patient by name """
        test_pat = self._create_pats(1)[0]
        # get the id of a patient
        #resp = self.app.get(
            #"/pats/{}".format(test_pat.id), content_type="application/json")
        resp = self.app.get(
            "".join(["/pats?given=", test_pat.name[0].given_1, "&family=", test_pat.name[0].family]), 
            content_type="application/json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data[0]["name"][0]["given"][0], test_pat.name[0].given_1)
        self.assertEqual(data[0]["name"][0]["family"], test_pat.name[0].family)

    def test_get_pat_by_phone(self):
        """ Get a single patient by phone """
        test_pat = self._create_pats(1)[0]
        # get the id of a patient
        resp = self.app.get(
            "/pats?phone_home={}".format(test_pat.phone_home), content_type="application/json")
    
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data[0]["phone_home"], test_pat.phone_home)

    def test_get_pat_not_found(self):
        """ Get a patient whos not found """
        resp = self.app.get("/pats/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        
        
    def test_create_pat(self):
        """ Create a new patient """
        test_pat = self._create_pats(1)[0]
        #test_pat = PatFactory()
        logging.debug(test_pat)
        resp = self.app.post(
            "/pats", json=sample_data, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)
        # Check the data is correct
        new_pat = resp.get_json()
        self.assertEqual(new_pat["name"][0]["family"], test_pat.name[0].family, "Last name does not match")
        self.assertEqual(new_pat["name"][0]["given"][0], test_pat.name[0].given_1, "First name does not match")
        self.assertEqual(new_pat["address"][0]["postalCode"], test_pat.address[0].postalCode, "Zip code does not match")
        self.assertEqual(new_pat["address"][0]["line"][0], test_pat.address[0].line_1, "Zip code does not match")
        self.assertEqual(new_pat["birthDate"], test_pat.DOB.strftime("%Y-%m-%d"), "DOB does not match")
        # Check that the location header was correct
        resp = self.app.get(location, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Check the data is correct
        new_pat = resp.get_json()
        self.assertEqual(new_pat["name"][0]["family"], test_pat.name[0].family, "Last name does not match")
        self.assertEqual(new_pat["name"][0]["given"][0], test_pat.name[0].given_1, "First name does not match")
        self.assertEqual(new_pat["address"][0]["postalCode"], test_pat.address[0].postalCode, "Zip code does not match")
        self.assertEqual(new_pat["address"][0]["line"][0], test_pat.address[0].line_1, "Zip code does not match")
        self.assertEqual(new_pat["birthDate"], test_pat.DOB.strftime("%Y-%m-%d"), "DOB does not match")

    def test_update_pat(self):
        """ Update an existing patient """
        # create a patient to update
        #test_pat = self._create_pats(1)[0]
        #test_pat = PatFactory()
        resp = self.app.post(
            "/pats", json=sample_data, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # update the patient
        new_pat = resp.get_json()
        new_json = copy.deepcopy(sample_data)
        #modify the item value
        new_json["telecom"][1]["value"] = "daisy.cao@email.com"
        new_json["name"][0]["given"][0] = "Daisy"
        logging.debug(new_json)
        
        resp = self.app.put(
            "/pats/{}".format(new_pat["id"]),
            json=new_json,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_pat = resp.get_json()
        logging.debug(updated_pat)
        #updated the pprofile entry
        self.assertEqual(updated_pat["email"], "daisy.cao@email.com")
        #added a new first name
        self.assertEqual(updated_pat["name"][1]["given"][0], "Daisy")
        self.assertEqual(updated_pat["name"][0]["given"][0], "Nedward")
    

    def test_update_pat_latest_name(self):
        """ Update the latest name of an existing patient """
        # create a patient to update
        resp = self.app.post(
            "/pats", json=sample_data, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_pat = resp.get_json()

        # update the latest name of patient
        modified_name_json = copy.deepcopy(sample_data["name"])
        #modify the name
        modified_name_json[len(modified_name_json)-1]["family"] = "Doggie"
        modified_name_json[len(modified_name_json)-1]["given"][0] = "Daisy"
        logging.debug(modified_name_json)
        
        resp = self.app.put("/pats/{}/latest_name".format(new_pat["id"]), 
            json=modified_name_json[len(modified_name_json)-1], content_type="application/json")
        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_name = resp.get_json()
        logging.debug(updated_name)

        #updated latest name
        self.assertEqual(updated_name["given"][0], "Daisy")
        self.assertEqual(updated_name["family"], "Doggie")


    def test_delete_pat(self):
        """ Delete a patient """
        test_pat = self._create_pats(1)[0]
        resp = self.app.delete(
            "/pats/{}".format(test_pat.id), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        # make sure they are deleted
        resp = self.app.get(
            "/pats/{}".format(test_pat.id), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_pat_list_by_gender(self):
        """ Query patients by gender """
        pats = self._create_pats(1)
        test_gender = pats[0].gender
        gender_pats = [pat for pat in pats if pat.gender.name == test_gender.name]
        resp = self.app.get("/pats", query_string="gender={}".format(quote_plus(test_gender.name)))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), len(gender_pats))
        # check the data just to be sure
        for _dd in data:
            self.assertEqual(_dd["gender"], test_gender.name)
        app.logger.info("run a test for testing query patients with the same gender")

    def test_bad_request(self):
        """ Send wrong media type """
        pat = Pprofile()
        pat = pat.deserialize(sample_data)
        resp = self.app.post("/pats", json=pat.serialize(), content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


    def test_unsupported_media_type(self):
        """ Send wrong media type """
        resp = self.app.post("/pats", json=sample_data, 
            content_type="test/html")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


    def test_method_not_allowed(self):
        """ Make an illegal method call """
        resp = self.app.put(
            "/pats", json=sample_data, 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    # @patch('service.models.Pet.find_by_name')
    # def test_bad_request(self, bad_request_mock):
    #     """ Test a Bad Request error from Find By Name """
    #     bad_request_mock.side_effect = DataValidationError()
    #     resp = self.app.get('/pets', query_string='name=fido')
    #     self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    #
    # @patch('service.models.Pet.find_by_name')
    # def test_mock_search_data(self, pet_find_mock):
    #     """ Test showing how to mock data """
    #     pet_find_mock.return_value = [MagicMock(serialize=lambda: {'name': 'fido'})]
    #     resp = self.app.get('/pets', query_string='name=fido')
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)
