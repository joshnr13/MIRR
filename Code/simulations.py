import os
import datetime
import pylab
import csv

from _mirr import Mirr
from annex import get_only_digits,  convert_value, convert2excel, uniquify_filename, transponse_csv, invert_dict
from collections import OrderedDict
from database import Database
from config_readers import MainConfig
from report_output import ReportOutput
from constants import report_directory, CORRELLATION_FIELDS, CORRELLATION_IRR_FIELD, IRR
from numbers import Number

from numpy import corrcoef, around, isnan
from pylab import *
from itertools import izip_longest

class Simulation():

    def __init__(self, comment=''):
        self.db =  Database()
        self.simulation_no = self.get_next_simulation_no()
        self.comment = comment

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
        self.simulation_date = datetime.datetime.now().date()

    def db_insert_results(self):
        """Inserts iteration @iteration number to db"""
        self.db.insert(self.line)

    def convert_results(self):
        """Processing results before inserting to DB"""
        self.line = convert_value(self.prepared_line)

    def prepare_results(self, iteration, iteration_number):
        obj = self.r
        line = dict()

        line["simulation"] = self.simulation_no
        line["iteration"] = iteration
        line["iteration_number"] = iteration_number
        line["date"] = self.simulation_date
        line["comment"] = self.comment

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

        self.prepared_line = line

    def run_simulation(self,  iterations_number):
        """Run multiple simulations"""
        print "%s - runing simulation %s with %s iterations\n" % ( datetime.datetime.now().date(), self.simulation_no, iterations_number)
        self.irrs = []
        for i in range(iterations_number):
            print "\tRunning iteration %s of %s" % (i + 1, iterations_number)
            self.run_one_iteration(i+1, iterations_number)

    def get_irrs(self):
        """return  filtered irrs"""
        good_irrs = []
        for irr in self.irrs:
            if irr is not None:
                if irr is not isnan(irr):
                    good_irrs.append(irr)
        return good_irrs

    def add_result_irr(self):
        self.irrs.append(getattr(self.o.r, IRR))

    def run_one_iteration(self, iteration_no, total_iteration_number):
        """runs 1 iteration, prepares new data and saves it to db"""
        self.prepare_data()
        self.prepare_results(iteration_no, total_iteration_number)
        self.convert_results()
        self.db_insert_results()
        self.add_result_irr()

def run_all_simulations(iterations_number, comment):
    """Runs multiple iterations @iterations_number with @comment
    return  IRR values"""

    s = Simulation(comment=comment)
    s.run_simulation(iterations_number)
    return s.get_irrs(), s.simulation_no

def show_save_irr_distribution(field, simulation_number, yearly):
    irr_values = Database().get_simulations_values_from_db(simulation_id=simulation_number, fields=[field], yearly=yearly)
    irr_values = filter(lambda x :isinstance(x, Number), irr_values[field])

    if irr_values:
        show_irr_charts(irr_values, field, simulation_number)
        save_irr_values(irr_values, '')
    else :
        print "All IRR values was Nan (can't be calculated, please check FCF , because IRR cannot be negative)"

def show_irr_charts(values, field, simulation_no):
    """Shows irr distribution and charts , field used for title"""


    fig= pylab.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)  # share ax1's xaxis

    # Plot
    ax1.hist(values, bins=7)
    ax2.plot(range(1, len(values)+1), values, 'o')

    title_format = "Simulation %s. {0} of %s based on %s values" %(simulation_no, field, len(values))
    ax1.set_title(title_format.format("Histogram"))
    ax2.set_title(title_format.format("Chart"))
    pylab.show()

def save_irr_values(values, simulation_no):
    """Saves IRR values to excel file"""
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "%s_%s.%s" % (cur_date, 'irr_values', 'csv')
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquify_filename(report_full_name)
    numbers = ["Iteration number"] + list(range(1, len(values)+1 ))
    simulation_info = ["Simulation number"] + [simulation_no]

    with open(output_filename,'ab') as f:
        values.insert(0, "IRR_values")
        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)
        w.writerow(numbers)
        w.writerow(values)

    #transponse_csv(output_filename)
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

def plot_correlation_tornado(field_dic, simulation_id, yearly=False):
    """Plot tornado chart with correlation of field and other stochastic variables"""

    values = []
    field_values = {}
    main_field_name = field_dic.keys()[0]
    main_field_db_name = field_dic.values()[0]

    results = Database().get_correlation_values(main_field_db_name, simulation_id, yearly)

    if not results:
        return  None
    else:
        rounded_values_dict, number_values_used = results

    if number_values_used  ==  0:
        print "No needed values in Database. Please run simulations before!"
        return
    else:
        print ("Corellation using simulation %s with %s values from DB" % (simulation_id, number_values_used))

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
    title('Simulation %s. Correlation between %s and stochastic values, based on %s values' %(simulation_id, main_field_name, number_values_used))
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

def irr_scatter_charts(simulation_id, yearly=False):
    """
    figures : <title, figure> dictionary
    ncols : number of columns of subplots wanted in the display
    nrows : number of rows of subplots wanted in the figure
    """
    cols = 3
    rows = 2
    main = CORRELLATION_IRR_FIELD.values()[0]
    figures = Database().get_simulations_values_from_db(simulation_id, [main]+CORRELLATION_FIELDS.values(), yearly)
    if not figures:
            print ValueError('No data in Database for simulation %s' %simulation_id)
            return None

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
        else:
            obj.set_axis_off()

    title = "Simulation %s. Scatter charts" % simulation_id
    fig = pylab.gcf()
    fig.suptitle(title, fontsize=14)

    pylab.show()

def get_pos_no(value, sorted_list, used):
    for i, v in enumerate(sorted_list):
        if v == value and i not in used:
            used.append(i)
            return i

def plot_charts(simulation_id, yearly=False):

    fields = ['revenue', 'cost', 'ebitda', 'deprication']
    results = Database().get_simulations_values_from_db(simulation_id, fields, yearly, convert_to=float)

    revenue, cost, ebitda, deprication =  results.values()
    last_revenue, last_cost, last_ebitda, last_deprication =  revenue[-1][1:], cost[-1][1:], ebitda[-1][1:], deprication[-1][1:]

    pylab.plot(last_revenue, label='REVENUE')
    pylab.plot(last_cost, label='COST')
    pylab.plot(last_ebitda, label='EBITDA')
    pylab.plot(last_deprication, label='deprication')
    #pylab.plot(net_earning, label='net_earning')

    pylab.xlabel("months")
    pylab.ylabel("EUROs")
    pylab.legend()
    pylab.grid(True, which="both",ls="-")
    pylab.axhline()
    pylab.axvline()

    title = 'Simulation %s. ' % simulation_id
    if yearly:
        title += 'Yearly data'
    else :
        title += "Monthly data"
    pylab.title(title)
    pylab.show()


if __name__ == '__main__':
    #run_all_iterations()
    #plot_correlation_tornado()
    #irr_scatter_charts(100)
    plot_charts(20)
    #test_100_iters()
    #irr_scatter_charts()
    #s = Simulation()
    #s.run_simulations(10)


