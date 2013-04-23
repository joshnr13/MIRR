
"""
3.4.2	generateElectiricityProduction
based on insolation generates electricity production values for each day
produced electricity = insolation * energyConversionFactor

3.4.3	getElectricityProduction
Parameters: dateStart, dateEnd
gives/reads the sum of the electricity produced in the specified period
getElectiricityProduction = sum of electricity in kWh for each day for the selected period

3.4.4	outputElectricityProduction
Parameters: start_date; end_date; resolution
Makes a graph (x-axis displays time; y-axis= displays electricity produced). The minimum interval on the x-axis is set by resolution (integer number of days).  Values on the y-axis are sum of the electricity produced in the time interval.


"""