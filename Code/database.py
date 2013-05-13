import sys
import  pymongo
import pylab

def get_connection():
    """get connection to db"""
    try:
        connection = pymongo.Connection()
    except pymongo.errors.ConnectionFailure:
        print "Please run MONGO SERVER"
        raise

    db = connection['MirrDatabase']
    return db

def test_database_read():
    """Test function to return some data from database"""
    db = get_connection()
    collection = db['collection']

    try:
        results = collection.find().sort("$natural")

        for doc in results:
            print "Iteration %s \n" % doc["hash_iteration"]
            #print doc
            print "Revenue\n\n"
            print doc['revenue']
            print
            print

    except:
        print "Unexpected error:", sys.exc_info()[0]


def get_irr_values_from_db(number, field, yearly):
    """Gets from DB and shows last @number of IRRs distribution
    selected by @field, using yearly suffix"""

    if yearly:
        field += '_y'

    db = get_connection()
    collection = db['collection']

    try:
        results = collection.find({field:  { '$exists' : True }}, {field: True,'_id': False}).sort([("$natural", -1)]).limit(number);
        irrs = []
        for doc in results:
            irrs.append(doc[field])
        return irrs

    except:
        print "Unexpected error:", sys.exc_info()
        return []





if __name__ == '__main__':

    print get_irr_values_from_db(10, 'irr_owners', False)