import pylab
import numpy
import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from collections import OrderedDict
from database import Database
from constants import report_directory, BINS, CORRELLATION_FIELDS
from annex import addYearlyPrefix, getResolutionStartEnd
from itertools import izip_longest

db = Database()

def plotRevenueCostsChart(simulation_no, iteration_no=1, yearly=False):
    """Plots 'revenue', 'cost', 'ebitda', 'deprication' chart"""

    fields = ['revenue', 'cost', 'ebitda', 'deprication']
    results = Database().getIterationValuesFromDb(simulation_no, fields, yearly, iteration_no=iteration_no)  #loding field values form DB

    suffix = '_y' * yearly
    revenue = results['revenue'+suffix]
    cost = results['cost'+suffix]
    ebitda = results['ebitda'+suffix]
    deprication = results['deprication'+suffix]

    last_revenue, last_cost, last_ebitda, last_deprication =  revenue[1:], cost[1:], ebitda[1:], deprication[1:]

    pylab.plot(last_revenue, label='REVENUE')
    pylab.plot(last_cost, label='COST')
    pylab.plot(last_ebitda, label='EBITDA')
    pylab.plot(last_deprication, label='deprication')

    pylab.ylabel("EUROs")
    pylab.legend()
    pylab.grid(True, which="both",ls="-")
    pylab.axhline()
    pylab.axvline()

    title_add = getTitleBasedOnPeriod(yearly)  #generating title Monthly or Yearly
    x_axis_title = getAxisTitleBasedOnPeriod(yearly)

    title = 'Simulation %s - iteration %s . %s' % (simulation_no, iteration_no, title_add)
    pylab.xlabel(x_axis_title)

    pylab.title(title)
    pylab.show()

def plotIRRChart(irr_values_lst, simulation_no, yearly):
    """
    figures : <title, figure> dictionary
    """
    figures = OrderedDict()
    for dic in irr_values_lst:
        dig_values = dic['digit_values']

        title1 = "Sim. N. %s. Histogram of %s - %s values" % (simulation_no, dic['field'], len(dig_values))
        figures[title1] = dig_values

        title2 = "Sim N. %s. Chart of %s - %s values" % (simulation_no, dic['field'], len(dig_values))
        figures[title2] = dig_values

    fig, axeslist = pylab.subplots(ncols=2, nrows=2)
    for ind,title in zip(range(4), figures):
        if title is not None:
            values = figures[title]
            if ind in [0, 2]:
                n, bins, patches = axeslist.ravel()[ind].hist(values, bins=BINS, normed=True)
                mu = numpy.mean(values)
                sigma = numpy.std(values)
                y = pylab.normpdf( bins, mu, sigma)
                axeslist.ravel()[ind].plot(bins, y, 'r--', linewidth=1)
            else:
                limx, limy = getLimitValues(range(len(values)), values)
                axeslist.ravel()[ind].plot(values, 'o')
                axeslist.ravel()[ind].set_xlim(limx)
                axeslist.ravel()[ind].set_ylim(limy)

            axeslist.ravel()[ind].set_title(title)

    pylab.show()

def plotHistogramsChart(dic_values, simulation_no, yearly):
    """
    figures : <title, figure> dictionary
    """
    figures = OrderedDict()
    for name, values in dic_values.items():
        title = "%s" % name
        figures[title] = values

    fig, axeslist = pylab.subplots(ncols=3, nrows=2)

    for ind,title in izip_longest(range(6), figures):
        if title is not None:
            values = figures[title]
            axeslist.ravel()[ind].hist(values, bins=BINS)
            axeslist.ravel()[ind].set_title(title)
        else:
            axeslist.ravel()[ind].set_axis_off()

    title = "Sim. N. %s. Stochastic histograms. %s iterations" % (simulation_no, len(values))
    fig = pylab.gcf()
    fig.suptitle(title, fontsize=14)
    pylab.show()

def plotCorrelationTornadoChart(field_dic, simulation_id, yearly=False):
    """Plot tornado chart with correlation of field and other stochastic variables"""

    values = []
    field_values = {}
    main_field_name = field_dic.keys()[0]
    main_field_db_name = field_dic.values()[0]

    results = Database().getCorrelationValues(main_field_db_name, simulation_id, yearly)

    if not results:
        return  None
    else:
        rounded_values_dict, number_values_used = results

    if number_values_used  ==  0:
        print "No needed values in Database. Please run simulations before!"
        return
    else:
        print ("Corellations using sim N. %s with %s values" % (simulation_id, number_values_used))

    for i, (field_short_name, main_field_db_name) in enumerate(CORRELLATION_FIELDS.items()):
        short_db_name = main_field_db_name.split('.')[-1]
        value = rounded_values_dict[short_db_name]
        print "Correllation between %s and %s = %s" % (short_db_name, field_short_name, value)
        if numpy.isnan(value):
            value = 0
        values.append(value)
        field_values[field_short_name] = value

    fig = pylab.figure(1)
    ax = fig.add_subplot(111)

    v1 = list(filter(lambda x : x>0, values))
    v2 = list(filter(lambda x : x<=0, values))
    v1.sort(key=abs, reverse=True)
    v2.sort(key=abs, reverse=True)

    sorted_list = sorted(values, key=abs)
    used = []
    pos1 = [getPosNo(value, sorted_list, used) for value in v1]
    pos2 = [getPosNo(value, sorted_list, used) for value in v2]

    ax.barh(pos1,v1, align='center', color='g')
    ax.barh(pos2,v2, align='center', color='r')

    y_names = sorted(field_values.items(), key=lambda x: abs(x[1]), reverse=True)
    y_names = [g[0] for g in y_names]

    pylab.yticks(list(reversed(range(len(y_names)))), y_names)
    pylab.xlabel('correlation coefficient')
    pylab.title('Sim N. %s. Correlation between %s and stochastic variables - %s iter.' %(simulation_id, main_field_name, number_values_used))
    pylab.grid(True)
    pylab.xlim(-1,1)
    pylab.ylim(-0.5, len(field_values)-0.5)
    #setp(ax.get_yticklabels(), fontsize=12,)

    fig.subplots_adjust(left=0.35)

    for (i,j) in zip(v1,pos1):
        value = i
        rel_position = len(str(value))
        pylab.annotate(value, xy=(i,j), color='green', weight='bold', size=12,xytext=(rel_position, 00), textcoords='offset points',)

    for (i,j) in zip(v2,pos2):
        value = i
        rel_position = -len(str(value)) * 8
        pylab.annotate(value, xy=(i,j), color='red', weight='bold', size=12,xytext=(rel_position, 00), textcoords='offset points',)

    pylab.show()

def plotIRRScatterChart(simulation_no, field, yearly=False):
    """
    Plots XY chart for correlation @field with CORRELLATION_FIELDS
    figures : <title, figure> dictionary
    ncols : number of columns of subplots wanted in the display
    nrows : number of rows of subplots wanted in the figure
    """
    cols = 3
    rows = 2
    prefix = ''
    main = prefix + field
    real_field_shortname = addYearlyPrefix(field, yearly)

    figures = Database().getIterationValuesFromDb(simulation_no, [main], yearly, not_changing_fields=CORRELLATION_FIELDS.values())

    if not figures:
            print ValueError('No data in Database for simulation %s' %simulation_no)
            return None

    irrs = figures.pop(real_field_shortname)
    fig, axeslist = pylab.subplots(ncols=cols, nrows=rows)
    left,bottom,width,height = 0.2,0.1,0.6,0.6 # margins as % of canvas size

    for ind,title in izip_longest(range(cols*rows), figures):
        obj = axeslist.ravel()[ind]
        if title is not None:
            values = figures[title]
            plot_title = title  #titles[prefix+title]

            axes = pylab.Axes(obj.figure, [1,1,1,1]) # [left, bottom, width, height] where each value is between 0 and 1

            obj.plot(irrs, values, 'o')
            obj.set_title(plot_title)
            obj.set_xlabel(real_field_shortname)

            limx, limy = getLimitValues(irrs, values)

            obj.set_xlim(limx)
            obj.set_ylim(limy)

            obj.figure.add_axes([12,12,12,12], frameon=False)
        else:
            obj.set_axis_off()


    title = "Simulation %s. Scatter charts '%s'. %s" % (simulation_no, addYearlyPrefix(field, yearly), getTitleBasedOnPeriod(yearly))
    fig = pylab.gcf()
    fig.suptitle(title, fontsize=14)

    pylab.show()

def plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution, field):
    """Plots step chart based on database data, recieved based on inputs
    simulation_no and iteration_no
    start_date and end_date, date resolution
    field - field which used for chart
    """

    y_all_values = db.getIterationField(simulation_no, iteration_no, field)  #get all 'field' values from database
    keys = db.getIterationField(simulation_no, iteration_no, 'project_days')  #get dates for filed from database
    keys = map(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(), keys)  #converting string dates into datetime
    y_all_values = dict((x, y) for x, y in zip(keys, y_all_values))  #getting dict [date]=field value

    x_values = []
    y_values = []
    sm = 0

    for day_from, day_to in getResolutionStartEnd(start_date, end_date, resolution): #get dates for axis using resolution value
        delta = (day_to - day_from).days
        sum_period = sum([y_all_values[day_from+datetime.timedelta(days=days)] for days in range(delta)])
        y_values.append(sum_period)
        x_values.append(sm+delta)
        sm += delta

    title = "Sim. N. {simulation_no}; Iter. N. {iteration_no}. {field} from {start_date} to {end_date} - res. {resolution} days".format(**locals())
    pylab.step(x_values, y_values)
    pylab.title(title, fontsize=12)
    pylab.show()


def plotWeatherChart(data_dic, what, simulation_no):
    """Plot Weather Insolation and Temperature
    XY chart for @what , which will be title,
    based on @data_dic,
    which keys will be X values and values will be Y values
    """

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    x_values = data_dic.keys()
    y_values = data_dic.values() #combined values [1469.0687372877435, -1.1144659386320814], ...
    y_values_insolation = []
    y_values_temp = []
    for combined_value in y_values:
        ins, temp = combined_value[0], combined_value[1]
        y_values_insolation.append(ins)
        y_values_temp.append(temp)

    #plt.gcf().autofmt_xdate()

    ax1 = plt.subplot(111)
    ax1.plot(x_values, y_values_insolation, 'b-')
    ax1.set_ylabel('Insolation')
    ax1.set_xlabel('Dates')
    ax2 = plt.twinx()
    ax2.plot(x_values, y_values_temp, 'r--')
    ax2.set_ylabel('Temperature')

    plt.title(' %s simulation %s' % (what, simulation_no))
    plt.xlabel("Dates")
    plt.show()


def plotElectricityChart(data_list, what, simulation_no):
    """Plot Electricity prices simple XY chart for @what , which will be title,
    based on @data_dic,
    which keys will be X values and values will be Y values
    """

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    for data_dic in data_list:
        #iterating ower list of dicts with simulation data
        x_values = data_dic.keys()
        y_values = data_dic.values()
        plt.plot(x_values,y_values)

    plt.gcf().autofmt_xdate()

    if isinstance(simulation_no, int):
        plt.title(' %s simulation %s' % (what, simulation_no))
    else:
        plt.title('Multiple (%s) -  %s simulations' % (len(data_list), what))

    plt.xlabel("Dates")
    plt.ylabel(what)
    plt.show()


##################################### ANNEX CHARTS FUNCTIONS ###################

def getPosNo(value, sorted_list, used):
    """Gets free position on chart with multi-internal charts"""
    for i, v in enumerate(sorted_list):
        if v == value and i not in used:
            used.append(i)
            return i

def getLimitValues(x, y):
    """Calculates limits for chart borders"""
    min_irr = min(x)
    max_irr = max(x)
    irr_range = max_irr - min_irr

    min_val = min(y)
    max_val = max(y)
    val_range = max_val - min_irr

    delta_x = 0.05
    delta_y = 0.05

    min_irr = min_irr - delta_x * irr_range
    max_irr = max_irr + delta_x * irr_range

    min_val = min_val - delta_y * val_range
    max_val = max_val + delta_y * val_range

    return ((min_irr, max_irr), (min_val, max_val))

def getTitleBasedOnPeriod(yearly):
    if yearly:
        title = 'Yearly data'
    else :
        title = "Monthly data"
    return title

def getAxisTitleBasedOnPeriod(yearly):
    if yearly:
        title = 'years'
    else :
        title = "months"
    return title


if __name__ == '__main__':
    import datetime as dt
    start_date = dt.date(2013, 1, 1)
    end_date = dt.date(2017, 12, 31)
    #plot_charts(61, True)
    #irr_scatter_charts(11, 'irr_project', True)
    plotStepChart(60, 1, start_date, end_date, 10, 'insolations_daily')
