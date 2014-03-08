import datetime
from config_readers import MainConfig, SubsidyModuleConfigReader, TechnologyModuleConfigReader, EconomicModuleConfigReader

_country='1ITALY'
config = MainConfig(_country)
# print config.getConfigsValues()

_country='ITALY'
startdate = datetime.datetime(2000,1,1)
config = SubsidyModuleConfigReader(_country, startdate)
# print config.getConfigsValues()


config = TechnologyModuleConfigReader(_country)
# print config.getConfigsValues()

config = EconomicModuleConfigReader(_country, startdate)
print config.getConfigsValues()
