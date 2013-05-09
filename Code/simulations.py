import datetime
from _mirr import Mirr
from annex import get_only_digits, convert_value
from collections import OrderedDict
from database import get_connection

class Simulations():

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

        self.main_configs = self.config.getConfigValues()
        self.ecm_configs = self.ecm.getConfigValues()
        self.tm_configs = self.tm.getConfigValues()
        self.sm_configs = self.sm.getConfigValues()
        self.em_configs = self.em.getConfigValues()

        self.inputs = self.em.getInputs()

    def db_insert_results(self):
        """Prepares and in"""
        self.collection.insert(self.line, safe=True)
        print "Inserted new iteration %s" %self.iteration_no

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
        #line["ecm_configs"] = self.ecm_configs
        #line["tm_configs"] = self.tm_configs
        #line["sm_configs"] = self.sm_configs
        #line["em_configs"] = self.em_configs

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


        return line

def run_one_iteration():
    d = Simulations()
    d.prepare_data()
    d.get_next_iteration()
    d.process_results()
    d.db_insert_results()

if __name__ == '__main__':
    run_one_iteration()
