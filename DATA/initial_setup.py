from utils.download_data import run_download_data
from utils.station_summary import run_station_summary
from utils.download_station_data import run_download_station_data
from utils.combine_data import run_combine_data
from utils.clean_data_imputation import run_clean_data_imputation
from utils.clean_data_wo_imputation import run_clean_data_wo_imputation
from utils.load_to_db import run_load_to_db


def main(imputation=False, verbose=True):
    print("\n" + "=" * 80)
    print("  STEP 1: Download BOM weather data")
    print("=" * 80)
    run_download_data(verbose=verbose)

    print("\n" + "=" * 80)
    print("  STEP 2: Create station summary")
    print("=" * 80)
    run_station_summary(verbose=verbose)

    print("\n" + "=" * 80)
    print("  STEP 3: Combine datasets")
    print("=" * 80)
    run_combine_data(verbose=verbose)

    print("\n" + "=" * 80)
    print("  STEP 4: Download Station data")
    print("=" * 80)
    run_download_station_data()

    print("\n" + "=" * 80)
    print("  STEP 5: Clean and impute data")
    print("=" * 80)
    if imputation:
        run_clean_data_imputation(verbose=verbose)
    else:
        run_clean_data_wo_imputation(verbose=verbose)

    print("\n" + "=" * 80)
    print("  STEP 6: Load everything to db")
    print("=" * 80)
    run_load_to_db()


if __name__ == "__main__":
    imputation_flag = False
    main(imputation=imputation_flag, verbose=True)