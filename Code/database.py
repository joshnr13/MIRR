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


def show_irr_distribution(number, field, yearly):
    "Shows last @number of IRRs distribution"
    if yearly:
        field += '_y'

    db = get_connection()
    collection = db['collection']

    try:
        results = collection.find({field:  { '$exists' : True }}, {field: True,'_id': False}).sort([("$natural", 1)]).limit(number);
        irrs = []
        for doc in results:
            irrs.append(doc[field])

        pylab.hist(irrs)
        pylab.title("Histogram of %s using last %s values" %(field, number))
        pylab.show()

    except:
        print "Unexpected error:", sys.exc_info()


if __name__ == '__main__':

    show_irr_distribution(10, 'irr_owners', False)