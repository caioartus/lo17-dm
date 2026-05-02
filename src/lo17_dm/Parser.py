import os.path
import re
from pathlib import Path

from bs4 import BeautifulSoup
from lxml import etree


class BulletinParser:
    def __init__(self, path: Path):
        self.path = path

    def load(self):
        """Open htlm file and read contents, and extract DOM to etree"""
        with open(self.path) as f:
            self.content = f.read()
            self.soup = BeautifulSoup(self.content, "html.parser")
            self.dom = etree.HTML(str(self.soup))

    def extract_data(self):
        """Extract all fields"""
        dom = self.dom
        # document title
        self.title = dom.xpath(
            '//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[3]/td[1]/p[1]/span[2]/text()'
        )[0].strip()
        # author info
        auteur_info = "".join(
            dom.xpath(
                'string(//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[8]/td[2]/p/span)'
            )
        )
        # number of the article
        self.num_article = dom.xpath(
            '//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[6]/td[3]/p/a/span/text()'
        )[0]
        # number of the bulletin
        self.num_buletin = (
            dom.xpath(
                '//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[1]/td[3]/p/span[1]/text()'
            )[0]
            .strip()
            .replace("BE France", "")
            .strip()
        )
        # date of the article
        self.date = dom.xpath(
            '//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[1]/td[3]/p/span[3]/text()'
        )[0].strip()
        # rubrique title
        self.rubrique = dom.xpath(
            '//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[3]/td[1]/p[1]/span[1]/text()'
        )[0].strip()
        # contact info
        self.info_contact = "".join(
            dom.xpath(
                'string(//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[6]/td[2]/p/span)'
            )
        )
        # extract data from the main table data where the main text is
        td = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[3]/td[1]')[0]
        # extract text from table data but not images
        self.text = " ".join(
            td.xpath(
                ".//text()[not(ancestor::div[img]) and not(ancestor::span[@class='style88'])]"
            )
        ).strip()
        # extract images from table data
        self.images = [
            {
                "url": img.xpath("./@src")[0],
                "caption": " ".join(
                    img.xpath("./following-sibling::span//text()")
                ).strip(),
            }
            for img in td.xpath(".//div[img]/img")
        ]

        # extrait l'auteur et ses infos avec du regex (très souple car il y a souvent des erreurs)

        m = re.search(
            r"^(.*?)\s*-\s*(.*?)\s*-\s*emai.*\s*:\s*(.*?)$", auteur_info, re.IGNORECASE
        )

        if m:
            self.org, self.name, self.email = m.groups()
        else:
            print("None found")
            print(auteur_info)
            self.org, self.name, self.email = None, None, None

    def makeXML(self) -> str:
        """
        Builds XML for inserting into the main XML file with the corpus
        """
        root = etree.Element("document")

        etree.SubElement(root, "titre").text = self.title
        etree.SubElement(root, "rubrique").text = self.rubrique
        etree.SubElement(root, "article").text = self.num_article
        etree.SubElement(root, "bulletin").text = self.num_buletin
        etree.SubElement(root, "date").text = self.date
        etree.SubElement(root, "texte").text = self.text
        etree.SubElement(root, "auteur").text = self.name
        etree.SubElement(root, "contact").text = self.info_contact
        imgs = etree.SubElement(root, "images")
        for img in self.images:
            img_elem = etree.SubElement(imgs, "image")
            etree.SubElement(img_elem, "urlImage").text = img["url"]
            etree.SubElement(img_elem, "legendeImage").text = img["caption"]

        xml_str = etree.tostring(root, pretty_print=True, encoding="unicode")
        return xml_str


class CorpusParser:
    documents: list[BulletinParser]

    def __init__(self, folder_path: str | Path):
        self.folder_path: Path = Path(folder_path)
        self.documents: list[BulletinParser] = []

    def parseFiles(self) -> None:
        """Parses files in input folder one by one building BulletinParser objects as we go"""
        if not os.path.exists(self.folder_path):
            raise FileNotFoundError("Folder not found.")
        for file in self.folder_path.iterdir():
            if file.is_file():
                bulletin = BulletinParser(file)
                bulletin.load()
                bulletin.extract_data()
                self.documents.append(bulletin)

    def makeXML(self) -> str:
        """Builds the full XML file from all of the BulletinParser objects"""
        root = etree.Element("corpus")
        for bulletin in self.documents:
            # pour chaque bulletin on le wrap dans un <document>
            bulletin_xml = etree.fromstring(bulletin.makeXML())  # we dont escape yet
            root.append(bulletin_xml)
        xml_str = etree.tostring(root, pretty_print=True, encoding="unicode")
        self.xml_str = xml_str
        return xml_str

    def save_xml(self, path: str | Path) -> None:
        """Save in XML file"""
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.xml_str)
