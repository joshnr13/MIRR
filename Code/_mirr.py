from enm import EnvironmentalModule
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from report import Report
from config_readers import MainConfig
from report_output import ReportOutput


class Mirr():
    """Main class for combining all modules together
    """
    def __init__(self, country, iteration_no=None, simulation_no=None):
        """Creates all modules at INIT"""
        main_config = MainConfig(country)
        self.iteration_no = iteration_no
        self.simulation_no = simulation_no
        self.main_config = main_config
        self.energy_module = EnergyModule(main_config, country)
        self.technology_module = TechnologyModule(main_config, self.energy_module, country)
        self.subsidy_module = SubsidyModule(main_config, country)
        self.enviroment_module = EnvironmentalModule(main_config, country, self.technology_module.total_nominal_power)

        self.economic_module = EconomicModule(main_config, self.technology_module,
                                              self.subsidy_module, self.enviroment_module, country)
        self.r = Report(main_config, self.economic_module, iteration_no, simulation_no)

    def getMainConfig(self):
        """return  link to main config"""
        return  self.main_config

    def getEnergyModule(self):
        """return  link to energy module"""
        return  self.energy_module

    def getTechnologyModule(self):
        """return  link to technology module"""
        return  self.technology_module

    def getsubsidyModule(self):
        """return  link to subsidy module"""
        return  self.subsidy_module

    def getEconomicModule(self):
        """return  link to economic module"""
        return  self.economic_module

    def getReportModule(self):
        """return  link to report module"""
        return  self.r

    def getOutputModule(self):
        """return  link to report output module
        first we prepare (calculate) report values and after
        that initing new cls
        """
        self.r.calcReportValues()
        return ReportOutput(self.r)

    def getEnviromentModule(self):
        return self.enviroment_module



