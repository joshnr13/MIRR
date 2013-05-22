import os
import datetime
import pylab
import csv

from _mirr import Mirr
from annex import get_only_digits,  convert_value, convert2excel, uniquify_filename, transponse_csv, invert_dict
from collections import OrderedDict
from database import get_connection, get_values_from_db, get_rowvalue_from_db
from config_readers import MainConfig
from report_output import ReportOutput
from constants import report_directory, CORRELLATION_FIELDS, CORRELLATION_IRR_FIELD
from numpy import corrcoef, around, isnan
from pylab import *
from itertools import izip_longest

class Simulation():

    def __init__(self, connect=True):

        if connect:
            db =  get_connection()
            self.collection = db['collection']
            self.iterations = db['iteration']

    def get_next_iteration(self):
        """Get next iteration number

        TODO! Move it to database module !!!!!!!!!!!!!!!!!!
        TODO! Make database module as class !!!!!!!!!!!!!!!!!!!!!

        """
        self.iterations.update({'_id':'seq'}, {'$inc':{'seq':1}}, upsert=True)
        self.iteration_no = self.iterations.find_one()['seq']

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

        print
        #self.inputs = self.em.getInputs()

    def db_insert_results(self):
        """Prepares and in"""
        self.collection.insert(self.line, safe=True)
        print "Inserting new iteration %s" %self.iteration_no

    def process_results(self):
        """Processing results before inserting to DB"""
        line = self.prepare_results()
        line = convert_value(line)
        self.line = line

    def prepare_results(self):
        obj = self.r
        line = dict()

        line["hash_iteration"] = self.iteration_no
        line["date"] = datetime.datetime.now()

        line["main_configs"] = self.main_configs
        line["ecm_configs"] = self.ecm_configs
        line["tm_configs"] = self.tm_configs
        line["sm_configs"] = self.sm_configs
        line["em_configs"] = self.em_configs

        #line["inputs"] = self.inputs

        line["insolations"] = self.em.generatePrimaryEnergyAvaialbilityLifetime()
        #line["electricity_production"] = self.tm.electricity_production

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
        line["retained_earning"] = obj.retained_earning.values()
        line["unallocated_earning"] = obj.unallocated_earning.values()
        line["retained_earning"] = obj.retained_earning.values()
        line["financial_operating_obligation"] = obj.financial_operating_obligation.values()
        line["long_term_loan"] = obj.long_term_loan.values()
        line["short_term_loan"] = obj.short_term_loan.values()
        line["long_term_operating_liability"] = obj.long_term_operating_liability.values()
        line["short_term_debt_suppliers"] = obj.short_term_debt_suppliers.values()
        line["liability"] = obj.liability.values()
        line["equity"] = obj.equity.values()
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
        line["retained_earning_y"] = obj.retained_earning_y.values()
        line["unallocated_earning_y"] = obj.unallocated_earning_y.values()
        line["retained_earning_y"] = obj.retained_earning_y.values()
        line["financial_operating_obligation_y"] = obj.financial_operating_obligation_y.values()
        line["long_term_loan_y"] = obj.long_term_loan_y.values()
        line["short_term_loan_y"] = obj.short_term_loan_y.values()
        line["long_term_operating_liability_y"] = obj.long_term_operating_liability_y.values()
        line["short_term_debt_suppliers_y"] = obj.short_term_debt_suppliers_y.values()
        line["liability_y"] = obj.liability_y.values()
        line["equity_y"] = obj.equity_y.values()
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


        return line




def run_one_iteration(insert=True):
    d = Simulation(connect=insert)
    d.prepare_data()
    if insert:
        d.get_next_iteration()
        d.process_results()
    if insert:
        d.db_insert_results()

    return d.o  #report_output module

def run_all_iterations(simulation_number=None):
    """Runs multiple simulations , saves report of last iteration
    plots histogram or IRR distribution

    return  IRR values"""
    irrs = []
    if simulation_number is  None:
        simulation_number = MainConfig().getSimulationNumber()

    print "Runing %s number of simulations" % simulation_number
    for i in range(simulation_number):
        last_report = run_one_iteration()
        irrs.append(last_report.r.irr_owners)

    #last_report.prepare_report_IS_BS_CF_IRR(excel=True, yearly=False)

    good_irrs = []
    for irr in irrs:
        if irr is not None:
            if irr is not isnan(irr):
                good_irrs.append(irr)

    return good_irrs

def show_irr_charts(values):
    """Shows irr distribution and charts , field used for title"""
    field = 'irr_owners'
    title = " of %s using last %s values" %(field, len(values))

    fig= pylab.figure()

    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)  # share ax1's xaxis

    # Plot
    ax1.hist(values, bins=7)
    ax2.plot(range(1, len(values)+1), values, 'o')

    ax1.set_title("Histogram " + title)
    ax2.set_title("Chart " + title)
    pylab.show()


def save_irr_values(values):
    """Saves IRR values to excel file"""
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "%s_%s.%s" % (cur_date, 'irr_values', 'csv')
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquify_filename(report_full_name)
    numbers = ["Iteration number"] + list(range(1, len(values)+1 ))

    with open(output_filename,'ab') as f:
        values.insert(0, "IRR_values")
        w = csv.writer(f, delimiter=';')
        w.writerow(numbers)
        w.writerow(values)

    transponse_csv(output_filename)
    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquify_filename(xls_output_filename)

    convert2excel(source=output_filename, output=xls_output_filename)
    print "CSV Report outputed to file %s" % (xls_output_filename)


def get_limit_values(x, y):
    min_irr = min(x)
    max_irr = max(x)
    irr_range = max_irr - min_irr

    min_val = min(y)
    max_val = max(y)
    val_range = max_val - min_irr

    delta_x = 0.05
    delta_y = 0.05

    min_irr = min_irr - delta_x * irr_range
    max_irr = max_irr + delta_x * irr_range

    min_val = min_val - delta_y * val_range
    max_val = max_val + delta_y * val_range


    return ((min_irr, max_irr), (min_val, max_val))


def get_correlation_values(main_field, number=30, yearly=False):
    """get correlation of main_field with CORRELLATION_FIELDS"""

    fields = [main_field] + CORRELLATION_FIELDS.values()
    results = get_values_from_db(number, fields, yearly)
    #print("results = %s" %(results,))  #debug-info-print

    main_list_values = results.pop(main_field)
    number_values_used = len(main_list_values)

    correllation_dict = {}
    for k, v in results.items():
        cor = corrcoef([main_list_values, v] )[0][1]
        rounded_value = round(cor, 3)
        correllation_dict[k] = rounded_value

    return  correllation_dict, number_values_used


def plot_correlation_tornado(field_dic, number=30, yearly=False):
    """Plot tornado chart with correlation of field and other stochastic variables"""

    values = []
    field_values = {}
    main_field_name = field_dic.keys()[0]
    main_field_db_name = field_dic.values()[0]

    rounded_values_dict, number_values_used = get_correlation_values(main_field_db_name, number, yearly)

    if number_values_used  ==  0:
        print "No needed values in Database. Please run simulations before!"
        return
    else:
        print ("Corellation using last %s values from DB" % number_values_used)

    for i, (field_short_name, main_field_db_name) in enumerate(CORRELLATION_FIELDS.items()):
        value = rounded_values_dict[main_field_db_name]
        print "Correllation between %s and %s = %s" % (main_field_name, field_short_name, value)
        if isnan(value):
            value = 0
        values.append(value)
        field_values[field_short_name] = value

    fig = figure(1)
    ax = fig.add_subplot(111)

    v1 = list(filter(lambda x : x>0, values))
    v2 = list(filter(lambda x : x<=0, values))
    v1.sort(key=abs, reverse=True)
    v2.sort(key=abs, reverse=True)

    sorted_list = sorted(values, key=abs)
    used = []
    pos1 = [get_pos_no(value, sorted_list, used) for value in v1]
    pos2 = [get_pos_no(value, sorted_list, used) for value in v2]

    ax.barh(pos1,v1, align='center', color='g')
    ax.barh(pos2,v2, align='center', color='r')

    y_names = sorted(field_values.items(), key=lambda x: abs(x[1]), reverse=True)
    y_names = [g[0] for g in y_names]

    yticks(list(reversed(range(len(y_names)))), y_names)
    xlabel('correlation coefficient')
    title('Correlation between %s and stochastic values, using %s values' %(main_field_name, number_values_used))
    grid(True)
    xlim(-1,1)
    ylim(-0.5, len(field_values)-0.5)
    #setp(ax.get_yticklabels(), fontsize=12,)

    fig.subplots_adjust(left=0.35)

    for (i,j) in zip(v1,pos1):
        value = i
        rel_position = len(str(value))
        annotate(value, xy=(i,j), color='green', weight='bold', size=12,xytext=(rel_position, 00), textcoords='offset points',)

    for (i,j) in zip(v2,pos2):
        value = i
        rel_position = -len(str(value)) * 8
        annotate(value, xy=(i,j), color='red', weight='bold', size=12,xytext=(rel_position, 00), textcoords='offset points',)

    show()


def irr_scatter_charts(number=10, yearly=False):
    #title = " of %s using last %s values" %(field, len(values))
    """
    figures : <title, figure> dictionary
    ncols : number of columns of subplots wanted in the display
    nrows : number of rows of subplots wanted in the figure
    """
    cols = 3
    rows = 2
    main = CORRELLATION_IRR_FIELD.values()[0]
    figures = get_values_from_db(number, [main]+CORRELLATION_FIELDS.values(), yearly)
    #print("figures = %s" %(figures,))  #debug-info-print figures
    irrs = figures.pop(main)
    titles = invert_dict(CORRELLATION_FIELDS)

    fig, axeslist = pylab.subplots(ncols=cols, nrows=rows)
    left,bottom,width,height = 0.2,0.1,0.6,0.6 # margins as % of canvas size

    for ind,title in izip_longest(range(cols*rows), figures):
        obj = axeslist.ravel()[ind]
        if title is not None:
            values = figures[title]
            plot_title = titles[title]

            axes = pylab.Axes(obj.figure, [1,1,1,1]) # [left, bottom, width, height] where each value is between 0 and 1

            obj.plot(irrs, values, 'o')
            obj.set_title(plot_title)
            obj.set_xlabel(main)

            limx, limy = get_limit_values(irrs, values)

            obj.set_xlim(limx)
            obj.set_ylim(limy)

            obj.figure.add_axes([12,12,12,12], frameon=False)
            #obj.add_axes(fig,[left,bottom,width,height])
        else:
            obj.set_axis_off()

    pylab.show()



def get_pos_no(value, sorted_list, used):
    for i, v in enumerate(sorted_list):
        if v == value and i not in used:
            used.append(i)
            return i




def plot_charts(yearly=False):

    fields = ['revenue', 'cost', 'ebitda', 'deprication']
    #results = get_values_from_db(1, fields, yearly)

    #revenue = get_only_digits2(results['revenue'][0])
    #cost = get_only_digits2(results['cost'][0])
    #ebitda = get_only_digits2(results['ebitda'][0])
    #deprication = get_only_digits2(results['deprication'][0])
    revenue, cost, ebitda, deprication = get_rowvalue_from_db(fields, yearly)

    pylab.plot(revenue, label='REVENUE')
    pylab.plot(cost, label='COST')
    pylab.plot(ebitda, label='EBITDA')
    pylab.plot(deprication, label='deprication')
    #pylab.plot(net_earning, label='net_earning')

    pylab.xlabel("months")
    pylab.ylabel("EUROs")
    pylab.legend()
    pylab.grid(True, which="both",ls="-")
    pylab.axhline()
    pylab.axvline()
    if yearly:
        title = 'Yearly data'
    else :
        title = "Monthly data"
    pylab.title(title)
    pylab.show()


def test_100_iters():
    for i in range(100):
        run_one_iteration(insert=False)


if __name__ == '__main__':
    #run_one_iteration()
    #run_all_iterations()
    #plot_correlation_tornado()
    #irr_scatter_charts(100)
    #plot_charts()
    test_100_iters()
    #irr_scatter_charts()


