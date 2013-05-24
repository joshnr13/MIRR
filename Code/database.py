import sys
import  pymongo
import pylab
from collections import defaultdict
from numbers import Number
from annex import add_yearly_prefix
from constants import report_directory, CORRELLATION_FIELDS, CORRELLATION_IRR_FIELD
from numpy import corrcoef, around, isnan

class Database():
    def __init__(self):
        self.db = self.get_connection()
        self.collection = self.db['collection']
        self.iterations = self.db['iteration']
        self.simulations = self.db['simulation']

    def get_connection(self):
        """get connection to db"""
        try:
            connection = pymongo.Connection()
        except pymongo.errors.ConnectionFailure:
            print "Please run MONGO SERVER"
            raise

        db = connection['MirrDatabase']
        return db

    def insert(self,  line):
        """Safe inserts line to DB"""
        self.collection.insert(line, safe=True)

    def get_last_simulation_no(self):
        """Get last simulation number"""
        return  self.simulations.find_one()['seq']

    def get_next_simulation_no(self):
        """Get next simulation number
        """
        self.simulations.update({'_id':'seq'}, {'$inc':{'seq':1}}, upsert=True)
        return  self.get_last_simulation_no()

    def test_database_read(self):
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


    def get_values_from_db(self,  number, fields, yearly):
        """Gets from DB and shows LAST @number of fields
        - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
        - using yearly suffix
        - and limited to @number
        - SORTED in BACK order
        """

        select_by = {}
        get_values = {}

        for field in fields:
            field = add_yearly_prefix(field, yearly)
            select_by[field] = { '$exists' : True }
            get_values[field] = True

        try:
            sorted_order = [("$natural", -1)]
            results = self.collection.find(select_by, get_values).sort(sorted_order).limit(number)
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

    def format_request(self,  fields, yearly):
        """formats request to database, returns dicts with select and get values"""
        select_by = {}
        get_values = {}

        for field in fields:
            field = add_yearly_prefix(field, yearly)
            select_by[field] = { '$exists' : True }
            get_values[field] = True
        return  select_by, get_values

    def format_request_simulation_range(self,  range_values, dic):
        dic['simulation'] =  { '$in' : list(range_values) }

    def get_results_find_limit_iterations(self, number, fields, select_by, get_values, yearly):
        try:
            sorted_order = [("$natural", -1)]
            results = self.collection.find(select_by, get_values).sort(sorted_order).limit(number)
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

    def _get_results_find_limit_simulations(self, fields, select_by, get_values, yearly, convert_to=None):
        """Internal method to get results from last simulations"""
        try:
            sorted_order = [("simulation", -1)]
            results = self.collection.find(select_by, get_values).sort(sorted_order)
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

    def get_simulations_values_from_db(self,  need_prev_simulations, fields, yearly, convert_to=None):
        """Gets from DB and shows @fields from LAST @number of simulations
        - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
        - using yearly suffix
        - and limited to @number
        - SORTED in BACK order
        """

        last_number_simulation = self.get_last_simulation_no()
        if need_prev_simulations > last_number_simulation:
            raise ValueError("Not enough number of simulations in Database")

        simulation_range_numbers = range(last_number_simulation-need_prev_simulations+1, last_number_simulation+1)
        simulation_range_numbers_short = "[%s-%s]" % (min(simulation_range_numbers), max(simulation_range_numbers))

        select_by, get_values = self.format_request(fields, yearly)
        self.format_request_simulation_range(simulation_range_numbers, select_by)
        results = self._get_results_find_limit_simulations(fields, select_by, get_values, yearly, convert_to)

        return  results, simulation_range_numbers_short

    def get_correlation_values(self, main_field, number=30, yearly=False):
        """get correlation of main_field with CORRELLATION_FIELDS"""

        fields = [main_field] + CORRELLATION_FIELDS.values()
        results, simulation_range_numbers = self.get_simulations_values_from_db(number, fields, yearly)

        main_list_values = results.pop(main_field)
        number_values_used = len(main_list_values)

        correllation_dict = {}
        for k, v in results.items():
            cor = corrcoef([main_list_values, v] )[0][1]
            rounded_value = round(cor, 3)
            correllation_dict[k] = rounded_value

        return  correllation_dict, simulation_range_numbers, number_values_used

    def get_rowvalue_from_db(self,  fields, yearly):
        """Gets 1 LAST ROW from DB
        - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
        - using yearly suffix
        """
        dic_values = self.get_values_from_db(1, fields, yearly)
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
    fields = [ 'irr_owners']
    #print get_rowvalue_from_db( fields, True)
    d = Database()
    #print d.get_rowvalue_from_db( fields, False)
    print d.get_simulations_values_from_db( 1, fields, False)