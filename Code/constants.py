import os
from annex import mkdir_p

REPORT_PATH = '~/data/mirr_reports'     #relevent path to storing reports
report_directory = os.path.expanduser(os.path.normpath(REPORT_PATH))
mkdir_p(report_directory)