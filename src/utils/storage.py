import sys

sys.path.append("..")

from src.utils import BunnyCDNStorage
import os
from pathlib import Path
from src.core import config

# initialize the font folder
font_raw_path = "../Fonts/"
font_path = Path(font_raw_path)

# get all the fonts in the Font folder
folders = os.listdir(font_path)


def process_folder(
    folder: str,
):
    single_font = os.path.join(font_path, folder)

    # load all files
    files = os.listdir(single_font)
    # initialize a connection with the bunny storage
    cdn_connector = BunnyCDNStorage.CDNConnector(
        config.BUNNY_TOKEN,
        "free-fonts",
    )

    print(f"Files - {files}")
    for file in files:
        print(f"File - {file}")
        # upload file to the storage
        try:
            cdn_connector.upload_file(
                f"Fonts/{folder}/",
                file_name=file,
                file_path=os.path.join(
                    single_font,
                    file,
                ),
            )
        except Exception as e:
            print(f"Error - {e}")


def main():
    for folder in folders:
        print(f"Folder - {folder}")
        process_folder(folder)


if __name__ == "__main__":
    main()
