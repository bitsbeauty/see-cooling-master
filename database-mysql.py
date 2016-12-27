#!/usr/bin/python

from peewee import *

db = MySQLDatabase('seebier', user='root',passwd='seelandtraum')

class UnknownField(object):
	def __init__(self, *_, **__): pass

class BaseModel(Model):
	class Meta:
		database = db

class Freezer(BaseModel):
	starttime = IntegerField(null=True)
	temp_air = DecimalField(null=True)
	temp_beer = DecimalField(null=True)
	temp_target = DecimalField(null=True)

	steps = [] # steps.append()
	class Meta:
		db_table = 'header'

class Steps(BaseModel):
	step_duration = IntegerField()
	step_temperature = DecimalField()
	tank = IntegerField(db_column='tank_id')

	class Meta:
		db_table = 'steps'




# ---------------------------------------------------------------
if __name__ == '__main__':
	db.connect()

	step = Steps.select().where(Steps.tank == 1)



	f = Freezer.select()


	# query = Pet.select().where(Pet.animal_type == 'cat')

	#for frez in f:
	#print "id: %i, start:%i, beer: %f, air:%f" % (frez.id, frez.starttime, frez.temp_beer, frez.temp_air)
	#print frez.id, frez.starttime, frez.temp_beer, frez.temp_air
	#Freezer

	for frez1steps in step:
		print frez1steps.tank, frez1steps.step_duration, frez1steps.step_temperature


	db.close()




# import MySQLdb

# # Open database connection
# db = MySQLdb.connect("localhost","root","seelandtraum","seebier" )

# # prepare a cursor object using cursor() method
# cursor = db.cursor()

# # execute SQL query using execute() method.
# cursor.execute("SELECT VERSION()")

# # Fetch a single row using fetchone() method.
# data = cursor.fetchone()

# print "Database version : %s " % data

# # disconnect from server
# db.close()
