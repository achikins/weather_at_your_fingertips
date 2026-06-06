'''
download_data.py

Purpose:
    Download daily weather station datasets from BOM FTP server, extract them, and save to a dated folder. 
    The script checks if the folder for today's date already exists to avoid redundant downloads. 

Software Requirements Satisfied:
    R-14: System shall download BOM weather data
'''

import ftplib               # FTP communication library
import os                   # File and directory operations
import tarfile              # Extraction of .tar.gz archives
import datetime             # Date handling
import json                 # Reading configuration file   
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent  # Determine the directory containing this script.
config_path = BASE_DIR / "config.json"      # Full path to configuration file.

def run_download_data(verbose=True):
    '''
    Download all required files from the configured FTP server.

    Process:
        1. Check if a folder named with today's date already exists. If it does, skip the download.
        2. Connect to the FTP server.
        3. Download all files listed in config.json.
        4. Extract compressed archives (.tgz / .tar.gz).
        5. Remove the original archive after extraction.
    
    Parameters:
        verbose (bool): If True, print status messages during the download and extraction process.
    
    Returns:
        None
    '''
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    download_folder = today_str

    if os.path.exists(download_folder): # Check whether today's folder already exists.
        if verbose:
            print(f"\nFolder {download_folder} already existed\n")

    else:
        os.makedirs(download_folder, exist_ok=True) # Create the date-based download directory

        with open(config_path) as f:    # Read FTP configuration information from config.json
            config = json.load(f)
        FTP_HOST = config["ftp_host"]   # "ftp.bom.gov.au" - FTP server hosting the weather data
        FTP_DIR = config["ftp_dir"]     # "anon/gen/clim_data/IDCJAC0009" - directory containing the daily weather station datasets
        FILES_TO_DOWNLOAD = config["files_to_download"] # ["IDCKWCDEA0.tgz"] - list of files to download from the FTP server

        ftp = ftplib.FTP(FTP_HOST)  # Establish FTP connection
        ftp.login()                 # Anonymous login
        ftp.set_pasv(True)          # Enable passive mode for firewall compatibility
        ftp.cwd(FTP_DIR)            # Change to the specified directory on the FTP server

        for filename in FILES_TO_DOWNLOAD:  # Download each file specified in configuration
            local_path = os.path.join(download_folder, filename)
            
            with open(local_path, "wb") as f:   # Download file in binary mode
                ftp.retrbinary(f"RETR {filename}", f.write)
                if verbose:
                    print(f"{filename} downloaded")

            if filename.endswith(".tgz") or filename.endswith(".tar.gz"):  # Check if the downloaded file is a compressed archive
                with tarfile.open(local_path, "r:gz") as tar:   # Extract archive contents into download folder
                    tar.extractall(path=download_folder, filter="data")
                os.remove(local_path)   # Remove archive after successful extraction
                if verbose:
                    print(f"{filename} extracted to {download_folder}")
                    print(f"{filename} deleted after extraction")
                
        ftp.quit()  # Close FTP connection and release resources

if __name__ == "__main__":
    run_download_data()
