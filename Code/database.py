import sys
import pymongo
from collections import defaultdict
from annex import addYearlyPrefix, convertDictDates
from constants import CORRELLATION_FIELDS


class Database():
    def __init__(self):
        """Class for connection to MongoDatabase"""
        self.db = self.getConnection()  #get connection to DB
        self.simulation_numbers = self.db['simulation_numbers']  #table simulation_numbers
        self.simulations = self.db['simulations']                #table simulations
        self.iterations = self.db['iterations']                  #table iterations
        self.weater_data = self.db['weater_data']                #table weather data
        self.electricity_prices = self.db['electricity_prices']  #table electrictity prices
        self.addIndexes()  # indexes for speed

    def getConnection(self):
        """get connection to db"""
        try:
            connection = pymongo.Connection()  #try to connect
        except pymongo.errors.ConnectionFailure:
            raise ValueError("Please run MONGO SERVER")

        db = connection['MirrDatabase']
        return db

    def addIndexes(self):
        """add indexed to database"""
        #self.iterations.ensure_index('simulation', background=True )
        self.iterations.ensure_index([("country", pymongo.ASCENDING), ("simulation", pymongo.ASCENDING), ("iteration", pymongo.ASCENDING)], background=True)  #add simulation and iteration fields to index
        self.simulations.ensure_index("simulation", background=True)

    def deleteSimulation(self, simulation_no ):
        """Deletes selected simulation with @simulation_no"""
        self.simulations.remove({"simulation": simulation_no})  #removes data with simulation no from table with simulations
        self.iterations.remove({"simulation": simulation_no})  #removes data with simulation no from table with iterations
        print "Succesfully deleted simulation %s" % simulation_no
        if simulation_no == self.getLastSimulationNo():
            self.simulation_numbers.update({'_id': 'seq'}, {'$inc': {'seq': -1}}, upsert=True)  #changes last simulation no if we deleted last simulation

    def insertSimulation(self, record):
        """Safe inserts simulation line to DB"""
        self.simulations.insert(record, safe=True)

    def insertIteration(self,  line):
        """Safe inserts iterations line to DB"""
        self.iterations.insert(line, safe=True)

    def getLastSimulationNo(self):
        """Get last simulation number"""
        return self.simulation_numbers.find_one('seq')['seq']

    def getIterationsNumber(self, simulation_no):
        """return  number of iterations of current @simulation_no"""
        field = 'iterations_number'
        return self.getSimulationField(simulation_no, field)

    def getSimulationField(self, simulation_no, field):
        """return  1 field from db collection simulations limited by @simulation_no"""
        return self.simulations.find_one({'simulation': simulation_no}, {field: 1}).get(field, "no-result or error")

    def getIterationField(self, simulation_no, iteration_no, field):
        """return  1 field from db collection simulations limited by @simulation_no and @iteration_no"""
        query = {'simulation': simulation_no, 'iteration': iteration_no}
        data = self.iterations.find_one(query, {field: 1})
        if data is None:
            print '-'*80
            raise ValueError('No data for query %s' % query)
        else:
            return data.get(field, "no-result or error")

    def getReportHeader(self,simulation_no, iteration_no, yearly=False ):
        """return  report header - list of dates """
        return self.getIterationField(simulation_no, iteration_no, addYearlyPrefix('report_header', yearly))

    def getNextSimulationNo(self):
        """Get next simulation number and reserves it in database
        """
        if not self.simulation_numbers.find_one('seq'):
            print '*'*80
            print "THIS IS FIRST SIMULATION IN DATABASE"
            print '*'*80
            self.simulation_numbers.update({'_id': 'seq'}, {'$set': {'seq': 0}}, upsert=True)
        else:
            self.simulation_numbers.update({'_id': 'seq'}, {'$inc': {'seq': 1}}, upsert=True)
        return self.getLastSimulationNo()

    def formatRequest(self,  fields, not_changing_fields, yearly):
        """formats request to database Mongo, returns dicts with select and get values"""
        select_by = {}
        get_values = {'_id': False}

        for field in fields:
            if not field:
                continue
            if field not in not_changing_fields:
                field = addYearlyPrefix(field, yearly)
            select_by[field] = {'$exists': True }
            get_values[field] = True
        return select_by, get_values

    def getResultsFindLimitSimulation(self, fields, select_by, get_values, yearly, convert_to=None, not_changing_fields=[],
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
                    field_name = addYearlyPrefix(field_name, yearly)
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
            return {}

    def getSimulationCountry(self, simulation_no, print_result=False):
        s = self.simulations.find_one({'simulation': simulation_no}, {'_id': False, 'country': True})
        country = str(s.get('country', 'Country unknown'))
        if print_result:
            print "Simulation %s with country %r" % (simulation_no, country)
        return country

    def getSimulationValuesFromDB(self,  simulation_no, fields):
        """Gets data from collection 'simulations'
        """
        select_by, get_values = self.formatRequest(fields, [], False)
        select_by['simulation'] = simulation_no

        results = self.getResultsFindLimitSimulation(fields, select_by, get_values,
                                               yearly=False, collection='simulations')
        return  results

    def getIterationValuesFromDb(self, simulation_no, fields, yearly,
            not_changing_fields=[], iteration_no=None, one_result=False, country=None):
        """Gets from DB and shows @fields from LAST @number of simulations
        if iteration_no is not None, also filters by iteration no
        - using not_changing_fields with out prefix and
        - selected by list of @fields, any type - example ['irr_owners', 'irr_project', 'main_configs.lifetime']
        - using yearly suffix

        - and limited to @number
        - SORTED in BACK order
        """
        fields = not_changing_fields + fields
        select_by, get_values = self.formatRequest(fields, not_changing_fields, yearly)
        select_by['simulation'] = simulation_no
        if iteration_no:
            select_by['iteration'] = iteration_no
            one_result = True

        results = self.getResultsFindLimitSimulation(fields, select_by, get_values, yearly, not_changing_fields=not_changing_fields, one_result=one_result)
        if not results:
            raise ValueError('No results for simulation %r , country %r , iteration %s' %
                             (simulation_no, country, iteration_no))

        return results

    def getCorrelationValues(self, main_field, simulation_no, yearly=False):
        """get correlation of main_field with CORRELLATION_FIELDS"""

        fields = CORRELLATION_FIELDS.values()
        results = self.getIterationValuesFromDb(simulation_no, fields, yearly, not_changing_fields=[main_field])  #load iteration values from DB
        if not results:
            print('No data in Database for simulation %s' % simulation_no)
            return None

        main_list_values = results.pop(main_field)  #get main field results
        number_values_used = len(main_list_values)  #get number of main field results

        correllation_dict = {}
        for param, v in results.items():
            v1 = v[:]; v1[0] += 0.00001  #add too small to have some small correllation in case the same values
            cor = corrcoef([main_list_values, v1] )[0][1]  #calculation of correlation
            rounded_value = round(cor, 3)  #rounding
            correllation_dict[param] = rounded_value  #filling correllation dict

        return correllation_dict, number_values_used

    def updateSimulationComment(self, simulation_no, comment):
        """Updates comment in simulation"""
        self.simulations.update({'simulation': simulation_no,}, {"$set":{'comment': comment}}, multi=True, safe=True)
        print "Updated comment for simulation %s : %s" % (simulation_no, comment)

    def printLastSimulationsLog(self, last=10):
        """prints @last simulations data from database """
        last_simulation_no = self.getLastSimulationNo()  #get last simulation_no
        min_s = last_simulation_no - last + 1
        max_s = last_simulation_no  #range of simulation numbers

        group_by = {
                     "_id" : "$simulation",
                     "iterations_number": {'$last':"$iterations_number"},
                     "date": {'$last': "$date"},
                     "comment" : {'$last': "$comment"},
                     "country" : {'$last': "$country"},
                     }

        project = {
                  '_id': '$simulation',
                  'simulation': '$simulation',
                  "comment":True,
                  "country":True,
                  "len": {"$sum": "$simulation.iterations"},
                    }

        pipeline = [
            {'$match': {'simulation': {'$lte': max_s, '$gte': min_s,}} },
            {"$group" : group_by},
            {'$sort': {'_id': 1},},
        ]

        results = self.simulations.aggregate(pipeline)['result']
        for r in results:
            print u"%s - Simulation %s date %s - iterations %s - '%s'" % (
                r["country"],
                r["_id"],
                r["date"],
                r["iterations_number"],
                r['comment'])

    def cleanPreviousWeatherData(self, country):
        """removing previos weather simulations from db"""
        self.weater_data.remove({"country": country})

    def cleanPreviousElectricityPriceData(self, country):
        """removing previos electricity price simulations from db"""
        self.electricity_prices.remove({"country": country})

    def writeWeatherData(self, data):
        """Writes weather data
        data LIST looks like this:
                    [
                    {"simulation_no":"1", "data": {01.01.2001: (ins,temp), 02.01.2001: (ins,temp) ... 31.12.2035: (ins,temp) },
                    {"simulation_no":"2", "data": {01.01.2001: (ins,temp), 02.01.2001: (ins,temp) ... 31.12.2035: (ins,temp) },
                    {"simulation_no":"100", "data": {01.01.2001: (ins,temp), 02.01.2001: (ins,temp) ... 31.12.2035: (ins,temp) },
                    ]
        """
        self.weater_data.insert(data, safe=True)

    def getWeatherData(self, simulation_no, country):
        """return  weather data with defined @simulation_no"""
        result = self.weater_data.find_one({"simulation_no": simulation_no, "country": country}, {"_id": False})
        if result:
            return convertDictDates(result['data'])
        else:
            raise ValueError("No weather data for %r with simulation_no %s" % (country, simulation_no))

    def writeElectricityPrices(self, data):
        """write electricity prices simulation to db"""
        self.electricity_prices.insert(data, safe=True)

    def getElectricityPrices(self, simulation_no, country):
        """return  electricity prices data with defined @simulation_no or list of simulations_no"""
        if isinstance(simulation_no, int):
            result = self.electricity_prices.find_one({"country": country, "simulation_no": simulation_no}, {"_id": False})
            if result:
                result = convertDictDates(result['data'])
        elif isinstance(simulation_no, list):
            #it simulation no is list - get all electricity prices, indicated in list
            result = self.electricity_prices.find({"country": country, 'simulation_no': {"$in": simulation_no}}, {"_id": False, 'data': True})
            if result:
                result = [convertDictDates(r['data']) for r in result]
        else:
            raise ValueError('Incorrect format simulation_no: ' + simulation_no)

        if not result:
            raise ValueError('No data for Electricity prices for %r with simulation_no: %s' %(country, simulation_no))

        return result

