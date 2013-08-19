import sys
import datetime
import csv

from _mirr import Mirr
from annex import convertValue
from collections import defaultdict
from database import Database
from report_output import ReportOutput
from rm import caclIrrsStatisctics
from constants import IRR_REPORT_FIELD, IRR_REPORT_FIELD2

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
        self.line = convertValue(self.prepared_line)

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

        self.calc_irr_statistics()
        self.add_irr_results_to_simulation()
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

    def add_irr_results_to_simulation(self):
        """Adding irr results to dict with simulation data"""
        self.simulation_record['irr_stats'] = self.irr_stats

    def calc_irr_statistics(self):
        """    for each simulation batch calculate, display and save the standard deviation of IRR (both of owners and project - separately)
        - skweness : http://en.wikipedia.org/wiki/Skewness
        - kurtosis: http://en.wikipedia.org/wiki/Kurtosis
        """
        irr_values = [self.irrs0, self.irrs1]
        fields = [IRR_REPORT_FIELD, IRR_REPORT_FIELD2]
        self.irr_stats =  caclIrrsStatisctics(fields, irr_values)


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

def run_save_simulation(iterations_no, comment):
    """
    1) Runs multiple iterations @iterations_number with @comment
    2) Shows charts
    3) Save results
    return  simulation_no
    """
    s = Simulation(comment=comment)
    s.run_simulation(iterations_no)
    return  s.get_simulation_no()


