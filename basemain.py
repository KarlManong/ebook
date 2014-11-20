# -*- coding:utf-8 -*-
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask("eBooks")
db = SQLAlchemy(app)


def config():
    app.config.from_object("config")
    import index

config()

