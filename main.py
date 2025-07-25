import asyncio
from src.domains.fontesk import get_font_informations


def main():
    print("Hello from free-font-scraper !")
    result = asyncio.run(get_font_informations())
    print(f"Total fonts processed: {len([f for f in result if f])}")


if __name__ == "__main__":
    main()
