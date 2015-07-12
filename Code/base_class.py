from Code.constants import TESTMODE


class BaseClassConfig():
    """class Wrapper for configs Module, simply returns some configs as attributes"""
    def __init__(self, config_module):
        self._config_module = config_module

    @property
    def start_date_project(self):
        return  self._config_module.getStartDate()

    @property
    def end_date_project(self):
        return self._config_module.getEndDate()

    @property
    def all_project_dates(self):
        return self._config_module.getAllDates()

    @property
    def real_permit_procurement_duration(self):
        return self._config_module.getPermitProcurementDuration()

    @property
    def real_construction_duration(self):
        return self._config_module.getConstructionDuration()

    @property
    def last_day_permit_procurement(self):
        return self._config_module.getLastDayPermitProcurement()

    @property
    def first_day_construction(self):
        return self._config_module.getFirstDayConstruction()

    @property
    def last_day_construction(self):
        return self._config_module.getLastDayConstruction()

    @property
    def resolution(self):
        return self._config_module.getResolution()

    @property
    def lifetime (self):
        return self._config_module.getLifeTime()

    @property
    def report_dates(self):
        return  self._config_module.getReportDates()

    @property
    def report_dates_y(self):
        return  self._config_module.getReportDatesY()

    @property
    def weather_data_rnd_simulation(self):
        simulation_no = self._config_module.weather_data_rnd_simulation
        if TESTMODE:
            print "** Using weather data simulation : %s" % simulation_no
        return simulation_no

    @property
    def electricity_prices_rnd_simulation(self):
        simulation_no = self._config_module.electricity_price_rnd_simulation
        if TESTMODE:
            print "** Using electricity price simulation : %s" % simulation_no
        return simulation_no





