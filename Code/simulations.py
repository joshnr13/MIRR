import os
import datetime
import pylab
import csv

from _mirr import Mirr
from annex import get_only_digits, convert_value, convert2excel, uniquify_filename, transponse_csv
from collections import OrderedDict
from database import get_connection, get_values_from_db
from config_readers import MainConfig
from report_output import ReportOutput
from math import isnan
from constants import report_directory

class Simulation():

    def __init__(self):
        db =  get_connection()
        self.collection = db['collection']
        self.iterations = db['iteration']

    def get_next_iteration(self):
        """Get next iteration number"""
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

        return line




def run_one_iteration():
    d = Simulation()
    d.prepare_data()
    d.get_next_iteration()
    d.process_results()
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

    last_report.prepare_report_IS_BS_CF_IRR(excel=True, yearly=False)
    good_irrs = [irr for irr in irrs if not isnan(irr)]

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


def calc_correllation():
    """
    - permit_procurement_duration+
    - construction_duration+
    - subsidy duration+
    - kWh_subsidy+
    #line["ecm_configs"] = self.ecm_configs
    #line["tm_configs"] = self.tm_configs
    #line["em_configs"] = self.em_configs
    """
    fields = [
    "main_configs.real_permit_procurement_duration",
    "main_configs.real_construction_duration",
    "sm_configs.kWh_subsidy",
    "sm_configs.delay",
    ]
    fields = ["sm_configs"]
    print get_values_from_db(number=10, fields=fields, yearly=False)
    """
        >>> from numpy import *
    >>> a = array([1,2,3,4,6,7,8,9])
    >>> b = array([2,4,6,8,10,12,13,15])
    >>> c = array([-1,-2,-2,-3,-4,-6,-7,-8])
    >>> corrcoef([a,b,c])
    array([[ 1.        ,  0.99535001, -0.9805214 ],
           [ 0.99535001,  1.        , -0.97172394],
           [-0.9805214 , -0.97172394,  1.        ]])

    Here we can get the correlation coefficient of a,b (0.995), a,c (-0.981) and b,c (-0.972) at once. The two-data-set case is just a special case of N-data-set class. And probably it's better to keep the same return type. Since the "one value" can be obtained simply with

    >>> corrcoef(a,b)[1,0]
    0.99535001355530017
    """


if __name__ == '__main__':
    run_one_iteration()
    #run_all_iterations()
    #calc_correllation()


