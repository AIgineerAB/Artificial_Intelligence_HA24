from pathlib import Path
import requests
from bs4 import BeautifulSoup


class NBILinkScraper:
    def __init__(self) -> None:
        self.base_url = "https://www.nbi-handelsakademin.se"

    def scrape(self, pathname, query=""):
        url = f"{self.base_url}/{pathname}/{query}"
        all_links_raw = ExtractHtml.soup(url).select(
            ".wpgb-card-media-content-bottom > a[href]"
        )

        extracted_links = set(link["href"] for link in all_links_raw)
        extracted_links = {url.split("/")[-2]: url for url in extracted_links}

        return extracted_links


class DataScraper:
    def __init__(self, pathname, query="") -> None:
        self.links = NBILinkScraper().scrape(pathname, query)

    def scrape(self, subject):
        description_raw = ExtractHtml.soup(self.links[subject]).select(
            ".wpb_text_column span, p,h4+ul li"
        )

        description = " ".join(
            [
                raw.text
                for raw in description_raw
                if not "\xa0" in raw.get_text()  # or "@" in raw.text)
            ]
        )

        return description


class EducationScraper(DataScraper):
    def __init__(self) -> None:
        super().__init__("utbildningar", query="/?_programkurser=program")


class CourseScraper(DataScraper):
    def __init__(self) -> None:
        super().__init__("kurser")


class ExtractHtml:
    @staticmethod
    def soup(url):
        response = requests.get(url)
        return BeautifulSoup(response.text, "html.parser")


class ScrapeFormat:
    def __init__(self, pathname) -> None:
        base_url = NBILinkScraper().base_url
        url = f"{base_url}/{pathname}"
        self.soup = ExtractHtml.soup(url)

    def extract_text(self, tag):
        text_list = [tag.text for tag in self.soup.select(tag)]
        return " ".join(text_list)

    def extract_list(self, tag):
        return [tag.text for tag in self.soup.select(tag)]


class ApplicationScraper:
    def __init__(self, pathname="ansokan") -> None:
        self._scraper = ScrapeFormat(pathname)

    @property
    def description(self):
        return self._scraper.extract_text("h1, h1~*")

    @property
    def time_plan(self) -> list:
        return self._scraper.extract_list("#tab-tidplan ul li, #tab-tidplan ul + p")

    @property
    def available_educations(self) -> list:
        return self._scraper.extract_list("#tab-ansok li")

    @property
    def application_steps(self) -> list:
        return self._scraper.extract_list("h3 a")


class FaqScraper:
    def __init__(self, pathname="faq") -> None:
        self._scraper = ScrapeFormat(pathname)

    @property
    def faq(self) -> list:
        return self._scraper.extract_list(".toggle.default a, .toggle.default p")


class ExportScrapedText:
    def __init__(self, filename, content) -> None:

        data_path = Path(__file__).parent / "data"
        data_path.mkdir(parents=True, exist_ok=True)

        with open(data_path / filename, "w") as file:
            file.write(content)
