import os
from annex import mkdir_p

REPORT_ROUNDING = 2
REPORT_PATH = '~/data/mirr_reports'     #relevent path to storing reports
report_directory = os.path.expanduser(os.path.normpath(REPORT_PATH))
mkdir_p(report_directory)


IS_ROWS = ["revenue", "cost", "ebitda", "deprication", "ebit",
        "iterest_paid", "ebt", "tax", "net_earning" ]

IS_NAMES = ["Dates", "Revenue", "Costs", "EBITDA", "Deprication", "EBIT",
         "Interest paid", "EBT", "Taxes", "Net earnings"]

BS_ROWS = ["fixed_asset", "current_asset", "inventory",
           "operating_receivable", "short_term_investment",
           "asset_bank_account", "asset",
           "paid_in_capital", "retained_earning", "unallocated_earning"]

BS_NAMES = ["Dates", "Fixed Assests", "Current Assets", "Inventories",
         "Operating Receivables", "Short-Term Investments",
         "Assets On Bank Accounts", "Assets",
         "Paid-In Capital", "Retained Earnings", "Unallocated Earnings"]