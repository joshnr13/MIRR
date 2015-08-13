import sys
import datetime
import multiprocessing

from annex import convertValue, setupPrintProgress
from collections import defaultdict
from config_readers import RiskModuleConfigReader, MainConfig
from database import Database
from rm import calcSimulationStatistics
from constants import IRR_REPORT_FIELD, IRR_REPORT_FIELD2, IRR_REPORT_FIELD3, TEP_REPORT_FIELD, TEP_REPORT_FIELD2, TEP_REPORT_FIELD3

from enm import EnvironmentalModule
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from report import Report
from config_readers import MainConfig
from report_output import ReportOutput


class Simulation():
    """Class for preparing, runinning and saving simulations to Database"""

    def __init__(self, country, comment=''):
        """Initializes simulation class, preparing storage and db links.
        @country: the country to run the simulation for.
        @comment: user comment for this simulation."""
        self.db =  Database()  #connection to Db
        self.comment = comment  #user comment for current simulation
        self.country = country #country which data will be used in simulation
        self.simulation_no = self.db.getNextSimulationNo()  #load last simulation no from db
        self.rm_configs = RiskModuleConfigReader(self.country).getConfigsValues()

    def runSimulation(self,  iterations_number):
        """Run simulation with @iterations_number number of iterations."""
        self.initSimulationRecord(iterations_number)  # prepare atributes for saving simulation record
        self.runIterations(iterations_number)  # run all iterations with saving results
        self.addIrrStatsToSimulation()  # add IRR stats to simulation record for future speed access
        self.addTotalEnergyProducedStatsToSimulation()  # add TEP stats to simulation record for future speed access
        self.db.insertSimulation(self.simulation_record)   # insert simulation record

    def runIterations(self, iterations_number):
        """Run @iterations_number iterations."""

        cpu_count = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(cpu_count)
        data = [(i+1, self.simulation_no, self.country) for i in range(iterations_number)]
        result = pool.map(runIteration, data)  # irr and tep data
        result = zip(*result) # transpose

        # accumulation of values from all iterations
        self.irrs0, self.irrs1, self.irrs2 = result[:3]
        self.total_energy_produced, self.system_not_working, self.electricity_production_2ndyear = result[3:]

        #iterations_for_cpu = [[] for i in range(cpu_count)]
        #for i in range(iterations_number):
            #iterations_for_cpu[i % cpu_count].append(i+1)

        #thread_list = [multiprocessing.Process(target=runIterationsList, args=(lst, self)) for lst in iterations_for_cpu]

        #for t in thread_list: t.start()
        #for t in thread_list: t.join()
        #print self.irrs1
        #print self.total_energy_produced

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
        fields = [IRR_REPORT_FIELD, IRR_REPORT_FIELD2, IRR_REPORT_FIELD3]  #which field names will be used to calc stats

        riskFreeRate, benchmarkSharpeRatio = self.rm_configs['riskFreeRate'], self.rm_configs['riskFreeRate']
        self.simulation_record['irr_stats'] = calcSimulationStatistics(fields, [self.irrs0, self.irrs1, self.irrs2], riskFreeRate, benchmarkSharpeRatio )  #calculating and adding IRR stats to simulation record

    def addTotalEnergyProducedStatsToSimulation(self):
        """Adding total energy produced results to dict with simulation data."""
        fields = [TEP_REPORT_FIELD, TEP_REPORT_FIELD2, TEP_REPORT_FIELD3]
        riskFreeRate, benchmarkSharpeRatio = self.rm_configs['riskFreeRate'], self.rm_configs['riskFreeRate']
        self.simulation_record['total_energy_produced_stats'] = calcSimulationStatistics(
            fields, [self.total_energy_produced, self.system_not_working, self.electricity_production_2ndyear],
            riskFreeRate, benchmarkSharpeRatio)


class Iteration:
    """Class for running a single iteration."""

    def __init__(self, iteration_no, simulation_no, country):
        """Iteration number of this iteration and link to simulation module."""
        self.iteration_no = iteration_no
        self.simulation_no = simulation_no
        self.country = country
        self.db =  Database()  #connection to Db

        self.config = MainConfig(self.country)
        self.em = EnergyModule(self.config, self.country)
        self.sm = SubsidyModule(self.config, self.country)
        self.tm = TechnologyModule(self.config, self.em, self.country)
        self.enm = EnvironmentalModule(self.config, self.country, self.tm.total_nominal_power)
        self.ecm = EconomicModule(self.config, self.tm, self.sm, self.enm, self.country)
        self.r = Report(self.config, self.ecm, iteration_no, self.simulation_no)

    def run(self):
        """Runs 1 iteration and prepares new data."""
        print "running iter:", self.iteration_no
        self.r.calcReportValues()
        self.o = ReportOutput(self.r)
        self._prepareIterationResults()  # main func to prepare results in one dict

    def saveAndReturn(self):
        """Saves the data to simulation fields and database."""
        self.db.insertIteration(self.line)  # save iteration to db
        return self._getIrrValues() + self._getTepValues()

    def _prepareIterationResults(self):
        """prepare each iteration (@iteration number) results before saving to database"""
        obj = self.r
        line = dict()  #main dict for holding results of one iteration

        line["simulation"] = self.simulation_no
        line["iteration"] = self.iteration_no

        line["main_configs"] = self.config.getConfigsValues()
        line["ecm_configs"] = self.ecm.getConfigsValues()
        line["tm_configs"] = self.tm.getConfigsValues()
        line["sm_configs"] = self.sm.getConfigsValues()
        line["em_configs"] = self.em.getConfigsValues()
        line["enm_configs"] = self.enm.getConfigsValues()

        #####################################

        line["revenue"] = obj.revenue.values()  #values of revenue
        line["revenue_electricity"] = obj.revenue_electricity.values()
        line["revenue_subsidy"] = obj.revenue_subsidy.values()
        line["cost"] = obj.cost.values()
        line["operational_cost"] = obj.operational_cost.values()
        line["development_cost"] = obj.development_cost.values()
        line["ebitda"] = obj.ebitda.values()
        line["ebit"] = obj.ebit.values()
        line["ebt"] = obj.ebt.values()
        line["interest_paid"] = obj.interest_paid.values()
        line["depreciation"] = obj.depreciation.values()
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
        line["revenue_subsidy_y"] = obj.revenue_subsidy_y.values()
        line["cost_y"] = obj.cost_y.values()
        line["operational_cost_y"] = obj.operational_cost_y.values()
        line["development_cost_y"] = obj.development_cost_y.values()
        line["ebitda_y"] = obj.ebitda_y.values()
        line["ebit_y"] = obj.ebit_y.values()
        line["ebt_y"] = obj.ebt_y.values()
        line["interest_paid_y"] = obj.interest_paid_y.values()
        line["depreciation_y"] = obj.depreciation_y.values()
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
        line["fcf_project_before_tax"] = obj.fcf_project_before_tax.values()
        line["fcf_owners"] = obj.fcf_owners.values()
        line["fcf_project_y"] = obj.fcf_project_y.values()
        line["fcf_project_before_tax_y"] = obj.fcf_project_before_tax_y.values()
        line["fcf_owners_y"] = obj.fcf_owners_y.values()

        line["irr_project"] = obj.irr_project
        line["irr_project_before_tax"] = obj.irr_project_before_tax
        line["irr_owners"] = obj.irr_owners
        line["irr_project_y"] = obj.irr_project_y
        line["irr_project_before_tax_y"] = obj.irr_project_before_tax_y
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
        line["average_degradation_rate"] = self.tm.getAverageDegradationRate()
        line["average_power_ratio"] = self.tm.getAveragePowerRatio()

        line["insolations_daily"] = self.em.getInsolationsLifetime().values()
        line["electricity_production_daily"] = self.ecm.electricity_production.values()

        line["sun_insolation"] = obj.sun_insolation.values()
        line["sun_insolation_y"] = obj.sun_insolation_y.values()

        line["electricity_production"] = obj.electricity_production.values()
        line["electricity_production_y"] = obj.electricity_production_y.values()

        line["electricity_production_per_kW"] = obj.electricity_production_per_kW.values()
        line["electricity_production_per_kW_y"] = obj.electricity_production_per_kW_y.values()

        line["electricity_prices"] = obj.electricity_prices.values()
        line["electricity_prices_y"] = obj.electricity_prices_y.values()

        line["non_working_days"] = obj.non_working_days.values()
        line["non_working_days_y"] = obj.non_working_days_y.values()

        line["pv_owners"] = obj.pv_owners.values()
        line["pv_project"] = obj.pv_project.values()

        line["pv_owners_y"] = obj.pv_owners_y.values()
        line["pv_project_y"] = obj.pv_project_y.values()

        self.line = convertValue(line)

    def _getIrrValues(self):
        """Returns irr results fir specified attrributes."""
        return (getattr(self.r, IRR_REPORT_FIELD),
                getattr(self.r, IRR_REPORT_FIELD2),
                getattr(self.r, IRR_REPORT_FIELD3))

    def _getTepValues(self):
        """Returns total energy produced, system not working and electricity prod 2nd year attributes."""
        return (getattr(self.r, TEP_REPORT_FIELD),
                getattr(self.r, TEP_REPORT_FIELD2),
                getattr(self.r, TEP_REPORT_FIELD3))

def runIteration(args):
    i = Iteration(*args)
    i.run()
    return i.saveAndReturn()

def runAndSaveSimulation(country, iterations_no, comment):
    """
    1) Runs multiple iterations @iterations_number with @comment
    2) Shows charts
    3) Save results
    return  simulation_no
    """
    s = Simulation(country, comment=comment)
    s.runSimulation(iterations_no)
    return s.simulation_no


