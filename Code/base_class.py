
class BaseClassConfig():
    def __init__(self, config_module):
        self._config_module = config_module

    @property
    def start_date_project(self):
        return  self._config_module.getStartDate()

    @property
    def end_date_project(self):
        return self._config_module.getEndDate()

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


