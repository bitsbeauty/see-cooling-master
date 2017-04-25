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



def formatDurationStr( _s):
		#return str(datetime.timedelta(seconds=_s))
		hours = _s % 86400 // 3600
		return '{:02d}day {:02d}:{:02d}:{:02d}'.format(int(_s // 86400), int(hours), int(_s % 3600 // 60), int(_s % 60))


class Freezer():
	"""docstring for Freezer"""
	id = None   #  first starts with 1 !!!
	starttime = None

	temp_air = 0.0
	temp_beer = 0.0
	temp_target = None
	lastTempTarget = 0.0

	steps = {} # # type dictonary,

	overallRuntime = 0   # maximal time to run from start to end
	runtime = 0			 # time how long the system is started
	isStarted = False
	targetDuration = 0
	runtimeEnded = False
	fermentationProgramMode = 0 # 0=stopped; 1=running; 2=ended

	relayStatus = 0;

	def __init__(self, _id):
		self.id = _id

	def save(self):
		# h.starttime = self.starttime
		# h.temp_air = self.temp_air
		# h.temp_beer = self.temp_beer
		# h.temp_target = self.temp_target

		q = Header.update(starttime = self.starttime,
			temp_air = self.temp_air,
			temp_beer = self.temp_beer,
			temp_target = self.temp_target).where(Header.id == (self.id))
		q.execute()  # Execute the query, updating the database.

	def write2db_temps(self):
		q = Header.update(
			temp_air = self.temp_air,
			temp_beer = self.temp_beer).where(Header.id == (self.id))
		q.execute()  # Execute the query, updating the database.

	def updateValues(self):
		'import values from he database'

		# print "UPDATE VALUES - freezer:"+str(self.id)

		h = Header.get(Header.id == (self.id))
		self.starttime = h.starttime
		self.temp_air = h.temp_air
		self.temp_beer = h.temp_beer
		self.temp_target = h.temp_target

		# get Steps
		self.steps = Steps.select().where(Steps.tank_id == self.id).dicts()

		# get step Master Values
		self.overallRuntime = 0
		for s in self.steps:
			self.overallRuntime += s["step_duration"]
			self.lastTempTarget = s["step_temperature"]

			#print "update: step" + str(s["step_duration"]) + " - " + str(self.overallRuntime)
		#print "OVERALL: " + str(self.overallRuntime)

		if self.starttime != None:
			self.runtime = time.time() - self.starttime #update runtime

		self.isRunning()
		self.getTargetTemp() # update target value

	def isRunning(self):
		print "isRuning()? - freezer:"+str(self.id)
		print "- runtime:"+str(self.runtime)
		print "- overallRuntime:"+str(self.overallRuntime)

		if self.starttime != None and self.starttime != 0:
			if (self.runtime <= self.overallRuntime):
				# fermenttaion is running
				self.isStarted = True
				self.runtimeEnded = False
				self.fermentationProgramMode = 1
				print "- is running"
				return True
			else:
				# Fermaentation ended!!!
				print "- time ended"
				# print "- runtime:"+str(self.runtime)
				# print "- overallRuntime:"+str(self.overallRuntime)

				self.isStarted = True
				self.runtimeEnded = True
				self.fermentationProgramMode = 2
				return False
		else:
			# Fermentation stopped
			print "- was stopped"
			self.isStarted = False
			self.runtimeEnded = False
			self.fermentationProgramMode = 0
			return False

	def getTargetTemp(self):
		'gets the target temp and targetTempDuration - chek if freezer is running first!'

		if self.fermentationProgramMode == 0:
			# system stopped from inteface
			self.temp_target = None

		elif self.fermentationProgramMode == 1:
			# system is Running
			_stepSum = 0
			_lastStepSum = 0
			for step in self.steps:
				# # DEBUG			
				# steppstr = ""
				# for smeta in step:
				# 	# stepp = stepp + str(sname)
				# 	steppstr += str(smeta)+': '+str(step[smeta]) + ' - '
				# print steppstr

				# check if runtime is in this step
				_stepSum += step["step_duration"]
				if self.runtime > _lastStepSum and self.runtime <= _stepSum:
					# print("last= %f < runtime=%f < _stepSum=%f") % (_lastStepSum, self.runtime, _stepSum)
					self.temp_target = step["step_temperature"]
					self.targetDuration = _stepSum - self.runtime
					# print "-> TARGET TEMP =", self.temp_target
					break
				#else:
					# print("last= %f < runtime=%f < _stepSum=%f") % (_lastStepSum, self.runtime, _stepSum)

				_lastStepSum = _stepSum

		elif self.fermentationProgramMode == 2:
			# fermentaton program ended - keep last target Temp
			self.temp_target = self.lastTempTarget #lastTempTarget is updtated in update()



	def setRelay(self):
		r = 0
		if self.temp_beer <= (self.temp_target):
			# turn of cooling, temp is reached
			r = 0
		else:
			# turn on relay to cool down
			r = 1

		if r != self.relayStatus:
			self.relayStatus = r

		return self.relayStatus


	def getRuntimeStr(self):
		'time how long program is running since started'

		if self.isStarted == True and self.runtimeEnded == False:
			return str(formatDurationStr(time.time()-self.starttime))

		elif self.isStarted == True and self.runtimeEnded == True:
			return "System ENDED!  "
		
		elif self.isStarted == False:
			return "System STOPPED!"

	def getLeftRuntimeStr(self):
		'left time how long the whole programm will run (overallRuntime - runtime)'

		if self.isStarted == True and self.runtimeEnded == False:
			return str(formatDurationStr(self.overallRuntime-(time.time()-self.starttime)))

		elif self.isStarted == True and self.runtimeEnded == True:
			return "FERMENTAT. END!"
		
		elif self.isStarted == False:
			return "System STOPPED!"


	def getTargetDurationStr(self):
		'time left how long will keep actual target duration'

		if self.isStarted == True and self.runtimeEnded == False:
			return "-"+str(formatDurationStr(self.targetDuration))
		elif self.isStarted == True and self.runtimeEnded == True:
			return "System ENDED!  "
		elif self.isStarted == False:
			return "System STOPPED!"




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
