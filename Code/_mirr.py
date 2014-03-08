from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from report import Report
from config_readers import MainConfig
from report_output import ReportOutput
from annex import cached_property

class Mirr():
    """Main class for combining all modules together
    """
    def __init__(self, country):
        """Creates all modules at INIT"""
        main_config = MainConfig(country)
        self.main_config = main_config
        self.energy_module = EnergyModule(main_config, country)
        self.technology_module = TechnologyModule(main_config, self.energy_module, country)
        self.subside_module = SubsidyModule(main_config, country)
        self.economic_module = EconomicModule(main_config, self.technology_module, self.subside_module, country)
        self.r = Report(main_config, self.economic_module)

    def getMainConfig(self):
        """return  link to main config"""
        return  self.main_config

    def getEnergyModule(self):
        """return  link to energy module"""
        return  self.energy_module

    def getTechnologyModule(self):
        """return  link to technology module"""
        return  self.technology_module

    def getSubsideModule(self):
        """return  link to subside module"""
        return  self.subside_module

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



