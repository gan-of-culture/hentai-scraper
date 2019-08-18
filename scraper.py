from urllib.request import urlopen, Request, urlretrieve
from os.path import join, dirname, realpath
from os import getcwd
from bs4 import BeautifulSoup as soup
from sys import exit
import re
from json import dump

REQ_HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}

class Scraper:
    def __init__(self,  path: str=join(dirname(realpath(__file__)), "images")):
        self.RULE34_URL = "http://rule34.paheal.net/post/list/"
        self.DANBOORU_URL = "https://danbooru.donmai.us/posts?utf8=true;&page=<page>&ms=1&tags="

        self.image_limit = 1
        self.path = path
        self.urls = []

    def scrape_page(self, url: str):
        if url is not None:
            self.urls.append(url)
            self.image_limit = 1

        self._scrape_images()

    def scrape_by_tags(self, tags: list, image_limit: int=1):
        tag_url = tags[0]
        for tag in tags[1:]:
            tag_url = tag_url + "%20" + tag #%20 represents a space in the url
        self.urls.append(self.RULE34_URL + tag_url + "/<page>")

        tag_url = tags[0]
        for tag in tags[1:]:
            tag_url = tag_url + "+" + tag
        self.urls.append(self.DANBOORU_URL + tag_url)

        self.image_limit = image_limit

        self._scrape_images()

    def update_tags(self):
        tags = { "Rule34": {},
                 "Danbooru": {} }
        
        #get tag categorys
        tag_a_elements = self._get_soup("http://rule34.paheal.net/tags").find_all("span", {"class": "atoz"})[0].find_all("a")
        tag_categories = [ tag.text for tag in tag_a_elements ]
        for key in tags:
            for category in tag_categories:
                tags[key][category.upper()] = []

        #Rule 34
        tag_urls = [ "http://rule34.paheal.net" + tag.get("href") for tag in tag_a_elements ]

        for url in tag_urls:
            #all tags have a style element - find thoose
            tag_links = self._get_soup(url).find_all("section", {"id": "Tagsmain"})[0].find_all("div", {"class": "blockbody"})[0].find_all("a", {"style": re.compile(".*")})
            for tag in tag_links:
                tags["Rule34"][tag.text[0].upper()].append(tag.text)

        #Donboru
        basic_url = "https://danbooru.donmai.us/tags?commit=Search&page=<page>&search[category]=0&search[hide_empty]=yes&search[name_matches]=<tag_category>*&search[order]=name&utf8=%E2%9C%93"
        for category in tag_categories:
            page_index = 1
            current_url = basic_url.replace("<tag_category>", category + "*")
            while True:
                current_url = current_url.replace("<page>", str(page_index))
                site_content = self._get_soup(current_url)

                tag_table_rows = site_content.find_all("table", {"class": "striped"})[0].tbody.find_all("tr")
                if tag_table_rows == []:
                    break
                
                for row in tag_table_rows:
                    tag_text = row.find_all("td", {"class": "category-0"})[0].find_all("a")[1].text
                    tags["Danbooru"][tag_text[0].upper()].append(tag_text)

                page_index += 1

        with open("tags.json", "w") as tag_file:
            dump(tags, tag_file)

    def _get_soup(self, url: str):

        req = Request(url, headers=REQ_HEADER )
        with urlopen(req) as urlClient:
            page = urlClient.read()

        return soup(page, "html.parser")

    def _scrape_images(self):
        list_of_image_data = []

        page = 1
        while len(list_of_image_data) < self.image_limit:
            print("Images found: " + str(len(list_of_image_data)))
            for template_url in self.urls:

                if len(self.urls) >= 1:
                    url = template_url.replace("<page>", str(page))
                else:
                    self.image_limit = 0 #get out of the while loop
                    break

                try:
                    site_content = self._get_soup(url)
                except Exception as e:
                    print(e)
                    self.urls.remove(template_url)
                    continue

                if "rule34" in url:

                    posts = site_content.find_all("div", {"class": "shm-thumb thumb"})
                    for post in posts:
                        image_dic = {"url": post.find_all("a")[1].get("href"),
                                    "title": post.get("data-post-id"),
                                    "extension": post.get("data-ext") }

                        list_of_image_data.append(image_dic)

                elif "danbooru" in url:

                    posts = site_content.find_all("div", {"id": "posts-container"})[0].find_all("article")
                    for post in posts:
                        image_dic = {"url": post.get("data-large-file-url"),
                                    "title": post.get("data-id"),
                                    "extension": post.get("data-file-ext") }

                        list_of_image_data.append(image_dic)

            page += 1

        images = str(len(list_of_image_data))
        print("Images found: " + images)
        for index, image in enumerate(list_of_image_data):
            print("[Downloading](" + str(index) + "/"+ images + ")" + image["url"])
            self._download_image(image["url"], image["title"], image["extension"])
            #break


    def _download_image(self, url: str, img_title:str, img_ext: str):
        req = Request(url=url, headers=REQ_HEADER)
        filename = join(self.path, img_title + "." + img_ext)

        try:

            with urlopen(req) as uClient:
                img_file = open(filename, "wb")
                img_file.write(uClient.read())
                img_file.close()

            print("[FINISHED] "+ img_title + "." + img_ext)

        except Exception as e:
            print(e)

tags=["cat_ears", "nude"]
Scraper().scrape_by_tags(tags=tags, image_limit=100)
##Scraper().update_tags()