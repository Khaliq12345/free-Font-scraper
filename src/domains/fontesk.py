import asyncio
import os
from typing import List
import zipfile
import shutil
import httpx
from selectolax.parser import HTMLParser
import re
import subprocess

semaphore = asyncio.Semaphore(10)


def remove_at(path):
    if not os.path.exists(path):
        print(f"Le chemin {path} n'existe pas.")
        return
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
        print(f"Fichier supprimé : {path}")
    elif os.path.isdir(path):
        shutil.rmtree(path)
        print(f"Dossier supprimé avec son contenu : {path}")
    else:
        print(f"Type inconnu, impossible de supprimer : {path}")


def download_file(url: str, output_path: str) -> str:
    try:
        subprocess.run(
            ["curl", "-L", "--ssl-no-revoke", url, "-o", output_path],
            check=True,
        )
        return output_path
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")
        return ""


def unzip_folder(zip_path: str) -> str:
    try:
        extracted_path = os.path.splitext(zip_path)[
            0
        ]  # même nom que le zip sans extension
        os.makedirs(extracted_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extracted_path)
        print(f"Fichiers extraits dans : {extracted_path}")
        return extracted_path
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return ""


def find_font_file(root_path: str) -> str:
    search_path = os.path.join(root_path)
    if not os.path.exists(search_path):
        print(f"Le sous-dossier {search_path} n'existe pas.")
        return ""
    for root, _, files in os.walk(search_path):
        for file in files:
            if file.lower().endswith((".ttf", ".otf")):
                return os.path.join(root, file)
    print("Aucun fichier .ttf ou .otf trouvé.")
    return ""


def copy_and_rename_file(src_file: str, destination_folder: str, new_name: str) -> str:
    try:
        os.makedirs(destination_folder, exist_ok=True)
        dest_path = os.path.join(destination_folder, new_name)
        shutil.copy(src_file, dest_path)
        print(f"Fichier copié dans {dest_path}")
        return dest_path
    except Exception as e:
        print(f"Erreur lors de la copie : {e}")
        return ""


def text_to_txt(text_input: str, save_path: str) -> str:
    try:
        directory = os.path.dirname(save_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(text_input)
        print(f"Fichier créé avec succès : {save_path}")
        return save_path
    except Exception as e:
        print(f"Erreur lors de la création du fichier : {e}")
        return ""


def get_firstdir(parent_dir: str) -> str:
    entries = os.listdir(parent_dir)
    first_subdir = None
    for entry in entries:
        full_path = os.path.join(parent_dir, entry)
        if os.path.isdir(full_path):
            first_subdir = full_path
            break
    return first_subdir if first_subdir else ""


def process_font(data) -> str:
    font_name = str(data["name"]).replace(" ", "_").lower()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.abspath(
        os.path.join(current_dir, "..", "..", f"Fonts/fontesk_{font_name}")
    )
    if os.path.exists(path):
        return "Fonts/fontesk_{font_name}"
    print(f"path --- {path}")
    # Make Directory
    os.makedirs(path, exist_ok=True)
    # Zip File
    zip_path = download_file(data["download_link"], f"{path}/font_zip.zip")
    unzip_path = unzip_folder(zip_path)
    first_directory = get_firstdir(unzip_path)
    font_lookup_path = f"{first_directory}/static" if first_directory else unzip_path
    licence_lookup_path = first_directory if first_directory else unzip_path
    licence_ends_with = "license.txt" if first_directory else "nfo.txt"
    # Font .ttf or .otf
    font_file_path = find_font_file(font_lookup_path)
    copy_and_rename_file(
        font_file_path, path, f"{font_name}.{font_file_path.split('.')[-1]}"
    )
    # Images
    for index, img in enumerate(data["images"]):
        download_file(img, f"{path}/{font_name}_image{index + 1}.{img.split('.')[-1]}")
        pass
    # Full License
    for filename in os.listdir(licence_lookup_path):
        if filename.endswith(licence_ends_with):
            licence_file = os.path.join(licence_lookup_path, filename)
            copy_and_rename_file(licence_file, path, "license.txt")
            break
    # Description
    text_to_txt(data["description"], f"{path}/description.txt")
    # Tags
    text_to_txt(" - ".join(data["tags"]), f"{path}/tags.txt")
    # License Type
    text_to_txt(data["license"], f"{path}/font_type.txt")
    # Source
    text_to_txt(data["source_url"], f"{path}/source_url.txt")
    # Remove Zip and Extracted
    remove_at(unzip_path)
    remove_at(zip_path)
    return f"Fonts/fontesk_{font_name}"


def extract_images(tree, limit=2):
    images = []
    slider_blocks = tree.css("div.fw-slider-item")
    for block in slider_blocks:
        img_node = block.css_first("img")
        if img_node:
            src = img_node.attributes.get("src", "")
            if src and not src.startswith("data:image"):
                images.append(src)
        if len(images) >= limit:
            break
    return images


def extract_download_link(tree):
    download_link = ""
    script_nodes = tree.css("script")
    for script in script_nodes:
        script_text = script.text() or ""
        if "function downloads()" in script_text:
            match = re.search(r"window\.location\.href='([^']+)'", script_text)
            if match:
                download_link = match.group(1)
                break
    return download_link


async def get_font_information(client: httpx.AsyncClient, font_link: str) -> str:
    async with semaphore:
        try:
            response = await client.get(font_link, timeout=30)
            response.raise_for_status()
        except httpx.RequestError as e:
            print(f"Erreur réseau pour {font_link}: {e}")
            return ""
        except httpx.HTTPStatusError as e:
            print(f"Erreur HTTP {e.response.status_code} pour {font_link}")
            return ""

        tree = HTMLParser(response.text)

        # 1. Font Name
        node = tree.css_first("h1.entry-title")
        name = node.text().strip() if node else ""

        # 2. Images
        images = extract_images(tree, limit=2)

        # 3. Description
        description_nodes = tree.css("div.entry-content p")
        description = (
            " ".join([n.text(strip=True) for n in description_nodes])
            if description_nodes
            else ""
        )

        # 4. License
        license_node = tree.css_first("div.content-meta-license a")
        license_text = license_node.text(strip=True) if license_node else "Unspecified"

        # 5. Tags
        tags = []
        tag_section = tree.css_first("footer.entry-meta")
        if tag_section:
            for tag_node in tag_section.css("a[rel='tag']"):
                tags.append(tag_node.text(strip=True))

        # 6. Download link
        download_link = extract_download_link(tree)

        data = {
            "source_url": font_link,
            "name": name,
            "images": images,
            "description": description,
            "license": license_text,
            "tags": tags,
            "download_link": download_link,
        }

        print(data)
        font_relative_folder = process_font(data)
        return font_relative_folder


async def get_font_links(client: httpx.AsyncClient, page_url: str) -> List[str]:
    try:
        fonts_links = []
        response = await client.get(page_url, timeout=30)
        response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Erreur réseau pour {page_url}: {e}")
        return []
    except httpx.HTTPStatusError as e:
        print(f"Erreur HTTP {e.response.status_code} pour {page_url}")
        return []
    tree = HTMLParser(response.text)
    for node in tree.css("h2.entry-title a"):
        href = node.attributes.get("href")
        if href:
            fonts_links.append(href)
    return fonts_links


async def get_all_font_links(client: httpx.AsyncClient, base_url: str) -> List[str]:
    all_links = []
    page = 1
    while True:
        page_url = base_url if page == 1 else f"{base_url}page/{page}/"
        print(f" ---------------- << Scraping Page {page} >> ---------------- ")
        links = await get_font_links(client, page_url)
        if not links:
            print("Aucune police trouvée, arrêt du scraping.")
            break
        all_links.extend(links)
        page += 1

    return all_links


async def get_font_informations() -> List[str]:
    font_folders = []
    page_url = (
        "https://fontesk.com/license/free-for-commercial-use,free-for-personal-use/"
    )
    async with httpx.AsyncClient(
        follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}
    ) as client:
        font_links = await get_all_font_links(client, page_url)
        print(f"Got -- {len(font_links)} -- links")
        tasks = [get_font_information(client, link) for link in font_links]
        font_folders = await asyncio.gather(*tasks)

    return font_folders
