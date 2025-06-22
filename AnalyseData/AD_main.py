from AnalyseData.AD_Account import overal_balance, account_balance, \
    account_distribution
from AnalyseData.AD_Depotbuilder import calculate_depot_distribution, \
    calculate_depot_value, calculate_input, calculate_shares
from AnalyseData.AD_Kategories import spending_overall, \
    spending_distribution, kategorie_spending
# from AnalyseData.AD_SummUp import current_summary, future_projection


depot = "safe_sparplan.csv"
einkommen = "safe_einkommen.csv"
fixkosten = "safe_fixkosten.csv"


def analyse_dashboard_data():
    calculated_buyin = calculate_input(depot)
    print("calculate buyin", calculated_buyin)
    calculated_shares = calculate_shares(depot)
    calculate_depot_value(calculated_shares)
    calculate_depot_distribution(calculated_shares)
    account_balance()
    overal_balance()
    account_distribution()
    kategorie_spending()
    spending_distribution()
    spending_overall()
    # current_summary()
    # future_projection()
