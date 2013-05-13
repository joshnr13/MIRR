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


def get_and_show_irr_distribution(number, field, yearly):
    """Gets from DB and shows last @number of IRRs distribution
    selected by @field, using yearly suffix"""

    if yearly:
        field += '_y'

    db = get_connection()
    collection = db['collection']

    try:
        results = collection.find({field:  { '$exists' : True }}, {field: True,'_id': False}).sort([("$natural", 1)]).limit(number);
        irrs = []
        for doc in results:
            irrs.append(doc[field])

        title = "Histogram of %s using last %s values" %(field, len(irrs))
        if len(irrs) > 0:
            show_distribution(irrs, title)
        else :
            print "No IRR values in database. Cant plot charts!"

    except:
        print "Unexpected error:", sys.exc_info()


def show_distribution(values, title):
    pylab.hist(values, bins=7)
    pylab.title(title)
    pylab.show()


if __name__ == '__main__':

    get_and_show_irr_distribution(10, 'irr_owners', False)