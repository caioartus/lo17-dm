import re
from lxml import etree
from bs4 import BeautifulSoup
from pathlib import Path
import html
class Bulletins:
    def __init__(self, path : Path):
        self.path = path


    def load(self):
        with open(self.path) as f:
            self.content = f.read()
            self.soup = BeautifulSoup(self.content, 'html.parser')
            self.dom = etree.HTML(str(self.soup))

    def extract_data(self):
        dom = self.dom

        self.title = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[3]/td[1]/p[1]/span[2]/text()')[0].strip()
        auteur_info = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[8]/td[2]/p/span/text()')[0]
        self.auteur_email = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[8]/td[2]/p/span/a/text()')[0]

        self.num_article = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[6]/td[3]/p/a/span/text()')[0]
        self.num_buletin = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[1]/td[3]/p/span[1]/text()')[
            0].strip().replace("BE France", "").strip()
        self.date = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[1]/td[3]/p/span[3]/text()')[0].strip()
        self.rubrique = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[3]/td[1]/p[1]/span[1]/text()')[
            0].strip()

        self.info_contact = ''.join(dom.xpath('string(//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[6]/td[2]/p/span)'))

        td = dom.xpath('//*[@id="LayoutTable"]/table/tr[7]/td/table/tr[3]/td[1]')[0]

        self.text = ' '.join(td.xpath('.//text()[not(ancestor::div[img])]')).strip()

        self.images = [
            {
                "url": img.xpath('./@src')[0],
                "caption": ' '.join(img.xpath('./following-sibling::span//text()')).strip()
            }
            for img in td.xpath('.//div[img]/img')
        ]

        m = re.search(r'^(.*?)\s*-\s*(.*?)\s*-', auteur_info)
        if m:
            self.org, self.name = m.groups()
        else:
            self.org, self.name = None, None

    def makeXML(self) -> str:
        root = etree.Element("Bulletin")

        etree.SubElement(root, "titre").text = self.title
        etree.SubElement(root, "rubrique").text = self.rubrique
        etree.SubElement(root, "article").text = self.num_article
        etree.SubElement(root, "bulletin").text = self.num_buletin
        etree.SubElement(root, "date").text = self.date
        etree.SubElement(root, "texte").text = self.text


        author = etree.SubElement(root, "auteur")
        etree.SubElement(author, "nom").text = self.name
        etree.SubElement(author, "organisation").text = self.org
        etree.SubElement(author, "email").text = self.auteur_email
        etree.SubElement(root, "contact").text = self.info_contact
        imgs = etree.SubElement(root, "images")
        for img in self.images:
            img_elem = etree.SubElement(imgs, "Image")
            etree.SubElement(img_elem, "URL").text = img["url"]
            etree.SubElement(img_elem, "Caption").text = img["caption"]

        xml_str = etree.tostring(root, pretty_print=True, encoding='unicode')
        xml_str = html.unescape(xml_str)
        xml_str = html.unescape(xml_str)
        return xml_str

if __name__ == "__main__" :
    bul = Bulletins(Path("../data/BULLETINS/71359.htm"))
    bul.load()
    bul.extract_data()
    print(bul.makeXML())