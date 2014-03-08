from copy import deepcopy
import os
import random

import yaml

from annex import floatRange
from constants import TESTMODE


def read_file(name):
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs', name)
    return yaml.load(open(config_file))


def update_dict(orig_dict, new_dict):
    for key, val in new_dict.iteritems():
        if isinstance(val, dict):
            tmp = update_dict(orig_dict.get(key, {}), val)
            orig_dict[key] = tmp
        elif isinstance(val, (list, long)):
            orig_dict[key] = (orig_dict[key] + val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict


def get_values(name, country):
    data = read_file(name)
    default_data = data['DEFAULT']
    if data.has_key(country):
        country_data = data[country]
        return update_dict(default_data, country_data)
    else:
        print "No country data in '%s' for %s. Will be used default"
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

    if not values or len_values > 3:
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


def config_get_random(value, value_type='guess'):
    if value_type == 'guess':
        if '.' in value:
            if value.replace(' ', '').replace('.', '').replace(',', '').isdigit():
                value_type = float
        elif value.replace(' ', '').replace(',', '').isdigit():
            value_type = int
        else:
            value_type = str

    if value_type == str:
        return value
    elif value_type in (int, float):
        return parse_list_and_get_random(value, value_type=value_type)


def parse(dic):
    result = deepcopy(dic)
    for key, value in dic.items():
        if isinstance(value, (str, int)):
            result[key] = config_get_random(str(value))
        else:
            result[key] = parse(value)
    return result


print get_values('main_config.ini', 'ITALY')
config = parse(get_values('main_config.ini', 'ITALY'))


def get_config_value(dic, path, type_format=None):
    dic_path = path.split('.')
    result = dic
    for key in dic_path:
        try:
            result = result[key]
        except KeyError:
            print 'Incorrect path "%s"' % (path,)
            raise

    return type_format(result) if type_format else result


print get_config_value(config, 'MAIN.resolution1', int)

