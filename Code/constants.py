#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import sys
from annex import mkdir_p
from collections import OrderedDict


TESTMODE = True

REPORT_ROUNDING = 2
REPORT_PATH = '~/data/mirr_reports'     #relevent path to storing reports
report_directory = os.path.expanduser(os.path.normpath(REPORT_PATH))
mkdir_p(report_directory)

IS = OrderedDict()  #INCOME STATEMENT , format dic[field_name]=attr_name or blank
IS["Dates"] = ""
IS["Revenue"] = "revenue"
IS["Revenues electricity sales"] = "revenue_electricity"
IS["Revenues subsidy"] = "revenue_subsides"
IS["Costs"] = "cost"
IS["Operational costs"] = "operational_cost"
IS["Development costs"] = "development_cost"
IS["EBITDA"] = "ebitda"
IS["Deprication"] = "deprication"
IS["EBIT"] = "ebit"
IS["Interest paid"] = "iterest_paid"
IS["EBT"] = "ebt"
IS["Taxes"] = "tax"
IS["Net earnings"] = "net_earning"

BS = OrderedDict()  #BALANCE SHEET , format dic[field_name]=attr_name or blank
BS["Dates"] = ""
BS["Fixed Assests"] = "fixed_asset"
BS["Current Assets"] = "current_asset"
#BS["Inventories"] = "inventory"
BS["Operating Receivables"] = "operating_receivable"
#BS["Short-Term Investments"] = "short_term_investment"
BS["Assets On Bank Accounts"] = "asset_bank_account"
BS["Assets"] = "asset"
BS["Equity"] = "equity"

BS["Paid-In Capital"] = "paid_in_capital"
BS["Retained Earnings"] = "retained_earning"
BS["Unallocated Earnings"] = "unallocated_earning"
BS["Financial And Operating Obligations"] = "financial_operating_obligation"
BS["Long-Term Loans"] = "long_term_loan"
#BS["Long-Term Operating Liabilities"] = "long_term_operating_liability"
BS["Short-Term Loans"] = "short_term_loan"
BS["Short-Term Debt to Suppliers"] = "short_term_debt_suppliers"
BS["Liabilities"] = "liability"
BS["Control"] = "control"

PROJECT_START = "Project Start"



CF = OrderedDict()  #BALANCE SHEET , format dic[field_name]=attr_name or blank
CF["Dates"] = ""
CF["FCF project"] = "fcf_project"
CF["FCF owners"] = "fcf_owners"


