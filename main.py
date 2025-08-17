from Datenbank.DB_Config import init_db
from GetData.GD_Main import main as gd_main
from AnalyseData.AD_main import analyse_dashboard_data


def main():
    init_db()
    gd_main()
    analyse_dashboard_data()


if __name__ == "__main__":
    main()
