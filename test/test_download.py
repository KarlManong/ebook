# -*- coding:utf-8 -*-
import requests


def download(url_):
    response = requests.get(url_, headers={"referer": "	http://it-ebooks.info/book/385/"}, stream=True)
    if response.status_code == 200:
        pass


if __name__ == "__main__":
    download("http://filepi.com/i/2NhKxEj")
