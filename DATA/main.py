from download_data import run_download_data
from station_summary import run_station_summary
from download_station_data import run_download_station_data
from combine_data import run_combine_data
from clean_data_imputation import run_clean_data_imputation
from clean_data_wo_imputation import run_clean_data_wo_imputation
from transformer.ptd_imputation import run_prepare_transformer_data_imputation
from transformer.ptd_wo_imputation import run_prepare_transformer_data_wo_imputation


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
    print("  STEP 4: Clean and impute data")
    print("=" * 80)
    if imputation:
        run_clean_data_imputation(verbose=verbose)
    else:
        run_clean_data_wo_imputation(verbose=verbose)

    print("\n" + "=" * 80)
    print("  STEP 5: Prepare transformer data")
    print("=" * 80)
    if imputation:
        run_prepare_transformer_data_imputation(verbose=verbose)
    else:
        run_prepare_transformer_data_wo_imputation(verbose=verbose)



if __name__ == "__main__":
    main(imputation=False, verbose=True)