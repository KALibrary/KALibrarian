import os
import datetime
import sqlalchemy
from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = sqlalchemy.create_engine('sqlite:///kalibrary.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


association_table = Table('association', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('transaction_id', Integer, ForeignKey('transactions.id'))
)


class Book(Base):
    __tablename__ = 'books'

    id = Column(String, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collections.id'))
    title = Column(String)
    author = Column(String)
    collection = relationship("Collection", back_populates="collections")
    transactions = relationship(
        "Transaction",
        secondary=association_table,
        back_populates="books")

    def __repr__(self):
        return "<Book(title={}, author={}, collection={}>".format(
            self.title, self.author, self.collection)


class Collection(Base):
    __tablename__ = 'collections'
    __table_args__ = {'sqlite_autoincrement': True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)
    books = relationship("Book", back_populates="collections")

    def __repr__(self):
        return "<Collection(name={}, location={}>".format(
            self.name, self.location)


class Transaction(Base):
    __tablename__ = 'transactions'
    __table_args__ = {'sqlite_autoincrement': True}

    id = Column(Integer, primary_key=True)
    slack_user_id = Column(String)
    type = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    due_date = Column(DateTime)
    status = Column(String)
    books = relationship(
        "Book",
        secondary=association_table,
        back_populates="transactions")

    def __repr__(self):
        return "<Transaction(type={}, user={}, book={}>".format(
            self.type, self.slack_user_id, self.book_id)


if __name__ == "__main__":
    pass
