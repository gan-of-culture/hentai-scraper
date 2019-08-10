from urllib.request import urlopen, Request, urlretrieve
from os.path import join, dirname, realpath
from os import getcwd
from bs4 import BeautifulSoup as soup
from sys import exit

REQ_HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}

class Scraper:
    def __init__(self, tags: list=None, path: str=join(dirname(realpath(__file__)), "images"),image_limit: int=1, url: str=None):
        self.RULE34_URL = "http://rule34.paheal.net/post/list/"
        self.DANBOORU_URL = "https://danbooru.donmai.us/posts?utf8=true;&page=<page>&ms=1&tags="


        self.tags = tags
        self.path = path
        self.image_limit = image_limit
        self.urls = []

        if url is not None:
            self.urls.append(url)

        #only scrape the one url
        if url is not None:
            self.image_limit = 1

        #create url of passed tags
        if url is None:
            if self.tags is None:
                exit("Parameter error")
            else:
                tag_url = self.tags[0]
                for tag in self.tags[1:]:
                    tag_url = tag_url + "%20" + tag
                self.urls.append(self.RULE34_URL + tag_url + "/<page>")

                tag_url = self.tags[0]
                for tag in self.tags[1:]:
                    tag_url = tag_url + "+" + tag
                self.urls.append(self.DANBOORU_URL + tag_url)

        self._scrape_images()

    def _get_soup(self, url: str):

        req = Request(url, headers=REQ_HEADER )
        with urlopen(req) as urlClient:
            page = urlClient.read()

        return soup(page, "html.parser")

    def _scrape_images(self):
        list_of_image_data = []

        page = 1
        while len(list_of_image_data) < self.image_limit:
            for url in self.urls:
            
                if len(self.urls) >= 1:
                    url = url.replace("<page>", str(page))
                    print(url)

                try:
                    site_content = self._get_soup(url)
                except Exception as e:
                    print(e)
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

tags=["cat_tail", "nude"]
Scraper(tags=tags, image_limit=500)