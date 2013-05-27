#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
from annex import mkdir_p
from collections import OrderedDict

TESTMODE = False

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

CF = OrderedDict()  #CASH FLOW , format dic[field_name]=attr_name or blank
CF["Dates"] = ""
CF["FCF project"] = "fcf_project"
CF["FCF owners"] = "fcf_owners"

NPV = OrderedDict()  #NPV , format dic[field_name]=attr_name or blank
NPV["Dates"] = ""
NPV["NPV project"] = "pv_project"
NPV["NPV owners"] = "pv_owners"

IRR_REPORT_FIELD = 'irr_project_y'
IRR_REPORT_FIELD2 = 'irr_owners_y'  #for statistics after simulation
NPV_REPORT_FIELD = 'npv_project_y'


REPORT_DEFAULT_NUMBER_SIMULATIONS = 10
REPORT_DEFAULT_NUMBER_ITERATIONS = 20

CORRELLATION_FIELDS = OrderedDict() # IRR ONE SHOULD HAVE NAME =IRR and be FIRST ONE
CORRELLATION_FIELDS["permit_procurement_duration"] = "main_configs.real_permit_procurement_duration"
CORRELLATION_FIELDS["construction_duration"] = "main_configs.real_construction_duration"
CORRELLATION_FIELDS["subsidy_Kw"] = "sm_configs.kWh_subsidy"
CORRELLATION_FIELDS["subsidy_delay"] = "sm_configs.subsidy_delay"
CORRELLATION_FIELDS["subsidy_duration"] = "sm_configs.subsidy_duration"

CORRELLATION_IRR_FIELD = {"IRR": IRR_REPORT_FIELD}
CORRELLATION_NPV_FIELD = {"NPV": NPV_REPORT_FIELD}

SECOND_SHEET = OrderedDict()
SECOND_SHEET["Dates"] = ""
SECOND_SHEET["Solar insolation"] = "sun_insolation"
SECOND_SHEET["Production of electricity"] = "electricity_production"
SECOND_SHEET["Electricity prices"] = "electricity_prices"
