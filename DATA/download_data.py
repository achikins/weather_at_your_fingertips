import ftplib
import os
import tarfile
import datetime
import json


today_str = datetime.date.today().strftime("%Y-%m-%d")
download_folder = today_str

if os.path.exists(download_folder):
    print("-" * 100)
    print(f"\nFolder {download_folder} already existed\n")
    print("-" * 100)

else:
    os.makedirs(download_folder, exist_ok=True)

    with open("config.json") as f:
        config = json.load(f)
    FTP_HOST = config["ftp_host"]
    FTP_DIR = config["ftp_dir"]
    FILES_TO_DOWNLOAD = config["files_to_download"]

    ftp = ftplib.FTP(FTP_HOST)
    ftp.login()
    ftp.set_pasv(True)
    ftp.cwd(FTP_DIR)

    print("-" * 100)
    print("\nConnected to {ftp_host} and navigated to {ftp_dir}")

    for filename in FILES_TO_DOWNLOAD:
        local_path = os.path.join(download_folder, filename)
        
        with open(local_path, "wb") as f:
            print(f"Downloading {filename} ...")
            ftp.retrbinary(f"RETR {filename}", f.write)
            print(f"{filename} downloaded")

        if filename.endswith(".tgz") or filename.endswith(".tar.gz"):
            print(f"Extracting {filename} ...")
            with tarfile.open(local_path, "r:gz") as tar:
                tar.extractall(path=download_folder, filter="data")
            print(f"{filename} extracted to {download_folder}")
            os.remove(local_path)
            print(f"{filename} deleted after extraction")
    
    ftp.quit()
    print("")
    print("-" * 100)
    print("All Done")