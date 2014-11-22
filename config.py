import os
import platform
import sys

DEBUG = True
SQLALCHEMY_ECHO = False

if DEBUG and platform.system() == 'Linux':
    cwd = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(cwd, "ebooks.db")
    STORAGE_DIR = os.path.join(cwd, "books")
else:
    SQLALCHEMY_DATABASE_URI = "sqlite:///D:\project\ebook\ebooks.db"
    STORAGE_DIR = r"D:\project\ebook\books"
