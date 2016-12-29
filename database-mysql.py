#!/usr/bin/python
import time, datetime
from peewee import *

db = MySQLDatabase('seebier', user='root', passwd='seelandtraum')

class UnknownField(object):
	def __init__(self, *_, **__): pass

class BaseModel(Model):
	class Meta:
		database = db

class Header(BaseModel):
	starttime = IntegerField(null=True)
	temp_air = DecimalField(null=True)
	temp_beer = DecimalField(null=True)
	temp_target = DecimalField(null=True)

	class Meta:
		db_table = 'header'

class Steps(BaseModel):
	step_duration = IntegerField()
	step_temperature = DecimalField()
	tank_id = IntegerField()
	# tank = IntegerField(db_column='tank_id')

	class Meta:
		db_table = 'steps'




class Freezer():
	"""docstring for Freezer"""
	id = None   #  first starts with 1 !!!
	starttime = None
	temp_air = 0.0
	temp_beer = 0.0
	temp_target = 0.0

	steps = {} # # type dictonary,

	overallRuntime = 0   # maximal time to run from start to end
	runtime = 0			 # time how long the system is started

	def __init__(self, _id):
		self.id = _id

	def updateValues(self):
		# get steps
		try:  
			db.connect()
		except:  
			# this catches ALL other exceptions including errors.  
			# You won't get any error messages for debugging  
			# so only use it once your code is working
			import traceback
			print traceback.format_exc()
			print "Other error or exception occurred!"  

		h = Header.get(Header.id == self.id)
		self.starttime = h.starttime
		self.temp_air = h.temp_air
		self.temp_beer = h.temp_beer
		self.temp_target = h.temp_target

		# get Steps
		self.steps = Steps.select().where(Steps.tank_id == self.id).dicts()
		# print "Updated Freezer --> ",self.id

		db.close()

		# get step Master Values
		for s in self.steps:
			self.overallRuntime += s["step_duration"]

	def isStarted(self):
		if self.starttime != None:
			# print "--ist started"
			return True
		else:
			# print "-- stopped"
			return False

	def updateRuntime(self):
		if self.starttime != None:
			self.runtime = time.time() - self.starttime
		else:
			self.runtime = None
		return self.runtime

	def getDurationStr(self):
		if frez.runtime != None:
			value = datetime.datetime.fromtimestamp(frez.runtime)
			# print("DURATION: ",value.strftime('%Y-%m-%d %H:%M:%S'))
			# print("DURATION: ",value.strftime('%d %H:%M:%S'))

			return datetime.datetime.now() - value
		else:
			return "---"



# ---------------------------------------------------------------
if __name__ == '__main__':

	try:  
		db.connect()
	except:  
		# this catches ALL other exceptions including errors.  
		# You won't get any error messages for debugging  
		# so only use it once your code is working
		import traceback
		print traceback.format_exc()
		#print "Other error or exception occurred!"  


	############ LOAD AVLUES ##################
	# f = Header.select()
	f = [] # type list
	for i in range(len(Header.select())):
			# get headers
			id = i+1
			
			f.append(Freezer(i+1))
			f[i].updateValues()

	# step = Steps.select().where(Steps.tank_id == 1)
	# query = Pet.select().where(Pet.animal_type == 'cat')


	# DEBUG VALUES
	for frez in f:
		print "----------FREEZER ["+ str(frez.id) +"] started:"+str(frez.isStarted())
		# print "startime", frez.starttime
		print "All Runtime:", frez.overallRuntime
		print "RUNNING:", frez.updateRuntime()
		print "DURATION", frez.getDurationStr()
		
		# print "---",frez.steps.tank_id, frez.steps.step_duration, frez.steps.step_temperature
		for s in frez.steps:
			stepp = ""
			for sname in s:
				# stepp = stepp + str(sname)
				stepp += str(sname)+': '+str(s[sname]) + ' - '
			print stepp

	#print "id: %i, start:%i, beer: %f, air:%f" % (frez.id, frez.starttime, frez.temp_beer, frez.temp_air)
	#print frez.id, frez.starttime, frez.temp_beer, frez.temp_air
	#Freezer

	# for frez1steps in step:
	# 	print frez1steps.tank_id, frez1steps.step_duration, frez1steps.step_temperature


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
