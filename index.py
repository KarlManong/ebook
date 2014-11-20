from flask import render_template
import requests
import threading
import os
from contextlib import closing
from basemain import app

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0"

BASE_URI = "http://it-ebooks-api.info/v1/"
ERROR_STR = "Error"


@app.route('/')
def hello_world():
    A = type("TestClass", (object,), {"a": lambda self: "123"})
    return render_template("index.html", test="123", a=A())


@app.route("/search")
@app.route("/search/<string:query>")
def search_page(query=None):
    if query:
        s = set()
        search(s, query)
        if s:
            storage(query, s)
            return str(s)
        return ""
    return ""


def storage(query, book_ids):
    from basemain import db
    import models

    books = []
    for id_ in book_ids:
        book = get_book(id_)
        books.append(book)

    tags = query.split(" ")
    for tag_str in tags:
        tag = models.Tag.query.filter_by(tag=tag_str).one()
        if not tag:
            tag = models.Tag(tag=query)
            db.session.add(tag)
        for book in books:
            if tag not in book.tags:
                book.tags.append(tag)

    db.session.commit()


class BookCatcher(threading.Thread):
    def __init__(self, book_ids, *args, **kwargs):
        threading.Thread.__init__(daemon=True, *args, **kwargs)
        self.bookIds = book_ids

    def run(self):
        for id_ in self.bookIds:
            pass


def search(set_, query_str, page=1):
    assert query_str is not None
    response = requests.get(BASE_URI + "/search/" + query_str + "/page/" + str(page))
    if response.status_code == 200:
        result = response.json()
        if result[ERROR_STR] == "0":
            for book in result["Books"]:
                set_.add(book["ID"])
            total = int(result["Total"])
            if total > page + 10:
                page += 10
                search(set_, query_str, page)
        else:
            print(result[ERROR_STR])
    else:
        print(response.status_code)


@app.route("/books/")
@app.route("/books/<int:id_>")
def books(id_=None):
    if id_:
        return fetch(id_)
    return ""


def download_file(url_):
    with closing(requests.get(url_, stream=True, headers={"referer": "	http://it-ebooks.info/book/386/",
                                                          "User-Agent": USER_AGENT})) as response:
        if response.status_code == 200:
            file_name = get_file_name(response)
            print("开始下载文件" + file_name)
            file_path = os.path.join(build_download_dir(), file_name)
            with open(file_path, "wb") as f:
                for idx, chunk in enumerate(response.iter_content(chunk_size=1024)):
                    if chunk:  # filter out keep-alive new chunks
                        print("已下载{}KB".format(idx))
                        f.write(chunk)
                        f.flush()
            return file_path


def build_download_dir():
    from basemain import app

    dir_ = app.config["STORAGE_DIR"]
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    return dir_


def get_file_name(response):
    return response.headers["Content-Disposition"].split("filename=")[-1][1:-1]


def fetch(book_id):
    assert book_id is not None
    response = requests.get(BASE_URI + "/book/" + str(book_id))
    if response.status_code == 200:
        result = response.json()
        if result[ERROR_STR] == "0":
            print(result["Download"])
            file_path = download_file(result["Download"])
            if file_path:
                book = get_book(book_id)
                book.title = result["Title"]
                book.sub_title = result["SubTitle"]
                book.image_path = result["Image"]
                book.file_path = file_path
                book.ISBN = result["ISBN"]
                update_book(book)
                return book.title
            else:
                return "下载失败"
        return result[ERROR_STR]
    return response.text, response.status_code


def get_book(book_id):
    import models
    from basemain import db

    book = models.BookModel.query.filter_by(eBook_id=book_id).one()
    if not book:
        book = models.BookModel(eBook_id=book_id)
        db.session.add(book)
        db.session.commit()
    return book


def update_book(book):
    from basemain import db

    db.session.add(book)
    db.session.commit()


