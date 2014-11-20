# -*- coding:utf-8 -*-
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import logging

app = Flask("eBooks")
db = SQLAlchemy(app)

from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(filename="ebooks.log")
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

def config():
    app.config.from_object("config")
    import index

config()

