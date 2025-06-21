from AnalyseData.AD_Account import overal_balance, account_balance, \
    account_distribution
from AnalyseData.AD_Depotbuilder import calculate_depot_distribution, \
    calculate_depot_value, calculate_input, calculate_shares
from AnalyseData.AD_Kategories import spending_overall, \
    spending_distribution, kategorie_spending
# from AnalyseData.AD_SummUp import current_summary, future_projection


def analyse_dashboard_data():
    calculate_buyin = calculate_input("safe_sparplan.csv")
    print("calculate buyin", calculate_buyin)
    calculate_shares()
    calculate_depot_value()
    calculate_depot_distribution()
    account_balance()
    overal_balance()
    account_distribution()
    kategorie_spending()
    spending_distribution()
    spending_overall()
    # current_summary()
    # future_projection()
