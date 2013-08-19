import pylab
import numpy
import datetime

from collections import OrderedDict
from database import Database
from constants import report_directory, CORRELLATION_FIELDS, CORRELLATION_IRR_FIELD, IRR_REPORT_FIELD, IRR_REPORT_FIELD2, CORRELLATION_NPV_FIELD, BINS
from annex import addYearlyPrefix, getResolutionStartEnd
from itertools import izip_longest


db = Database()

def plot_charts(simulation_no, iteration_no=1, yearly=False):

    fields = ['revenue', 'cost', 'ebitda', 'deprication']
    results = Database().get_iteration_values_from_db(simulation_no, fields, yearly, iteration_no=iteration_no)

    suffix = '_y' * yearly
    #revenue, cost, ebitda, deprication =  results.values()
    revenue = results['revenue'+suffix]
    cost = results['cost'+suffix]
    ebitda = results['ebitda'+suffix]
    deprication = results['deprication'+suffix]
    #print revenue, suffix, results
    last_revenue, last_cost, last_ebitda, last_deprication =  revenue[1:], cost[1:], ebitda[1:], deprication[1:]

    pylab.plot(last_revenue, label='REVENUE')
    pylab.plot(last_cost, label='COST')
    pylab.plot(last_ebitda, label='EBITDA')
    pylab.plot(last_deprication, label='deprication')
    #pylab.plot(net_earning, label='net_earning')

    pylab.ylabel("EUROs")
    pylab.legend()
    pylab.grid(True, which="both",ls="-")
    pylab.axhline()
    pylab.axvline()

    title_add = get_title_period(yearly)
    x_axis_title = get_x_axis_title(yearly)

    title = 'Simulation %s - iteration %s . %s' % (simulation_no, iteration_no, title_add)
    pylab.xlabel(x_axis_title)

    pylab.title(title)
    pylab.show()

def show_irr_charts(irr_values_lst, simulation_no, yearly):
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
                limx, limy = get_limit_values(range(len(values)), values)
                axeslist.ravel()[ind].plot(values, 'o')
                axeslist.ravel()[ind].set_xlim(limx)
                axeslist.ravel()[ind].set_ylim(limy)

            axeslist.ravel()[ind].set_title(title)

    pylab.show()


def plot_histograms(dic_values, simulation_no, yearly):
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

    #title = "Simulation %s. Scatter charts '%s'. %s" % (simulation_no, add_yearly_prefix(field, yearly), get_title_period(yearly))
    title = "Sim. N. %s. Stochastic histograms. %s iterations" % (simulation_no, len(values))
    fig = pylab.gcf()
    fig.suptitle(title, fontsize=14)

    pylab.show()



def plot_correlation_tornado(field_dic, simulation_id, yearly=False):
    """Plot tornado chart with correlation of field and other stochastic variables"""

    values = []
    field_values = {}
    main_field_name = field_dic.keys()[0]
    main_field_db_name = field_dic.values()[0]

    results = Database().get_correlation_values(main_field_db_name, simulation_id, yearly)

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
    pos1 = [get_pos_no(value, sorted_list, used) for value in v1]
    pos2 = [get_pos_no(value, sorted_list, used) for value in v2]

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

def irr_scatter_charts(simulation_no, field, yearly=False):
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

    figures = Database().get_iteration_values_from_db(simulation_no, [main], yearly, not_changing_fields=CORRELLATION_FIELDS.values())

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

            limx, limy = get_limit_values(irrs, values)

            obj.set_xlim(limx)
            obj.set_ylim(limy)

            obj.figure.add_axes([12,12,12,12], frameon=False)
        else:
            obj.set_axis_off()


    title = "Simulation %s. Scatter charts '%s'. %s" % (simulation_no, addYearlyPrefix(field, yearly), get_title_period(yearly))
    fig = pylab.gcf()
    fig.suptitle(title, fontsize=14)

    pylab.show()

##################################### ANNEX CHARTS FUNCTIONS ###################

def get_pos_no(value, sorted_list, used):
    for i, v in enumerate(sorted_list):
        if v == value and i not in used:
            used.append(i)
            return i

def get_limit_values(x, y):
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


def get_title_period(yearly):
    if yearly:
        title = 'Yearly data'
    else :
        title = "Monthly data"
    return title

def get_x_axis_title(yearly):
    if yearly:
        title = 'years'
    else :
        title = "months"
    return title

def step_chart(simulation_no, iteration_no, start_date, end_date, resolution, field):

    dates_range = getResolutionStartEnd(start_date, end_date, resolution)
    y_all_values = db.get_iteration_field(simulation_no, iteration_no, field)
    keys = db.get_iteration_field(simulation_no, iteration_no, 'project_days')

    keys = map(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(), keys)
    y_all_values = dict((x, y) for x, y in zip(keys, y_all_values))  #was @!! y_all_values = dict((x, y) for x, y in zip(keys, y_all_values[1:]))

    def sum_period(start, days):
        return

    x_values = []
    y_values = []
    sm = 0

    for day_from, day_to in dates_range:
        delta = (day_to - day_from).days
        sum_period = sum([y_all_values[day_from+datetime.timedelta(days=days)] for days in range(delta)])
        y_values.append(sum_period)
        x_values.append(sm+delta)
        sm += delta

    #print x_values
    #print y_values

    pylab.step(x_values, y_values)
    title = "Sim. N. {simulation_no}; Iter. N. {iteration_no}. Electricity production from {start_date} to {end_date} - res. {resolution} days".format(**locals())
    pylab.title(title, fontsize=12)
    pylab.show()

if __name__ == '__main__':
    import datetime as dt
    start_date = dt.date(2013, 1, 1)
    end_date = dt.date(2017, 12, 31)
    #plot_charts(61, True)
    #irr_scatter_charts(11, 'irr_project', True)
    step_chart(60, 1, start_date, end_date, 10, 'insolations_daily')
    #plot_correlation_tornado(CORRELLATION_NPV_FIELD, 66)