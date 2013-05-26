import pylab
import numpy

from collections import OrderedDict
from database import Database
from constants import report_directory, CORRELLATION_FIELDS, CORRELLATION_IRR_FIELD, IRR_REPORT_FIELD, IRR_REPORT_FIELD2, CORRELLATION_NPV_FIELD
from annex import invert_dict
from itertools import izip_longest

def plot_charts(simulation_id, yearly=False):

    fields = ['iterations.revenue', 'iterations.cost', 'iterations.ebitda', 'iterations.deprication']
    results = Database().get_simulations_values_from_db(simulation_id, fields, yearly, convert_to=float)

    revenue, cost, ebitda, deprication =  results.values()
    last_revenue, last_cost, last_ebitda, last_deprication =  revenue[-1][1:], cost[-1][1:], ebitda[-1][1:], deprication[-1][1:]

    pylab.plot(last_revenue, label='REVENUE')
    pylab.plot(last_cost, label='COST')
    pylab.plot(last_ebitda, label='EBITDA')
    pylab.plot(last_deprication, label='deprication')
    #pylab.plot(net_earning, label='net_earning')

    pylab.xlabel("months")
    pylab.ylabel("EUROs")
    pylab.legend()
    pylab.grid(True, which="both",ls="-")
    pylab.axhline()
    pylab.axvline()

    title = 'Simulation %s. ' % simulation_id
    if yearly:
        title += 'Yearly data'
    else :
        title += "Monthly data"
    pylab.title(title)
    pylab.show()

def show_irr_charts(irr_values_lst, simulation_no):
    """Shows irr distribution and charts , field used for title"""

    values = []
    fig= pylab.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)  # share ax1's xaxis

    # Plot
    ax1.hist(values, bins=7)
    ax2.plot(range(1, len(values)+1), values, 'o')

    title_format = "Simulation %s. {0} of %s based on %s values" %(simulation_no, field, len(values))
    ax1.set_title(title_format.format("Histogram"))
    ax2.set_title(title_format.format("Chart"))
    pylab.show()


def show_irr_charts(irr_values_lst, simulation_no):
    """
    figures : <title, figure> dictionary
    """
    figures = OrderedDict()
    for dic in irr_values_lst:
        dig_values = dic['digit_values']

        title1 = "Simulation %s - Histogram of %s, based on %s values" % (simulation_no, dic['field'], len(dig_values))
        figures[title1] = dig_values

        title2 = "Simulation %s - Chart of %s, based on %s values" % (simulation_no, dic['field'], len(dig_values))
        figures[title2] = dig_values

    fig, axeslist = pylab.subplots(ncols=2, nrows=2)

    for ind,title in zip(range(4), figures):
        if title is not None:
            values = figures[title]
            if ind in [0, 2]:
                axeslist.ravel()[ind].hist(values, bins=7)
            else:
                limx, limy = get_limit_values(range(len(values)), values)
                axeslist.ravel()[ind].plot(values, 'o')
                axeslist.ravel()[ind].set_xlim(limx)
                axeslist.ravel()[ind].set_ylim(limy)

            axeslist.ravel()[ind].set_title(title)

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
        print ("Corellation using simulation %s with %s values from DB" % (simulation_id, number_values_used))

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
    pylab.title('Simulation %s. Correlation between %s and stochastic values, based on %s values' %(simulation_id, main_field_name, number_values_used))
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

def irr_scatter_charts(simulation_id, yearly=False):
    """
    figures : <title, figure> dictionary
    ncols : number of columns of subplots wanted in the display
    nrows : number of rows of subplots wanted in the figure
    """
    cols = 3
    rows = 2
    prefix = 'iterations.'
    main = prefix + CORRELLATION_IRR_FIELD.values()[0]
    figures = Database().get_simulations_values_from_db(simulation_id, [], yearly, not_changing_fields=[main]+CORRELLATION_FIELDS.values())
    if not figures:
            print ValueError('No data in Database for simulation %s' %simulation_id)
            return None

    irrs = figures.pop(main.split('.')[-1])
    titles = invert_dict(CORRELLATION_FIELDS)

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
            obj.set_xlabel(main)

            limx, limy = get_limit_values(irrs, values)

            obj.set_xlim(limx)
            obj.set_ylim(limy)

            obj.figure.add_axes([12,12,12,12], frameon=False)
        else:
            obj.set_axis_off()

    title = "Simulation %s. Scatter charts" % simulation_id
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

if __name__ == '__main__':
    plot_charts(61, True)
    #irr_scatter_charts(66, True)
    #plot_correlation_tornado(CORRELLATION_NPV_FIELD, 66)