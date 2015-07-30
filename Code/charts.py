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

def plotRevenueCostsChart(simulation_no, iteration_no=1, yearly=False, country=None):
    """Plots 'revenue', 'cost', 'ebitda', 'depreciation' chart"""

    fields = ['revenue', 'cost', 'ebitda', 'depreciation']
    results = Database().getIterationValuesFromDb(simulation_no, fields, yearly,
        iteration_no=iteration_no, country=country)  # loading field values form DB

    suffix = '_y' * yearly
    revenue = results['revenue'+suffix]
    cost = results['cost'+suffix]
    ebitda = results['ebitda'+suffix]
    depreciation = results['depreciation'+suffix]

    last_revenue, last_cost, last_ebitda, last_depreciation = revenue[1:], cost[1:], ebitda[1:], depreciation[1:]

    pylab.plot(last_revenue, label='REVENUE')
    pylab.plot(last_cost, label='COST')
    pylab.plot(last_ebitda, label='EBITDA')
    pylab.plot(last_depreciation, label='Depreciation')

    pylab.ylabel("EUROs")
    pylab.legend()
    pylab.grid(True, which="both", ls="-")
    pylab.axhline()
    pylab.axvline()

    title_add = getTitleBasedOnPeriod(yearly)  #generating title Monthly or Yearly
    x_axis_title = getAxisTitleBasedOnPeriod(yearly)

    title = '%r - Simulation %s - iteration %s . %s' % (country, simulation_no, iteration_no, title_add)
    pylab.xlabel(x_axis_title)

    pylab.title(title)
    pylab.show()

def plotIRRChart(irr_values_lst, simulation_no, yearly, country):
    """Plots irr_values histogram and scatter plot for the @country and @simulation_no."""

    figures = OrderedDict()
    for dic in irr_values_lst:
        dig_values = dic['digit_values']

        title1 = "%s - Sim. N%s. Histogram of %s - %s values" % (country, simulation_no, dic['field'], len(dig_values))
        figures[title1] = dig_values

        title2 = "%s - Sim N%s. Chart of %s - %s values" % (country, simulation_no, dic['field'], len(dig_values))
        figures[title2] = dig_values

    fig, axeslist = pylab.subplots(ncols=2, nrows=3)

    for ind, title in zip(range(len(figures)), figures):
        if title is not None:
            values = figures[title]
            if ind % 2 == 0:
                mu = numpy.mean(values)
                sigma = numpy.std(values)

                weights = numpy.ones_like(values) / float(len(values))
                counts, bins, patches = axeslist.ravel()[ind].hist(values, bins=numpy.linspace(mu-0.25, mu+0.25, 51), weights=weights)

                y = []
                for x in bins:
                    try:
                        y.append(pylab.normpdf(x, mu, sigma) / 100)
                    except FloatingPointError: # underflow encountered
                        y.append(0)

                axeslist.ravel()[ind].plot(bins, y, 'r--', linewidth=2)
                axeslist.ravel()[ind].set_xlim(mu-0.25, mu+0.25)
            else:
                limx, limy = getLimitValues(range(len(values)), values)
                axeslist.ravel()[ind].plot(values, 'o')
                axeslist.ravel()[ind].set_xlim(limx)
                axeslist.ravel()[ind].set_ylim(limy)

            axeslist.ravel()[ind].set_title(title)

    pylab.show()

def plotTotalEnergyProducedChart(electricity_total_values, simulation_no, yearly, country):
    """Plots total electricity production in MWh and days of system not working."""

    figures = OrderedDict()
    for dic in electricity_total_values:
        dig_values = dic['digit_values']

        title1 = "%s - Sim. N%s. Histogram of %s - %s values" % (country, simulation_no, dic['field'], len(dig_values))
        figures[title1] = dig_values

        title2 = "%s - Sim N%s. Chart of %s - %s values" % (country, simulation_no, dic['field'], len(dig_values))
        figures[title2] = dig_values

    fig, axeslist = pylab.subplots(ncols=2, nrows=3)
    for ind, title in zip(range(len(figures)), figures):
        if title is not None:
            values = figures[title]
            if ind % 2 == 0:
                if set(values) == set([0]): # all counts are the same
                    axeslist.ravel()[ind].hist([0], bins=range(20))
                else:
                    weights = numpy.ones_like(values) / float(len(values))
                    counts, bins, patches = axeslist.ravel()[ind].hist(values, bins=BINS, weights=weights)
            else:
                limx, limy = getLimitValues(range(len(values)), values)
                axeslist.ravel()[ind].plot(values, 'o')
                axeslist.ravel()[ind].set_xlim(limx)
                ymin, ymax = limy
                if ymin == ymax: # get rid of user warning of the same limits
                    ymax += numpy.finfo(type(ymax)).eps
                    ymin -= numpy.finfo(type(ymax)).eps
                axeslist.ravel()[ind].set_ylim((ymin, ymax))

            axeslist.ravel()[ind].set_title(title)

    pylab.show()

def plotHistogramsChart(dic_values, simulation_no, yearly, country=None):
    """
    figures : <title, figure> dictionary
    """
    figures = OrderedDict()
    for name, values in dic_values.items():
        title = "%s" % name
        figures[title] = values

    cols, rows = getNumberColsRows(len(figures))
    fig, axeslist = pylab.subplots(ncols=cols, nrows=rows)

    for ind,title in izip_longest(range(cols*rows), figures):
        if title is not None:
            values = figures[title]
            axeslist.ravel()[ind].hist(values, bins=BINS)
            axeslist.ravel()[ind].set_title(title)
        else:
            axeslist.ravel()[ind].set_axis_off()

    title = "%s - Sim. N. %s. Stochastic histograms. %s iterations" % (country, simulation_no, len(values))
    fig = pylab.gcf()
    fig.suptitle(title, fontsize=14)
    pylab.show()


def plotElectricityHistogram(dic_values, what, simulation_no, country):
    """Plots several (3) histograms of electricity prices"""

    TITLES = {'price_diff': 'Price differences from day to day',
              'abs_price_diff': 'Absolute prices differences from day to day',
              'prices': 'Price from day to day'}
    figures = OrderedDict()
    for name, values in dic_values.items():
        title = TITLES.get(name, "%s" % name)  # to use human readable title
        figures[title] = values

    cols, rows = getNumberColsRows(len(figures))
    fig, axeslist = pylab.subplots(ncols=cols, nrows=rows)

    for ind, title in izip_longest(range(cols * rows), figures):
        if title is not None:
            values = figures[title]
            axeslist.ravel()[ind].hist(values, bins=BINS)
            axeslist.ravel()[ind].set_title(title)
        else:
            axeslist.ravel()[ind].set_axis_off()

    title = "Sim %s. Daily electricity price distribuiton for %s" % (simulation_no, country)
    fig = pylab.gcf()
    fig.suptitle(title, fontsize=14)
    pylab.show()


def plotCorrelationTornadoChart(field_dic, simulation_id, yearly=False, country=None):
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

    if number_values_used == 0:
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
    pylab.title('%r - Simulation %s - %s iterations\nCorrelation between %s and stochastic variables' %(country, simulation_id, number_values_used, main_field_name))
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


def getNumberColsRows(fig_count):
    if fig_count in range(0, 5):
        cols, rows = 2, 2
    elif fig_count < 7:
        cols, rows = 3, 2
    elif fig_count < 13:
        cols, rows = 4, 3
    elif fig_count < 16:
        cols, rows = 5, 3
    else:
        raise ValueError("%s - To many charts cant be shown on screen" % fig_count)
    return cols, rows

def plotIRRScatterChart(simulation_no, field, yearly=False, country=None):
    """
    Plots XY chart for correlation @field with CORRELLATION_FIELDS
    figures : <title, figure> dictionary
    ncols : number of columns of subplots wanted in the display
    nrows : number of rows of subplots wanted in the figure
    """
    prefix = ''
    main = prefix + field
    real_field_shortname = addYearlyPrefix(field, yearly)

    figures = Database().getIterationValuesFromDb(simulation_no, [main], yearly, not_changing_fields=CORRELLATION_FIELDS.values())
    cols, rows = getNumberColsRows(len(figures))

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
            obj.set_xlabel(real_field_shortname+"\n", labelpad=-2)

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

def plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution,
                  field, country):
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
        delta = (day_to - day_from).days + 1  # +1 -> to include last day
        sum_period = sum([y_all_values[day_from+datetime.timedelta(days=days)] for days in range(delta)])
        y_values.append(sum_period)
        x_values.append(sm+delta)
        sm += delta

    title = "{country}\n Sim. N. {simulation_no}; Iter. N. {iteration_no}. {field} {start_date}-{end_date} - res. {resolution} days".format(**locals())
    pylab.step(x_values, y_values)
    pylab.title(title, fontsize=12)
    pylab.show()


def plotWeatherChart(data_dic, what, simulation_no, country, chosen_simulation=None):
    """Plot Weather Insolation and Temperature
    XY chart for @what , which will be title,
    based on @data_dic,
    which keys will be X values and values will be Y values
    """

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    if isinstance(simulation_no, int):
        data_dic = [data_dic]
        chosen_simulation = 0
        chosen_simulation_no = simulation_no
    else:
        chosen_simulation_no = chosen_simulation

    x_values = data_dic[chosen_simulation].keys()
    y_values = data_dic[chosen_simulation].values() #combined values [1469.06645, -1.11432, 1.55653], ...
    y_values_insolation = []
    y_values_temp = []
    for combined_value in y_values:
        ins, temp = combined_value[0], combined_value[1]
        y_values_insolation.append(ins)
        y_values_temp.append(temp)

    ax = plt.subplot(111)
    if isinstance(simulation_no, int):
        plt.title('%r - %s simulation %s' % (country, what, chosen_simulation_no))
    else:
        plt.title('%r - Multiple (%s) -  %s simulations' % (country, len(data_dic), what))

    for data in data_dic:
        y_values_prod_per_kw = [data[day][2] for day in data]
        ax.plot(x_values, y_values_prod_per_kw)

    ax.set_ylabel('Production per kW')
    ax.set_xlabel("Dates")
    plt.show()

    ax1 = plt.subplot(111)
    ax1.plot(x_values, y_values_insolation, 'b-')
    ax1.set_ylabel('Insolation')
    ax1.set_xlabel('Dates')
    ax2 = plt.twinx()
    ax2.plot(x_values, y_values_temp, 'r--')
    ax2.set_ylabel('Temperature')

    plt.title('%r - %s simulation %s' % (country, what, chosen_simulation_no))
    plt.xlabel("Dates")
    plt.show()


def plotElectricityChart(data_list, what, simulation_no, country):
    """Plot Electricity prices simple XY chart for @what , which will be title,
    based on @data_dic,
    which keys will be X values and values will be Y values
    """

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    if isinstance(simulation_no, int):
        data_list = [data_list]
        plt.title('%r - %s simulation %s' % (country, what, simulation_no))
    else:
        plt.title('%r - Multiple (%s) -  %s simulations' % (country, len(data_list), what))

    for data_dic in data_list:
        #iterating ower list of dicts with simulation data
        x_values = data_dic.keys()
        y_values = data_dic.values()
        plt.plot(x_values,y_values)

    plt.gcf().autofmt_xdate()

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
