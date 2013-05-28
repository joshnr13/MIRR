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

        self.simulation_numbers = self.db['simulation_numbers']
        self.simulations = self.db['simulations']
        self.iterations = self.db['iterations']
        self.add_iteration_index()

    def get_connection(self):
        """get connection to db"""
        try:
            connection = pymongo.Connection()
        except pymongo.errors.ConnectionFailure:
            print "Please run MONGO SERVER"
            raise

        db = connection['MirrDatabase']
        return db

    def add_iteration_index(self):
        self.iterations.ensure_index('simulation', background=True )

    def delete_simulation(self, simulation_no ):
        """Deletes selected simulation with @simulation_no"""
        self.simulations.remove({"simulation":simulation_no})
        self.iterations.remove({"simulation":simulation_no})
        print "Succesfully deleted simulation %s" % simulation_no
        if simulation_no == self.get_last_simulation_no():
            self.simulation_numbers.update({'_id':'seq'}, {'$inc':{'seq':-1}}, upsert=True)

    def insert_simulation(self,  line):
        """Safe inserts simulation line to DB"""
        self.simulations.insert(line, safe=True)

    def insert_iteration(self,  line):
        """Safe inserts iterations line to DB"""
        self.iterations.insert(line, safe=True)

    def get_last_simulation_no(self):
        """Get last simulation number"""
        return  self.simulation_numbers.find_one()['seq']

    def get_iterations_number(self, simulation_no):
        """return  number of iterations of current @simulation_no"""
        field = 'iterations_number'
        return  self.get_simulation_field(simulation_no, field)

    def get_simulation_field(self, simulation_no, field):
        """return  1 field from db collection simulations limited by @simulation_no"""
        return  self.simulations.find_one({'simulation': simulation_no}, {field: 1}).get(field, "no-result or error")

    def get_iteration_field(self, simulation_no, iteration_no, field):
        """return  1 field from db collection simulations limited by @simulation_no and @iteration_no"""
        return  self.iterations.find_one({'simulation': simulation_no, 'iteration': iteration_no}, {field: 1}).get(field, "no-result or error")

    def get_next_simulation_no(self):
        """Get next simulation number
        """
        self.simulation_numbers.update({'_id':'seq'}, {'$inc':{'seq':1}}, upsert=True)
        return  self.get_last_simulation_no()

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
            results = self.iterations.find(select_by, get_values).sort(sorted_order).limit(number)
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
            if not field:
                continue
            if field not in not_changing_fields:
                field = add_yearly_prefix(field, yearly)
            select_by[field] = { '$exists' : True }
            get_values[field] = True
        return  select_by, get_values

    def _get_results_find_limit_simulation(self, fields, select_by, get_values, yearly, convert_to=None, not_changing_fields=[],
                                           collection='iterations', one_result=False):
        """Internal method to get results from last iterations"""

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

        def process_doc_1result(doc):
            if isinstance(doc, dict):
                for k in fields_names:
                    if doc.has_key(k):
                        values[k]=doc[k]
                for k in sub_keys:
                    if doc.has_key(k):
                        process_doc(doc[k])
            elif isinstance(doc, list):
                for l in doc:
                    process_doc(l)

        try:
            sorted_order = [("simulation", -1)]
            results = self.db[collection].find(select_by, get_values).sort(sorted_order)
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

            if one_result:
                for doc in results:
                    process_doc_1result(doc)
            else:
                for doc in results:
                    process_doc(doc)

            return values

        except:
            print "Unexpected error:", sys.exc_info()
            #raise
            return {}

    def get_simulation_values_from_db(self,  simulation_no, fields):
        """Gets data from collection 'simulations'
        """
        self.check_simulation(simulation_no)
        select_by, get_values = self.format_request(fields, [], False)
        results = self._get_results_find_limit_simulation(fields, select_by, get_values,
                                               yearly=False,
                                               collection='simulations')
        return  results

    def check_simulation(self, simulation_no):
        last_number_simulation = self.get_last_simulation_no()
        if simulation_no > last_number_simulation:
            print ValueError("Not such simulation in DB. Last simulation is %s" %last_number_simulation)

    def get_iteration_values_from_db(self,  simulation_no, fields, yearly, not_changing_fields=[], iteration_no=None, one_result=False):
        """Gets from DB and shows @fields from LAST @number of simulations
        if iteration_no is not None, also filters by iteration no
        - using not_changing_fields with out prefix and
        - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
        - using yearly suffix

        - and limited to @number
        - SORTED in BACK order
        """
        self.check_simulation(simulation_no)
        fields = not_changing_fields + fields
        select_by, get_values = self.format_request(fields, not_changing_fields, yearly)
        select_by['simulation'] =  simulation_no
        if iteration_no:
            select_by['iteration'] =  iteration_no
            one_result = True

        results = self._get_results_find_limit_simulation(fields, select_by, get_values, yearly, not_changing_fields=not_changing_fields, one_result=one_result)

        return  results

    def get_correlation_values(self, main_field, simulation_id, yearly=False):
        """get correlation of main_field with CORRELLATION_FIELDS"""

        fields = CORRELLATION_FIELDS.values()
        results = self.get_iteration_values_from_db(simulation_id, fields, yearly, not_changing_fields=[main_field])
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
        self.simulations.update({'simulation': simulation_no,},{"$set":{'comment': comment}} , multi=True, safe=True)
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
                     "iterations_number": {'$last':"$iterations_number"},
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
        results = self.simulations.aggregate(pipeline)['result']
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
    #print d.get_iteration_field(4, 1, 'equipment_description')
    #d.update_simulation_comment(35, "test")
    ##d.get_last_simulations_log()
    #select_by = {
                 ##'main_configs.real_construction_duration': {'$exists': True},
                 ##'sm_configs.subsidy_duration': {'$exists': True},
                 ##'sm_configs.subsidy_delay': {'$exists': True},
                 #'simulation': 66,
                 ##'iterations.npv_project_y': {'$exists': True},
                 #'iterations.sm_configs.kWh_subsidy': {'$exists': True},
                 #'iterations.main_configs.real_permit_procurement_duration': {'$exists': True},
                 #}
    #get_values = {'iterations.iteration': True, 'simulation': True,}
    sorted_order = [("simulation", -1)]
    select_by =    {'main_configs.real_construction_duration': {'$exists': True}, 'sm_configs.subsidy_duration': {'$exists': True}, 'sm_configs.subsidy_delay': {'$exists': True}, 'irr_project_y': {'$exists': True}, 'simulation': 11, 'sm_configs.kWh_subsidy': {'$exists': True}, 'main_configs.real_permit_procurement_duration': {'$exists': True}}

    get_values = {'sm_configs.subsidy_duration': True, 'main_configs.real_construction_duration': True, 'sm_configs.subsidy_delay': True, 'irr_project_y': True, 'sm_configs.kWh_subsidy': True, 'main_configs.real_permit_procurement_duration': True, '_id': False}

    r = d.iterations.find(select_by, get_values)  #.sort(sorted_order)
    print "--"
    for rr in r:
        print rr
