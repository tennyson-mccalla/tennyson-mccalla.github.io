# Database Enhancement

## Narrative

Initially all of my thoughts on this enhancement centered around adding the ability to directly export raw data from the embedded board to a MongoDB database. Despite hours of attempts to reconcile apparently irreconcilable "includes", get syntax correct, and scour the internet for any conjunction of a subset of terms like "ti" "texas instruments" "ccs" "mongodb" "mongoc" etc. things simply didn't work.

This meant adopting a different approach fairly late in the game.

Rather than a direct export of raw sensor data to the database I'd employ an indirect medium that could connect the two systems: a CSV/text file. With every iteration of the infinite loop a write operation would be performed that would put out the data (that was previously only going out via the UART) to a CSV/text file.

![UART output]({{site.url}}/media/Screen%20Recording%202022-02-25%20at%2015.56.31.mov)

![Watch the CSV file grow]({{site.url}}/media/Screen%20Recording%202022-02-25%20at%2015.57.50.mov)

Once [the CSV/text]({{site.url}}/database_stuff/temps_outfile.csv) file was big enough for my tastes I went about importing it into mongoDB. I previously went into the mongo shell (mongosh) and created a db and collection (both called ti_temps) and performed a test insert of a single document. MongoDB apparently will not show the database in the "show dbs" list until some data has been added to it. After that I left the mongosh and used mongoimport as in the screenshot below:

![Show dbs and mongoimport]({{site.url}}/media/Screen%20Shot%202022-02-25%20at%2016.07.18.png)

The other alteration was to customize [an old Python pyMongo class]({{site.url}}/database_stuff/animal_shelter.py) for use with this new db/collection/authentication (that last one because security is important!):

## Python Script

[therm_records.py]({{site.url}}/database_stuff/therm_records.py)

```python
#!/usr/bin/env python3

from pymongo import MongoClient
from bson.json_util import dumps
import urllib.parse

class thermRecords(object):
    """ CRUD operations for ti_temps collection in MongoDB """

    def __init__(self, username=None, password=None, dbName=None):
        # Initializing the MongoClient. This helps to 
        # access the MongoDB databases and collections.

        # percent escaping inputs. See below link for details:
        # https://pymongo.readthedocs.io/en/latest/examples/authentication.html
        username = urllib.parse.quote_plus(username)
        password = urllib.parse.quote_plus(password)
        dbName = urllib.parse.quote_plus(dbName)
        
        self.client = MongoClient(f'mongodb://{username}:{password}@localhost:27017/{dbName}') # improved for modern python
        self.database = self.client['ti_temps']

    # the C in CRUD.
    def create(self, data=None):
        if data is not None:
            if isinstance(data, dict):
                insert = self.database.ti_temps.insert_one(data)  # data should be dictionary
            elif isinstance(data, list):
                insert = self.database.ti_temps.insert_many(data) # data should be a list of dicts

            # could replace this with "return bool(insert)" but explicit is better than implicit
            if insert: # test to see if insert is empty
                return True
            else:
                return False
        else:
            raise Exception("Nothing to save, because data parameter is empty")

    # the R in CRUD. 
    def read(self, lookup):
        data = self.database.ti_temps.find(lookup, {"_id" : False})
        return data

    # the U in CRUD. 
    def update(self, lookup, insert):
        if lookup is not None and insert is not None: # ensure that neither arg is None
            if lookup and insert: # ensure that neither arg is empty
                response = self.database.ti_temps.update_one(lookup, {"$set": insert}) # use $set
                if response.modified_count > 0: # if successful modified is positive
                    data = self.database.ti_temps.find_one(lookup) # call find_one on lookup item
                    return dumps(data) # return string of JSON
                else:
                    return "Nothing updated"

        else:
            raise Exception("Nothing to update, because lookup or insert parameter is empty")

    # the D in CRUD. 
    def delete(self, lookup):
        if lookup is not None: # ensure that lookup arg is None
            if lookup: # ensure that lookup arg is not empty
                response = self.database.ti_temps.delete_one(lookup)
                if response.deleted_count > 0:
                    data = self.database.ti_temps.find_one(lookup)
                    return dumps(data)
                else:
                    return "Nothing deleted"
        else:
            raise Exception("Nothing to delete, because either lookup or insert parameter is empty")
```

[tennyson-mccalla.github.io](https://tennyson-mccalla.github.io)
