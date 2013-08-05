import os, sys
import datetime
import pylab
import csv


from _mirr import Mirr
from annex import get_only_digits,  convert_value, convert2excel, uniquify_filename, transponse_csv, get_only_digits_list, calc_statistics, get_report_dates
from collections import OrderedDict, defaultdict
from database import Database
from config_readers import MainConfig, EmInputsReader, EnergyModuleConfigReader
from report_output import ReportOutput
from numbers import Number
from charts import show_irr_charts, plot_histograms
from constants import IRR_REPORT_FIELD, IRR_REPORT_FIELD2, report_directory, CORRELLATION_FIELDS, TESTMODE
from numpy.random import normal as gauss

db = Database()

class Simulation():

    def __init__(self, comment=''):
        self.db =  Database()
        self.comment = comment
        self.simulation_no = self.get_next_simulation_no()
        self.irrs0 = []
        self.irrs1 = []

    def get_simulation_no(self):
        return  self.simulation_no

    def get_next_simulation_no(self):
        return  self.db.get_next_simulation_no()

    def prepare_data(self):
        self.i = Mirr()
        self.config = self.i.getMainConfig()
        self.ecm = self.i.getEconomicModule()
        self.tm = self.i.getTechnologyModule()
        self.sm = self.i.getSubsideModule()
        self.em = self.i.getEnergyModule()
        self.r = self.i.getReportModule()
        self.o = self.i.getOutputModule()

        self.main_configs = self.config.getConfigsValues()
        self.ecm_configs = self.ecm.getConfigsValues()
        self.tm_configs = self.tm.getConfigsValues()
        self.sm_configs = self.sm.getConfigsValues()
        self.em_configs = self.em.getConfigsValues()

    def convert_results(self):
        """Processing results before inserting to DB"""
        self.line = convert_value(self.prepared_line)

    def prepare_iteration_results(self, iteration, iteration_number):
        obj = self.r
        line = dict()

        line["simulation"] = self.simulation_no
        line["iteration"] = iteration

        line["main_configs"] = self.main_configs
        line["ecm_configs"] = self.ecm_configs
        line["tm_configs"] = self.tm_configs
        line["sm_configs"] = self.sm_configs
        line["em_configs"] = self.em_configs

        #####################################

        line["revenue"] = obj.revenue.values()
        line["revenue_electricity"] = obj.revenue_electricity.values()
        line["revenue_subsides"] = obj.revenue_subsides.values()
        line["cost"] = obj.cost.values()
        line["operational_cost"] = obj.operational_cost.values()
        line["development_cost"] = obj.development_cost.values()
        line["ebitda"] = obj.ebitda.values()
        line["ebit"] = obj.ebit.values()
        line["ebt"] = obj.ebt.values()
        line["iterest_paid"] = obj.iterest_paid.values()
        line["deprication"] = obj.deprication.values()
        line["tax"] = obj.tax.values()
        line["net_earning"] = obj.net_earning.values()
        line["investment"] = obj.investment.values()
        line["fixed_asset"] = obj.fixed_asset.values()
        line["asset"] = obj.asset.values()
        line["inventory"] = obj.inventory.values()
        line["operating_receivable"] = obj.operating_receivable.values()
        line["short_term_investment"] = obj.short_term_investment.values()
        line["asset_bank_account"] = obj.asset_bank_account.values()
        line["paid_in_capital"] = obj.paid_in_capital.values()
        line["current_asset"] = obj.current_asset.values()
        line["unallocated_earning"] = obj.unallocated_earning.values()
        line["retained_earning"] = obj.retained_earning.values()
        line["financial_operating_obligation"] = obj.financial_operating_obligation.values()
        line["long_term_loan"] = obj.long_term_loan.values()
        line["short_term_loan"] = obj.short_term_loan.values()
        line["long_term_operating_liability"] = obj.long_term_operating_liability.values()
        line["short_term_debt_suppliers"] = obj.short_term_debt_suppliers.values()
        line["liability"] = obj.liability.values()
        line["equity"] = obj.equity.values()
        line["control"] = obj.control.values()
        line["report_header"] = obj.control.keys()

        ###############################
        line["revenue_y"] = obj.revenue_y.values()
        line["revenue_electricity_y"] = obj.revenue_electricity_y.values()
        line["revenue_subsides_y"] = obj.revenue_subsides_y.values()
        line["cost_y"] = obj.cost_y.values()
        line["operational_cost_y"] = obj.operational_cost_y.values()
        line["development_cost_y"] = obj.development_cost_y.values()
        line["ebitda_y"] = obj.ebitda_y.values()
        line["ebit_y"] = obj.ebit_y.values()
        line["ebt_y"] = obj.ebt_y.values()
        line["iterest_paid_y"] = obj.iterest_paid_y.values()
        line["deprication_y"] = obj.deprication_y.values()
        line["tax_y"] = obj.tax_y.values()
        line["net_earning_y"] = obj.net_earning_y.values()
        line["investment_y"] = obj.investment_y.values()
        line["fixed_asset_y"] = obj.fixed_asset_y.values()
        line["asset_y"] = obj.asset_y.values()
        line["inventory_y"] = obj.inventory_y.values()
        line["operating_receivable_y"] = obj.operating_receivable_y.values()
        line["short_term_investment_y"] = obj.short_term_investment_y.values()
        line["asset_bank_account_y"] = obj.asset_bank_account_y.values()
        line["paid_in_capital_y"] = obj.paid_in_capital_y.values()
        line["current_asset_y"] = obj.current_asset_y.values()
        line["unallocated_earning_y"] = obj.unallocated_earning_y.values()
        line["retained_earning_y"] = obj.retained_earning_y.values()
        line["financial_operating_obligation_y"] = obj.financial_operating_obligation_y.values()
        line["long_term_loan_y"] = obj.long_term_loan_y.values()
        line["short_term_loan_y"] = obj.short_term_loan_y.values()
        line["long_term_operating_liability_y"] = obj.long_term_operating_liability_y.values()
        line["short_term_debt_suppliers_y"] = obj.short_term_debt_suppliers_y.values()
        line["liability_y"] = obj.liability_y.values()
        line["equity_y"] = obj.equity_y.values()
        line["control_y"] = obj.control_y.values()
        line["report_header_y"] = obj.control_y.keys()

        ##################################
        line["fcf_project"] = obj.fcf_project.values()
        line["fcf_owners"] = obj.fcf_owners.values()
        line["fcf_project_y"] = obj.fcf_project_y.values()
        line["fcf_owners_y"] = obj.fcf_owners_y.values()

        line["irr_project"] = obj.irr_project
        line["irr_owners"] = obj.irr_owners
        line["irr_project_y"] = obj.irr_project_y
        line["irr_owners_y"] = obj.irr_owners_y

        line["npv_project"] = obj.npv_project
        line["npv_owners"] = obj.npv_owners
        line["npv_project_y"] = obj.npv_project_y
        line["npv_owners_y"] = obj.npv_owners_y

        line["wacc"] = obj.wacc
        line["wacc_y"] = obj.wacc

        #########################################
        line["project_days"] = self.ecm.electricity_prices.keys()

        line["equipment_description"] = self.tm.get_equipment_description()

        line["insolations_daily"] = self.em.get_insolations_lifetime().values()
        line["electricity_production_daily"] = self.ecm.electricity_production.values()


        line["sun_insolation"] = obj.sun_insolation.values()
        line["sun_insolation_y"] = obj.sun_insolation_y.values()

        line["electricity_production"] = obj.electricity_production.values()
        line["electricity_production_y"] = obj.electricity_production_y.values()

        line["electricity_prices"] = obj.electricity_prices.values()
        line["electricity_prices_y"] = obj.electricity_prices_y.values()

        line["pv_owners"] = obj.pv_owners.values()
        line["pv_project"] = obj.pv_project.values()

        line["pv_owners_y"] = obj.pv_owners_y.values()
        line["pv_project_y"] = obj.pv_project_y.values()

        self.prepared_line = line

    def run_simulation(self,  iterations_number):
        """Run multiple simulations"""

        self.init_simulation_record(iterations_number)
        for i in range(iterations_number):
            percent = (i + 1) * 100 / float(iterations_number)
            self.run_one_iteration(i+1, iterations_number)
            self.db.insert_iteration(self.line)
            sys.stdout.write("\r%d%%" %percent)    # or print >> sys.stdout, "\r%d%%" %i,
            sys.stdout.flush()
        print "\n"

        irr_stats = self.calc_irr_statistics()
        self.add_irr_results_to_simulation(irr_stats)
        self.db.insert_simulation(self.simulation_record)

    def init_simulation_record(self, iterations_number):
        print "%s - runing simulation %s with %s number of iterations\n" % ( datetime.datetime.now().date(), self.simulation_no, iterations_number)
        self.simulation_record = defaultdict(list)
        self.simulation_record["simulation"] = self.simulation_no
        self.simulation_record["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        self.simulation_record["comment"] = self.comment
        self.simulation_record["iterations_number"] = iterations_number

    def write_iteration_to_db(self):
        self.simulation_record['iterations'].append(self.line)

    def add_irr_results_to_simulation(self, irr_results):
        """Adding irr results to dict with simulation data"""
        self.simulation_record['irr_stats'] = irr_results

    def calc_irr_statistics(self):
        """    for each simulation batch calculate, display and save the standard deviation of IRR (both of owners and project - separately)
        - skweness : http://en.wikipedia.org/wiki/Skewness
        - kurtosis: http://en.wikipedia.org/wiki/Kurtosis
        """
        results = []
        for i, irr in enumerate([self.irrs0, self.irrs1]):
            result = {}
            digit_irr = self.get_filtered_irrs(irr)
            field = IRR_REPORT_FIELD if i == 0 else IRR_REPORT_FIELD2
            result['field'] = field
            result['digit_values'] = digit_irr
            result[field] = irr
            result.update(calc_statistics(digit_irr))
            results.append(result)

        return  results

    def get_filtered_irrs(self, obj):
        """return  filtered irrs"""
        return  get_only_digits_list(obj)

    def add_result_irrs(self):
        """Adds irr results to attrributes"""
        self.irrs0.append(getattr(self.o.r, IRR_REPORT_FIELD))
        self.irrs1.append(getattr(self.o.r, IRR_REPORT_FIELD2))

    def run_one_iteration(self, iteration_no, total_iteration_number):
        """runs 1 iteration, prepares new data and saves it to db"""
        #print "\tRunning iteration %s of %s" % (iteration_no, total_iteration_number)
        self.prepare_data()
        self.prepare_iteration_results(iteration_no, total_iteration_number)
        self.convert_results()
        self.add_result_irrs()

def print_equipment_db(simulation_no, iteration_no=1):
    return  db.get_iteration_field(simulation_no, iteration_no, 'equipment_description')

def run_save_simulation(iterations_no, comment):
    """
    1) Runs multiple iterations @iterations_number with @comment
    2) Shows charts
    3) Save results
    return  simulation_no
    """
    s = Simulation(comment=comment)
    s.run_simulation(iterations_no)
    #process_irr_values(s.calc_irr_statistics(), s.get_simulation_no())
    return  s.get_simulation_no()

def show_save_irr_distribution(simulation_no, yearly=False):
    """
    1 Gets from DB yearly values of irr
    2 Saves in xls report & Charts

    """
    field = 'irr_stats'
    irr_values_lst = db.get_simulation_values_from_db(simulation_no, [field])
    irr_values_lst = irr_values_lst[field][0]

    save_irr_values_xls(irr_values_lst, simulation_no, yearly)  #was irr_values[:]
    show_irr_charts(irr_values_lst, simulation_no, yearly) #was irr_values[:]
    print_irr_stats(irr_values_lst)

def print_irr_stats(irr_values_lst):
    """Prints statistics of irr values"""
    for dic in irr_values_lst:
        print "Statistics for %s" % dic.get('field', None)
        print "\tSt.deviation value %s" % dic.get('std', None)
        print "\tVariance value %s" % dic.get('variance', None)
        print "\tMin value %s" % dic.get('min', None)
        print "\tMax value %s" % dic.get('max', None)
        print "\tMedium value %s" % dic.get('median', None)
        print "\tMean value %s" % dic.get('mean', None)
        print "\tSkew value %s" % dic.get('skew', None)
        print "\tKurtosis value %s" % dic.get('kurtosis', None)

def save_irr_values_xls(irr_values_lst, simulation_no, yearly):
    """Saves IRR values to excel file
    @irr_values_lst - list  with 2 complicated dicts inside """

    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "{cur_date}_irr_values_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquify_filename(report_full_name)

    blank_row = [""]
    field1 = irr_values_lst[0]['field']
    field2 = irr_values_lst[1]['field']

    irr_values1 = [field1] + irr_values_lst[0][field1]
    irr_values2 = [field2] + irr_values_lst[1][field2]

    iterations = ["Iteration number"] + list(range(1, len(irr_values1)))
    simulation_info = ["Simulation number"] + [simulation_no]

    stat_params = ['min', 'max', 'median', 'mean', 'variance', 'std','skew', 'kurtosis']
    stat_fields = ['field'] + stat_params

    stat_info1 = [field1]
    stat_info2 = [field2]

    for key in stat_params:
        stat_info1.append(irr_values_lst[0][key])
        stat_info2.append(irr_values_lst[1][key])

    with open(output_filename,'ab') as f:

        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)
        w.writerow(blank_row)

        w.writerow(iterations)
        w.writerow(irr_values1)
        w.writerow(irr_values2)

        w.writerow(blank_row)
        w.writerow(stat_fields)
        w.writerow(stat_info1)
        w.writerow(stat_info2)

    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquify_filename(xls_output_filename)

    convert2excel(source=output_filename, output=xls_output_filename)
    print "CSV Report outputed to file %s" % (xls_output_filename)


def plotsave_stochastic_values_by_simulation(simulation_no, yearly=True):
    """"""
    fields = CORRELLATION_FIELDS.values()
    results = db.get_iteration_values_from_db(simulation_no, fields=[], yearly=yearly , not_changing_fields=fields)
    plot_histograms(results, simulation_no, yearly)
    save_stochastic_values_by_simulation(results, simulation_no)

def save_stochastic_values_by_simulation(dic_values, simulation_no):
    """Saves IRR values to excel file
    @irr_values_lst - list  with 2 complicated dicts inside """

    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "{cur_date}_stochastic_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquify_filename(report_full_name)
    rows_values = []
    rows_stats = []

    for name, values in dic_values.items():
        row = [name] + values
        rows_values.append(row)
        stats_dic = calc_statistics(values)
        stats = [name] + stats_dic.values()
        rows_stats.append(stats)


    blank_row = [""]

    iterations = ["Iteration number"] + list(range(1, len(values)+1))
    simulation_info = ["Simulation number"] + [simulation_no]
    stat_info = ["Statistics"] + stats_dic.keys()

    with open(output_filename,'ab') as f:

        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)
        w.writerow(blank_row)

        w.writerow(iterations)
        w.writerows(rows_values)

        w.writerow(blank_row)
        w.writerow(stat_info)
        w.writerows(rows_stats)

    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquify_filename(xls_output_filename)

    convert2excel(source=output_filename, output=xls_output_filename)
    print "Stochastic Report outputed to file %s" % (xls_output_filename)


class WeatherSimulations():
    def __init__(self, period, simulations_no):
        """
        inputs - class with inputs
        @period - list dates for simulation
        """
        config = EnergyModuleConfigReader()
        self.mean = config.mean
        self.stdev = config.stdev
        self.period = period
        self.simulations_no = simulations_no
        self.inputs = EmInputsReader()
        self.db = Database()

    def clend_prev_data(self):
        print "Cleaning previous data"
        self.db.clean_previous_weather_data()

    def simulate(self):
        self.clend_prev_data()
        for simulation_no in range(1, self.simulations_no+1):
            data = self.generate_one_simulation(simulation_no)
            self.write_weather_data(data)

    def generate_one_simulation(self, simulation_no):

        days_dict = OrderedDict()
        for date in self.period:
            insolation, temperature = self.generate_weather_data(date)
            date_str = date.strftime("%Y-%m-%d")
            days_dict[date_str] = (insolation, temperature)
        simulation_result = {"simulation_no": simulation_no, "data": days_dict}
        return  simulation_result

    def write_weather_data(self, data):
        self.db.write_weather_data(data)
        print 'Writing simulation %s' % data["simulation_no"]

    def generate_weather_data(self, date):
        """
        generates insolation and temperature for given_data
        - each time new random factor used
        return  2 values:  insolation, temperature
        """
        rnd_factor = self.getRandomFactor()
        insolation = self.getAvMonthInsolation(date) * rnd_factor
        temperature = self.getAvMonthTemperature(date) * rnd_factor

        return  insolation, temperature

    def getRandomFactor(self):
        """return random factor with normal distribution"""
        if not TESTMODE:
            return gauss(self.mean, self.stdev)
        else:
            return self.mean

    def getAvMonthInsolation(self, date):
        """Returns average daily insolation in given date"""
        month = date.month - 1
        av_insolation = self.inputs.getAvMonthInsolation_month(month)
        return av_insolation

    def getAvMonthTemperature(self, date):
        """Returns average daily temperature in given date"""
        month = date.month - 1
        av_temperature = self.inputs.getAvMonthTemperature_month(month)
        return av_temperature

    def generatePrimaryEnergyAvaialbility(self, date):
        """Parameters: start date
        based on monthly averages creates daily data
        """
        result = self.getAvMonthInsolation(date) * self.getRandomFactor()
        return result


if __name__ == '__main__':
    #run_all_iterations()
    #plot_correlation_tornado()
    #irr_scatter_charts(100)
    #plot_charts(20)
    #test_100_iters()
    #irr_scatter_charts()
    #s.run_simulations(10)

    #show_save_irr_distribution(2)
    #plotsave_stochastic_values_by_simulation(60)
    from annex import get_list_dates
    date_start = datetime.date(2001, 1, 1)
    date_end = datetime.date(2051, 1, 1)
    #period =get_report_dates(date_start, date_end)[0].values()
    period = get_list_dates(date_start, date_end)
    print 1
    s = WeatherSimulations(period, 100)
    #s.simulate()
    print s.db.get_weather_data(1)



