import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

import psycopg2
import urlparse

Base = declarative_base()
##Config Ends##
class User(Base):
	__tablename__='user'
	name = Column(String(40),nullable=False)
	id = Column(Integer,primary_key = True)
	picture = Column(String(200))
	email = Column(String(100),nullable=False)
	pollItems = relationship("Poll",cascade="all, delete-orphan")

class  Poll(Base):
	__tablename__= 'poll'
	name = Column(String(80),nullable= False)
	id = Column(Integer, primary_key = True)
	opItems = relationship("Option",cascade="all, delete-orphan")
 	vtItems = relationship("Votes",cascade="all, delete-orphan")
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	@property
	def serialize(self):
		return {
		'name' : self.name,
		'id' : self.id,
		}

class Option(Base):
	__tablename__='option'
	name = Column(String(80),nullable= False)
	id = Column(Integer, primary_key = True)
	poll_id = Column(Integer, ForeignKey('poll.id'))
	poll = relationship(Poll)

class Votes(Base):
	__tablename__='votes'
   	id = Column(Integer, primary_key = True)
   	poll_id = Column(Integer, ForeignKey('poll.id'))
	option_id = Column(Integer, ForeignKey('option.id'))
     	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
 	ip = Column(String(100))

##END OF FILE##
engine = create_engine('postgres://mjugseuryqvrac:XUnNTExgmDoIYV3Ef1wBnvaPtM@ec2-54-243-201-58.compute-1.amazonaws.com:5432/dc033pbqf9kspd')

Base.metadata.create_all(engine)
