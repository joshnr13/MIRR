import sys
import  pymongo
import pylab
from collections import defaultdict
from numbers import Number

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


def add_yearly_prefix(field, yearly):
    if yearly:
        if field.find('.') == -1:
            field += '_y'
            return field
    return field


def get_values_from_db(number, fields, yearly):
    """Gets from DB and shows LAST @number of fields
    - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
    - using yearly suffix
    - and limited to @number
    - SORTED in BACK order
    """

    db = get_connection()
    collection = db['collection']

    select_by = {}
    get_values = {}

    for field in fields:
        field = add_yearly_prefix(field, yearly)
        select_by[field] = { '$exists' : True }
        get_values[field] = True

    try:
        sorted_order = [("$natural", -1)]
        results = collection.find(select_by, get_values).sort(sorted_order).limit(number)
        values = defaultdict(list)
        for doc in results:
            for field in fields:
                field = add_yearly_prefix(field, yearly)
                if "." in field:
                    names = field.split('.')[::-1]
                    value = doc[names.pop()]
                    while names:
                        value = value[names.pop()]
                else:
                    value = doc[field]

                values[field].append(value)

        return values

    except:
        print "Unexpected error:", sys.exc_info()
        return {}


def get_rowvalue_from_db(fields, yearly):
    """Gets 1 LAST ROW from DB
    - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
    - using yearly suffix
    """
    dic_values = get_values_from_db(1, fields, yearly)
    result = []

    for field in fields:
        field = add_yearly_prefix(field, yearly)
        value = dic_values[field]
        row = filter(lambda x :isinstance(x, (Number, list)), value)
        if row:
            row = row[0]
            if isinstance(row, list):
                row = filter(lambda x :isinstance(x, Number), row)
            result.append(row)

    return result


#def test():
    #select_by =  {'irr_owners_y': {'$exists': True}, 'main_configs.lifetime_y': {'$exists': True}, 'irr_project_y': {'$exists': True}}
    #get_values =
    #sorted_order =
    #number = 1
    #results = collection.find(select_by, get_values).sort(sorted_order).limit(number)

if __name__ == '__main__':
    fields = ['irr_owners', 'irr_project', 'main_configs.lifetime', 'revenue', 'npv_project']
    fields = [ 'npv_project', 'wacc', 'fcf_project']
    #print get_rowvalue_from_db( fields, True)
    print get_rowvalue_from_db( fields, False)