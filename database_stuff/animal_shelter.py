#!/usr/bin/env python3

from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps
import urllib.parse
# from pprint import pformat

class AnimalShelter(object):
    """ CRUD operations for Animal collection in MongoDB """

    def __init__(self, username=None, password=None, dbName=None):
        # Initializing the MongoClient. This helps to 
        # access the MongoDB databases and collections.

        # percent escaping inputs. See below link for details:
        # https://pymongo.readthedocs.io/en/latest/examples/authentication.html
        username = urllib.parse.quote_plus(username)
        password = urllib.parse.quote_plus(password)
        dbName = urllib.parse.quote_plus(dbName)
        
        self.client = MongoClient(f'mongodb://{username}:{password}@localhost:27017/{dbName}') # improved for modern python
        # self.database = self.client['project']
        self.database = self.client['AAC']

    # Complete this create method to implement the C in CRUD.
    def create(self, data=None):
        if data is not None:
            if isinstance(data, dict):
                insert = self.database.animals.insert_one(data)  # data should be dictionary
            elif isinstance(data, list):
                insert = self.database.animals.insert_many(data) # data should be a list of dicts

            # could replace this with "return bool(insert)" but explicit is better than implicit
            if insert: # test to see if insert is empty
                return True
            else:
                return False
        else:
            raise Exception("Nothing to save, because data parameter is empty")

    # Create method to implement the R in CRUD. 
    def read(self, lookup):
        # if lookup is not None:
            # if lookup: # test to see if lookup is empty
                # use lookup, might be any part of doc
        data = self.database.animals.find(lookup, {"_id" : False})
                # for datum in data:
                #     pformat(datum)
        return data
        # else:
            # raise Exception("Nothing to return, because lookup parameter is empty")

    # Create method to implement the U in CRUD. 
    def update(self, lookup, insert):
        if lookup is not None and insert is not None: # ensure that neither arg is None
            if lookup and insert: # ensure that neither arg is empty
                response = self.database.animals.update_one(lookup, {"$set": insert}) # use $set
                if response.modified_count > 0: # if successful modified is positive
                    data = self.database.animals.find_one(lookup) # call find_one on lookup item
                    return dumps(data) # return string of JSON
                else:
                    return "Nothing updated"

        else:
            raise Exception("Nothing to update, because lookup or insert parameter is empty")

    # Create method to implement the D in CRUD. 
    def delete(self, lookup):
        if lookup is not None: # ensure that lookup arg is None
            if lookup: # ensure that lookup arg is not empty
                response = self.database.animals.delete_one(lookup)
                if response.deleted_count > 0:
                    data = self.database.animals.find_one(lookup)
                    return dumps(data)
                else:
                    return "Nothing deleted"
        else:
            raise Exception("Nothing to delete, because either lookup or insert parameter is empty")
