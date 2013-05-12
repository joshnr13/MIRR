from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from report import Report
from main_config_reader import MainConfig
from report_output import ReportOutput

class Mirr():
    def __init__(self):
        main_config = MainConfig()
        self.main_config = main_config
        self.energy_module = EnergyModule(main_config)
        self.technology_module = TechnologyModule(main_config, self.energy_module)
        self.subside_module = SubsidyModule(main_config)
        self.economic_module = EconomicModule(main_config, self.technology_module, self.subside_module)
        self.r = Report(main_config, self.economic_module)
        self.r.calc_report_values()
        self.o = ReportOutput(self.r)

    def getMainConfig(self):
        return  self.main_config

    def getEnergyModule(self):
        return  self.energy_module

    def getTechnologyModule(self):
        return  self.technology_module

    def getSubsideModule(self):
        return  self.subside_module

    def getEconomicModule(self):
        return  self.economic_module

    def getReportModule(self):
        return  self.r

    def getOutputModule(self):
        return  self.o

