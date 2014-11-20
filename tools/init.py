# -*- coding:utf-8 -*-
from basemain import db, app


def init_db():
    import models

    db.create_all()


def build_db():
    msg = u"初始化开始, 数据库是: " + app.config["SQLALCHEMY_DATABASE_URI"]
    app.logger.info(msg)
    import os

    dbstr = app.config["SQLALCHEMY_DATABASE_URI"]
    if dbstr.startswith("sqlite"):
        dir = os.path.split(dbstr[10:])[0]
    if dir and not os.path.exists(dir):
        os.makedirs(dir)
    db.drop_all()
    init_db()

if __name__ == "__main__":
    build_db()