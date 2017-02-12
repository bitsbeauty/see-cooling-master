#!/usr/bin/python

import time
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import json
import database as db

# Define Variables
MQTT_BROKER = "seebier.local"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "/kuehlung/setTemp/kuehlung1"
MQTT_MSG = "yes, Hello MQTT - Daniel, you did that!"



# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print("Connected with result code "+str(rc))

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	print(str(client)+" - "+str(userdata))
	print(msg.topic+" -- "+str(msg.payload))




def on_message_kuehlung(client, userdata, message):
	#print("%s %s" % (message.topic, message.payload))

	# get nr of the freezer which send the mesage
	frezNr = int(message.topic.partition('/freezer/f')[-1].rpartition('/')[0])
	print("frezzerNR: %s")%(frezNr)

	data = json.loads(message.payload)

	for key,value in data.iteritems():
		if key == 'tempbeer':
			print "beer:"+str(value)
			f[frezNr].temp_beer = value
			## TODO PUT INTO mysql database
		if key == 'tempair':
			print "air:"+str(value)
			## TODO PUT INTO mysql database
			f[frezNr].temp_air = value

	f[frezNr].save()


f = [] # abstraction list of freezer

# ---------------------------------------------------------------
if __name__ == '__main__':

	###### //// MYSQL  /////// ######
	try:  
		db.db.connect()
		print "database connected"
	except:  
		# this catches ALL other exceptions including errors.  
		# You won't get any error messages for debugging  
		# so only use it once your code is working
		import traceback
		print traceback.format_exc()
		#print "Other error or exception occurred!"  


	############ LOAD AVLUES ##################
	# f = Header.select()
	
	for i in range(len(db.Header.select())):
			# get headers
			id = i+1
			
			f.append(db.Freezer(i+1))
			f[i].updateValues()  # import data


	##### //// MQTT /////// ######
	#client = mqtt.Client()
	# client.on_connect = on_connect
	#client.on_message = on_message

	#client.connect("seebier.local", 1883, 60)

	print "BEFORE"
	#TODO: add QoS!!!
	subscribe.callback(on_message_kuehlung, "/freezer/+/isValues", hostname=MQTT_BROKER)
	print "AFTER"


	try:

		while True:
			# 1) get the freezer temp and updtae in database
			
			f[0].updateValues()
			if f[0].isStarted() is True:
				print("Freezer %i is Started") %(f[0].id)

				print("Freezer Duration %i") %(f[0].getDurationStr())


			# check if temp is t




			time.sleep(0.3)

	except:  
		# this catches ALL other exceptions including errors.  
		# You won't get any error messages for debugging  
		# so only use it once your code is working
		import traceback
		print traceback.format_exc()
		#print "Other error or exception occurred!"  
	  
	finally:
		print "---CLEANUP:"
		
		db.db.close()
		

	# ---------------------------------------------------------------



