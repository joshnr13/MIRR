import sys
import datetime

from _mirr import Mirr
from annex import convertValue, setupPrintProgress
from collections import defaultdict
from config_readers import RiskModuleConfigReader, start_iteration
from database import Database
from rm import caclIrrsStatisctics
from constants import IRR_REPORT_FIELD, IRR_REPORT_FIELD2



class Simulation():
    """Class for preparing, runinning and saving simulations to Database"""
    def __init__(self, country, comment=''):
        """@comment - user inputed comment"""
        self.db =  Database()  #connection to Db
        self.comment = comment  #user comment for current simulation
        self.country = country #country which data will be used in simulation
        self.simulation_no = self.getNextSimulationNo()  #load last simulation no from db
        self.irrs0 = []  #for keeping irr values for each iteration
        self.irrs1 = []

    def getSimulationNo(self):
        """return  current simulation no"""
        return self.simulation_no

    def getNextSimulationNo(self):
        """return  next simulation no from db"""
        return self.db.getNextSimulationNo()

    def prepareLinks(self):
        """create short links to prepared modules"""
        self.config = self.i.getMainConfig()
        self.ecm = self.i.getEconomicModule()
        self.tm = self.i.getTechnologyModule()
        self.sm = self.i.getSubsideModule()
        self.em = self.i.getEnergyModule()
        self.r = self.i.getReportModule()
        self.o = self.i.getOutputModule()

        self.main_configs = self.config.getConfigsValues()  #module config values
        self.ecm_configs = self.ecm.getConfigsValues()  #module config values
        self.tm_configs = self.tm.getConfigsValues()  #module config values
        self.sm_configs = self.sm.getConfigsValues() #module config values
        self.em_configs = self.em.getConfigsValues() #module config values
        self.rm_configs = RiskModuleConfigReader(self.country).getConfigsValues() #module config values

    def convertResults(self):
        """Processing results before inserting to DB"""
        self.line = convertValue(self.prepared_line)

    def prepareIterationResults(self, iteration):
        """prepare each iteration (@iteration number) results before saving to database"""
        obj = self.r
        line = dict()  #main dict for holding results of one iteration

        line["simulation"] = self.simulation_no
        line["iteration"] = iteration

        line["main_configs"] = self.main_configs  #module config values
        line["ecm_configs"] = self.ecm_configs #module config values
        line["tm_configs"] = self.tm_configs #module config values
        line["sm_configs"] = self.sm_configs #module config values
        line["em_configs"] = self.em_configs #module config values

        #####################################

        line["revenue"] = obj.revenue.values()  #values of revenue
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
        line["fcf_project"] = obj.fcf_project.values()  #FCF values
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
        line["project_days"] = self.ecm.electricity_prices.keys()  #list of all project days

        line["equipment_description"] = self.tm.equipmentDescription()

        line["insolations_daily"] = self.em.getInsolationsLifetime().values()
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

    def runSimulation(self,  iterations_number):
        """Run Simulation with multiple @iterations_number """
        self.initSimulationRecord(iterations_number)  #Prepare atributes for saving simulation record
        self.runIterations(iterations_number)  #run all iterations with saving results
        self.addIrrStatsToSimulation()  #add IRR stats to simulation record for future speed access
        self.db.insertSimulation(self.simulation_record)  #insert simulation record

    def runIterations(self, iterations_number):
        """Run multiple @iterations_number """
        print_progress = setupPrintProgress(
            '%d%%', lambda x: (x + 1) * 100 / float(iterations_number))
        for i in range(iterations_number):
            start_iteration(i+1)  # set global param with number of iteration
            self.runOneIteration(i+1, iterations_number)  #main calculations
            self.db.insertIteration(self.line)  #saving to db each iteration result
            print_progress(i)  # printing percent to screen
        print "\n"

    def initSimulationRecord(self, iterations_number):
        """Prepare atributes for saving simulation records"""
        print "%s - runing simulation %s with %s number of iterations\n" % ( datetime.datetime.now().date(), self.simulation_no, iterations_number)
        self.simulation_record = defaultdict(list)  #attribute for holding basic info about simulation
        self.simulation_record["simulation"] = self.simulation_no
        self.simulation_record["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        self.simulation_record["comment"] = self.comment
        self.simulation_record["iterations_number"] = iterations_number  #number of iterations,
        self.simulation_record["country"] = self.country  #number of iterations,

    def addIrrStatsToSimulation(self):
        """Adding irr results to dict with simulation data"""
        """    for each simulation batch calculate, display and save the standard deviation of IRR (both of owners and project - separately)
        - skweness : http://en.wikipedia.org/wiki/Skewness
        - kurtosis: http://en.wikipedia.org/wiki/Kurtosis
        """
        fields = [IRR_REPORT_FIELD, IRR_REPORT_FIELD2]  #which field names will be used to calc stats
        riskFreeRate, benchmarkSharpeRatio = self.rm_configs['riskFreeRate'], self.rm_configs['riskFreeRate']
        self.simulation_record['irr_stats'] = caclIrrsStatisctics(fields, [self.irrs0, self.irrs1], riskFreeRate, benchmarkSharpeRatio )  #calculating and adding IRR stats to simulation record

    def runOneIteration(self, iteration_no, total_iteration_number):
        """runs 1 iteration, prepares new data and saves it to db"""
        self.prepareMirr()  #prepare Mirr module, which has links for all other modules
        self.prepareLinks()  #make short links to other modules
        self.prepareIterationResults(iteration_no)  #main func to prepare results in one dict
        self.convertResults()  #post process results before saving to db
        self.addIterationIrrs()  #add irr values to additional lists for future analis

    def prepareMirr(self):
        """prepare All modules for simulation"""
        self.i = Mirr(self.country)

    def addIterationIrrs(self):
        """Adds irr results to attrributes"""
        self.irrs0.append(getattr(self.r, IRR_REPORT_FIELD))
        self.irrs1.append(getattr(self.r, IRR_REPORT_FIELD2))

def runAndSaveSimulation(country, iterations_no, comment):
    """
    1) Runs multiple iterations @iterations_number with @comment
    2) Shows charts
    3) Save results
    return  simulation_no
    """
    s = Simulation(country, comment=comment)
    s.runSimulation(iterations_no)
    return s.getSimulationNo()


