# -*- coding:utf-8 -*-
from basemain import db

tag_and_books = db.Table("TB_TAG_BOOK", db.Column("tag_id", db.Integer, db.ForeignKey("TB_TAG.id")),
                         db.Column("book_id", db.Integer, db.ForeignKey("TB_BOOK.id")))


class BookModel(db.Model):
    __tablename__ = "TB_BOOK"

    id = db.Column(db.Integer, primary_key=True)
    eBook_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(256))
    sub_title = db.Column(db.String(256))
    ISBN = db.Column(db.String(256))
    image_path = db.Column(db.String(256))
    file_path = db.Column(db.String(512))
    tags = db.relationship("Tag", secondary=tag_and_books)


class Tag(db.Model):
    __tablename__ = "TB_TAG"

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(64))
