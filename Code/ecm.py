"""
4.4.2	getRevenue
parameters: dateStart; dateEnd
E:= getElectiricityProduction;
sum for all days in the period: E * price + subsidies (E; date)

4.4.3	getCosts
parameters: dateStart; dateEnd
sum of costs for all days in teh period = num of days * costs per month/30
4.4.4	calculateTaxes
EBT in the year * 20%
enetered only in december

4.4.5	getDebtPayment
parameters: dateStart; dateEnd,.....
calculate the payment of the debt principal based on constant annuity repayment  - http://en.wikipedia.org/wiki/Fixed_rate_mortgage

4.4.6	calculateInterests
((debt in previous period + debt in current period) /2) * interest rate * num of days/365

4.4.7	calculateFCF
calculates the free cash flow based on IS nad BS
= net earnings + amortisation – investments in long term assests

4.4.8	generateISandBS
parameters: dateStart; dateEnd

"""

class EconomicModule:

    def __init__(self):
        self.loadConfig()
        self.loadMainConfig()

    def loadMainConfig(self, filename='main_config.ini'):
        """Reads main config file """
        config = ConfigParser.SafeConfigParser({'lifetime': 30, 'start_date': '2000/1/1', 'resolution': 10})
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.lifetime = config.getint('Main', 'lifetime')
        self.resolution = config.getint('Main', 'resolution')
        self.start_date = datetime.datetime.strptime(config.get('Main', 'start_date'), '%Y/%m/%d').date()
        self.end_date = datetime.date(self.start_date.year + self.lifetime, self.start_date.month, self.start_date.day)

    def loadConfig(self, filename='ecm_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)

        self.tax_rate = config.getfloat('Taxes', 'tax_rate')
        self.operational_costs = config.getfloat('Costs', 'operational_costs')
        self.costs_groth_rate = config.getfloat('Costs', 'growth_rate')

        self.market_price = config.getfloat('Electricity', 'market_price')
        self.price_groth_rate = config.getfloat('Electricity', 'growth_rate')

        self.investments = config.getfloat('Investments', 'investment_value')

        self.debt = config.getfloat('Debt', 'debt_value') * self.investments
        self.debt_rate = config.getfloat('Debt', 'interest_rate')

    def getRevenue(self): pass

    def getCosts(self): pass

    def getDebtPayment(self): pass

    def calculateInterests(self): pass

    def calculateFCF(self): pass

    def generateISandBS(self): pass













