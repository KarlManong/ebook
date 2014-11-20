from flask import render_template
import requests
import threading
import os
from contextlib import closing
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

from basemain import app

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0"

BASE_URI = "http://it-ebooks-api.info/v1/"
ERROR_STR = "Error"

semaphore = threading.BoundedSemaphore()


@app.route('/')
def hello_world():
    A = type("TestClass", (object,), {"a": lambda self: "123"})
    return render_template("index.html", test="123", a=A())


@app.route("/search")
@app.route("/search/<string:query>")
def search_page(query=None):
    # TODO 提供的api分页有问题，所以需要重新抓取
    if query:
        s = set()
        search(s, query)
        if s:
            storage(query, s)
            BookCatcher(s).start()
            return str(s)
        return ""
    return ""


def storage(query, book_ids):
    from basemain import db
    import models

    books = []
    for id_ in book_ids:
        book = get_book(id_, True)
        books.append(book)

    tags = query.split(" ")
    for tag_str in tags:
        try:
            tag = models.Tag.query.filter_by(tag=tag_str).one()
        except NoResultFound:
            tag = models.Tag(tag=query)
            db.session.add(tag)
        for book in books:
            if tag not in book.tags:
                book.tags.append(tag)

    db.session.commit()


class BookCatcher(threading.Thread):
    def __init__(self, book_ids, *args, **kwargs):
        threading.Thread.__init__(self, daemon=True, *args, **kwargs)
        self.book_ids = book_ids

    def run(self):
        semaphore.acquire(timeout=100)
        app.logger.info(threading.currentThread().getName() + "开始运行， 一共%d本书", len(self.book_ids))
        for book_id in self.book_ids:
            fetch(book_id)
        app.logger.info(threading.currentThread().getName() + "运行结束")
        semaphore.release()


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
        if fetch(id_):
            return id_
    return "error", 400


def get_file_size(response):
    return int(response.headers.get("Content-Length", 0))


def write_file_from_response(file_path, response):
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()


def filename_fix_existing(filename):
    """Expands name portion of filename with numeric ' (x)' suffix to
    return filename that doesn't exist already.
    """
    dirname = '.'
    name, ext = filename.rsplit('.', 1)
    names = [x for x in os.listdir(dirname) if x.startswith(name)]
    names = [x.rsplit('.', 1)[0] for x in names]
    suffixes = [x.replace(name, '') for x in names]
    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes
                if x.startswith(' (') and x.endswith(')')]
    indexes = [int(x) for x in suffixes
               if set(x) <= set('0123456789')]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return '%s (%d).%s' % (name, idx, ext)


def download_file(url_):
    with closing(requests.get(url_, stream=True, headers={"referer": "	http://it-ebooks.info/book/386/",
                                                          "User-Agent": USER_AGENT})) as response:
        if response.status_code == 200:
            file_name = get_file_name(response)
            file_size = get_file_size(response)

            file_path = os.path.join(download_dir(), file_name)
            if os.path.exists(file_path) and os.path.getsize(file_path) == file_size:
                return file_path
            app.logger.info(threading.current_thread().getName() + "开始下载文件%s，保存为%s，一共%dKB", url_, file_name,
                            file_size // 1024)
            try:
                write_file_from_response(file_path, response)
            except IOError:
                file_path = filename_fix_existing(file_path)
                write_file_from_response(file_path, response)

            if file_size:
                if os.path.getsize(file_path) == file_size:
                    app.logger.info("下载%s完成", file_name)
                    return file_path
                else:
                    os.unlink(file_path)


def download_dir():
    from basemain import app

    dir_ = app.config["STORAGE_DIR"]
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    return dir_


def get_file_name(response):
    def hash_name():
        from hashlib import md5
        import time

        return md5(str(time.time()).encode()).hexdigest() + ".pdf"

    file_name = response.headers.get("Content-Disposition", hash_name()).split("filename=")[-1][1:-1]
    for char in "/\\,:<>|*?":
        if char in file_name:
            file_name = file_name.replace(char, "-")
    if len(file_name) >= 255:
        _name, suffix = os.path.splitext(file_name)
        file_name = _name[:-len(suffix) - 10] + "..." + suffix
    return file_name


def fetch(book_id):
    assert book_id is not None
    book = get_book(book_id)
    if book.file_path and os.path.exists(book.file_path):
        return True
    response = requests.get(BASE_URI + "/book/" + str(book.eBook_id))
    if response.status_code == 200:
        result = response.json()
        if result[ERROR_STR] == "0":
            file_path = download_file(result["Download"])
            if file_path:
                book.title = result["Title"]
                book.sub_title = result["SubTitle"]
                book.image_path = result["Image"]
                book.file_path = os.path.relpath(file_path, download_dir())
                book.ISBN = result["ISBN"]
                update_book(book)
                return True
            else:
                app.logger.error(threading.currentThread().getName() + "下载失败" + str(book.title))
    return False


def get_book(book_id, create=False):
    import models
    from basemain import db

    try:
        book = models.BookModel.query.filter_by(eBook_id=book_id).one()
        return book

    except NoResultFound:
        if create:
            book = models.BookModel(eBook_id=book_id)
            db.session.add(book)
            db.session.commit()
            return book
    return None

def update_book(book):
    from basemain import db

    db.session.add(book)
    db.session.commit()


@app.route("/downloads")
def download_files():
    import models

    books = models.BookModel.query.filter(
        or_(models.BookModel.file_path == None, models.BookModel.file_path == "")).all()
    book_ids = [book.id for book in books]
    BookCatcher(book_ids).start()
    return str(book_ids)