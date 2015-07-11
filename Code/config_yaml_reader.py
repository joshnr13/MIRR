from copy import deepcopy
import os
import random
import datetime
import cStringIO
import yaml
from annex import floatRange
from constants import TESTMODE

def read_file(name):
    """
    Reads yaml file, return converted dict
    """
    config_file = os.path.join(os.path.dirname(__file__), 'configs', name)
    try:
        content = yaml.load(open(config_file))
    except Exception as e:
        print "Error while parsing YAML file '%s'. Please check it's content!" % name
        raise
    else:
        return content

def update_dict(orig_dict, new_dict):
    """
    Update original dict using values from new_dict
    return new merged dict
    """
    orig_dict = deepcopy(orig_dict)
    for key, val in new_dict.iteritems():
        if isinstance(val, dict):
            tmp = update_dict(orig_dict.get(key, {}), val)
            orig_dict[key] = tmp
        elif isinstance(val, (list, long)):
            orig_dict[key] = (orig_dict[key] + val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict

def get_country_values(name, country, silent):
    """
    get country config from file @name using key @country
    with silent - will no print notification message
    """
    data = read_file(name)
    default_data = data['DEFAULT']
    if country in data:
        country_data = data[country]
        return update_dict(default_data, country_data)
    elif not silent:
        print '-'*80
        print "No country data in '%s' for %s. Will be used DEFAULT!" % (name, country)

    return default_data

def parse_list_and_get_random(values, value_type=int):
    """
    Parses input
    if one value - return it
    if two - return range(min, max, with step = 1)
    if three - return range(min, max, with step = last_value)
    """
    list_values = values.split(',')
    len_values = len(list_values)

    if not values or len_values > 4:
        raise ValueError("Config value error " + values)

    if len_values == 1:
        return value_type(list_values[0])
    elif len_values == 3:
        step = value_type(list_values.pop(2))
    else:
        step = 1

    min_value = min(map(value_type, list_values))
    max_value = max(map(value_type, list_values))
    if TESTMODE:
        return value_type(0.5 * (min_value + max_value))
    else:
        return random.choice(floatRange(min_value, max_value, step, True))

def get_random_config_value(value, value_type='guess'):
    """
    get random value for from,to
    or return original value
    """

    if value_type == 'guess':
        if '.' in value:
            if value.replace(' ', '').replace('.', '').replace(',', '').replace('-', '').isdigit():
                value_type = float
        elif value.replace(' ', '').replace(',', '').replace('-', '').isdigit():
            value_type = int

        else:
            value_type = str

    if value_type == str:
        return value
    elif value_type in (int, float):
        return parse_list_and_get_random(value, value_type=value_type)


def parse(dic):
    """
    parse config dict , convert all values to our format
    """
    result = deepcopy(dic)
    for key, value in dic.items():
        if isinstance(value, (str, int, float)):
            result[key] = get_random_config_value(str(value))
        else:
            result[key] = parse(value)
    return result

def parse_yaml(name, country, silent=False):
    config_dict = get_country_values(name, country, silent)
    parsed_config_dict = parse(config_dict)
    return parsed_config_dict

def apply_format(value, new_format):
    """
    Apply defined @format or type to @value
    """
    if new_format is None:
        return value

    formats = {}
    formats['date'] = lambda x: datetime.datetime.strptime(x, '%Y/%m/%d').date()
    formats['float_percent'] = lambda x: float(x)/100

    new_format = formats.get(new_format) or new_format
    return new_format(value)


def get_config_value(dic, path, type_format=None):
    """
    Get one value from large nested dict using path,
    optional convert value, using @type_format
    """
    dic_path = path.split('.')
    result = dic
    for key in dic_path:
        try:
            result = result[key]
        except KeyError:
            print 'Incorrect path "%s"' % (path,)
            raise
        except TypeError:
            print 'Incorrect YAML content, please check path "%s"' % (path,)
            raise

    return apply_format(result, type_format)

if __name__ == '__main__':
    config = parse_yaml('em_config.ini', 'ITALY')
    print get_config_value(config, 'INPUTS', dict)
