1. Font Name
2. Font File (.ttf or .otf)
• Must be clearly labeled as either free for commercial use or personal use only
• Placed in a folder labeled with the font name
3. Preview Images
• Minimum 2 per font (name them FontName_Image1.jpg, FontName_Image2.jpg, etc.)
4. Font Description Text
• Scrape the main description/overview (style, usage, designer info if available)
5. Original Source URL
• Save the URL to the font’s page in a .txt file
6. License Information
• Note license type (e.g. “Free for commercial use”) and include any license file if available
7. Tags on the font

Fonts/
└── source_font_name/
    ├── FontName.ttf
    ├── FontName_Image1.jpg
    ├── FontName_Image2.jpg
    ├── description.txt
    ├── license.txt
    └── source_url.txt
    └── font tags.txt
    └── font_info.txt



Important function
get_font_information(font_link: str) -> str:
    return font_relative_folder

get_font_informations() -> List[str]:
    font_folders = []
    font_links = get_font_links()
    for font_link in font_links:
        font_folder = get_font_information(font_link)
        font_folders.append(font_folder)
    return font_folders

get_font_links() -> List[str]:
    return []
