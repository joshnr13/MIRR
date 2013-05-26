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
        self.add_simulation_index()

    def get_connection(self):
        """get connection to db"""
        try:
            connection = pymongo.Connection()
        except pymongo.errors.ConnectionFailure:
            print "Please run MONGO SERVER"
            raise

        db = connection['MirrDatabase']
        return db

    def add_simulation_index(self):
        self.collection.ensure_index('simulation', background=True )

    def delete_simulation(self, simulation_no ):
        """Deletes selected simulation with @simulation_no"""
        self.collection.remove({"simulation":simulation_no})
        print "Succesfully deleted simulation %s" % simulation_no
        if simulation_no == self.get_last_simulation_no():
            self.simulations.update({'_id':'seq'}, {'$inc':{'seq':-1}}, upsert=True)

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

    def format_request(self,  fields, not_changing_fields, yearly):
        """formats request to database, returns dicts with select and get values"""
        select_by = {}
        get_values = {'_id': False}

        for field in fields:
            if field not in not_changing_fields:
                field = add_yearly_prefix(field, yearly)
            select_by[field] = { '$exists' : True }
            get_values[field] = True
        return  select_by, get_values

    def _get_results_find_limit_simulations(self, fields, select_by, get_values, yearly, convert_to=None, not_changing_fields=[]):
        """Internal method to get results from last simulations"""

        def process_doc(doc):
            if isinstance(doc, dict):
                for k in fields_names:
                    if doc.has_key(k):
                        values[k].append(doc[k])
                for k in sub_keys:
                    if doc.has_key(k):
                        process_doc(doc[k])
            elif isinstance(doc, list):
                for l in doc:
                    process_doc(l)

        try:
            sorted_order = [("simulation", -1)]
            results = self.collection.find(select_by, get_values).sort(sorted_order)
            values = defaultdict(list)

            fields_names = []
            sub_keys = []
            for field in fields:

                splitted_field = field.split('.')
                sub_keys += splitted_field[:-1]

                field_name = splitted_field[-1]
                if field_name not in not_changing_fields and field not in not_changing_fields:
                    field_name = add_yearly_prefix(field_name, yearly)
                fields_names.append(field_name)

            sub_keys = set(sub_keys)
            for doc in results:
                process_doc(doc)

            return values

        except:
            print "Unexpected error:", sys.exc_info()
            raise
            return {}

    def get_simulations_values_from_db(self,  simulation_id, fields, yearly, convert_to=None, not_changing_fields=[]):
        """Gets from DB and shows @fields from LAST @number of simulations
        - using not_changing_fields with out prefix and
        - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
        - using yearly suffix

        - and limited to @number
        - SORTED in BACK order
        """

        last_number_simulation = self.get_last_simulation_no()
        if simulation_id > last_number_simulation:
            print ValueError("Not such simulation in DB. Last simulation is %s" %last_number_simulation)
            return  None
        fields = not_changing_fields + fields
        select_by, get_values = self.format_request(fields, not_changing_fields, yearly)
        select_by['simulation'] =  simulation_id
        results = self._get_results_find_limit_simulations(fields, select_by, get_values, yearly, convert_to, not_changing_fields)

        return  results

    def get_correlation_values(self, main_field, simulation_id, yearly=False):
        """get correlation of main_field with CORRELLATION_FIELDS"""

        main_field_fordb = "iterations." + main_field

        fields = CORRELLATION_FIELDS.values()
        results = self.get_simulations_values_from_db(simulation_id, fields, yearly, not_changing_fields=[main_field_fordb])
        if not results:
            print ValueError('No data in Database for simulation %s' %simulation_id)
            return None

        main_list_values = results.pop(main_field)
        number_values_used = len(main_list_values)

        correllation_dict = {}
        for k, v in results.items():
            cor = corrcoef([main_list_values, v] )[0][1]
            rounded_value = round(cor, 3)
            correllation_dict[k] = rounded_value

        return  correllation_dict, number_values_used

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

    def update_simulation_comment(self, simulation_no, comment):
        """Updates comment in simulation"""
        self.collection.update({'simulation': simulation_no,},{"$set":{'comment': comment}} , multi=True, safe=True)
        print "Updated comment for simulation %s : %s" % (simulation_no, comment)


    def get_last_simulations_log(self, last=10):
        last_simulation_no = self.get_last_simulation_no()
        min_s =  last_simulation_no - last
        max_s = last_simulation_no

        #group_by =  {"_id" : "$simulation",
                     #"iterations":  {"$sum":1},
                     #"date": {"$last": "$date"},
                     #"comment" : {"$last": "$comment"},}
        group_by =  {
                     "_id" : "$simulation",
                     "iterations_number": {'$last':"$iteration_number"},
                     "date": {'$last': "$date"},
                     "comment" : {'$last': "$comment"},
                     }

        project = {
                  '_id': '$simulation',
                  'simulation': '$simulation',
                  "comment":True,
                  #'len': {"$size": "$iterations",},
                  "len": {"$sum": "$simulation.iterations"},
                    }

        pipeline = [
            #{'$project': project},
            {'$match': {'simulation': {'$lte': max_s, '$gte': min_s,}} },
            #{ '$skip': ...some skip... },
            #{ '$limit': ...some limit... }
            {"$group" : group_by},
            { '$sort': {'_id': 1},},
            ]
        results = self.collection.aggregate(pipeline)['result']
        for r in results:
            print u"Simulation %s date %s - iterations %s - %s" % (r["_id"], r["date"], r["iterations_number"], r['comment'])




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
    d.update_simulation_comment(35, "test")
    #d.get_last_simulations_log()
    select_by = {
                 #'main_configs.real_construction_duration': {'$exists': True},
                 #'sm_configs.subsidy_duration': {'$exists': True},
                 #'sm_configs.subsidy_delay': {'$exists': True},
                 'simulation': 66,
                 #'iterations.npv_project_y': {'$exists': True},
                 'iterations.sm_configs.kWh_subsidy': {'$exists': True},
                 'iterations.main_configs.real_permit_procurement_duration': {'$exists': True},
                 }
    get_values = {'iterations.iteration': True, 'simulation': True,}
    sorted_order = [("simulation", -1)]
    r = d.collection.find(select_by, get_values).sort(sorted_order)
    print "--"
    for rr in r:
        print rr
