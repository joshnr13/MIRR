# Usage: python batch_runner.py

# 1  -->  SLOVENIA
# 2  -->  AUSTRIA
# 3  -->  ITALY
# 4  -->  GERMANY
# 5  -->  NETHERLANDS
# 6  -->  CROATIA
# 7  -->  FRANCE
# 8  -->  FRANCE-NICE

#######################################
###########  ENTER DATA    ############
#######################################

number_of_simulations = 2
countries = [7, 7]
numbers_of_iterations = [50, 50]

conf_data = [
    {
        'taxrate': '0',
        'duration': '0',
    },
    {
        'taxrate': '0',
        'duration': '60',
    }
             ]

#######################################
#######################################
#######################################

# These must pass
assert len(countries) == number_of_simulations
assert len(numbers_of_iterations) == number_of_simulations
assert len(conf_data) == number_of_simulations

import glob
from string import Template
import os

for it in range(number_of_simulations):
    print "Iteration", it+1
    print "Writing confs..."
    for conf_template_name in glob.glob('config_templates/*.ini'):
        with open(conf_template_name) as conf_template:
            template = Template(conf_template.read())
            conf = template.substitute(conf_data[it])
            bn = os.path.basename(conf_template_name)
            conf_to_write = os.path.join('configs', bn)
            print "writing", conf_to_write
            with open(conf_to_write, 'w') as g:
                g.write(conf)
    print "Done!"
    print "Running simulation:"
    print "  country:", countries[it]
    print "  iterations:", numbers_of_iterations[it]
    print "  conf_data:", conf_data[it]

    # zaporedje ukazov za mirr.py
    # torej 1, za simulacijo, potem st. drzave, st. iteracij, prazen komentar, in se 0 na koncu, da
    # lepo zakljuci. Se komot spremeni.
    input_data = "1\n{0}\n{1}\n\n0\n".format(countries[it], numbers_of_iterations[it])
    os.system('echo "{0}" | python mirr.py'.format(input_data))

    print "Done!"
    print "##################################"
