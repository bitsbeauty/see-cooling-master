#!/usr/bin/python

import time
import paho.mqtt.client as mqtt
# import paho.mqtt.subscribe as subscribe
import json
import database as db
import string

# Define Variables
MQTT_BROKER = "seebier.local"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC_TEMP_RECEIVE = "/freezer/+/temperatures"
MQTT_TOPIC_SEND_TO_FREEZER = "/freezer/f*/setValues"
MQTT_TOPIC_ACKN = "/freezer/+/receivedMessage"

timeACKreceived =[0,0]


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print("Connected to MQTT Broker")
	print("Connected with result code "+str(rc))
	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	# client.subscribe("$SYS/#")
	mqttc.subscribe(MQTT_TOPIC_TEMP_RECEIVE,2)
	mqttc.subscribe(MQTT_TOPIC_ACKN,2)
	


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	print("--------------------------------------------RECEIVED:")
	# print(str(client)+" - "+str(userdata))
	print(msg.topic+" -- "+str(msg.payload))
	print " "

	topicSub = msg.topic.split("/",1)[1]
	
	if msg.topic.split("/")[3]  == MQTT_TOPIC_TEMP_RECEIVE.split("/")[3] :
		## RECEIVE TEMPS
		on_message_kuehlung(client, userdata, msg)

	if msg.topic.split("/")[3]  == MQTT_TOPIC_ACKN.split("/")[3] :
		## ACKNOLEDGE ----
		frezNr = int(msg.topic.partition('/freezer/f')[-1].rpartition('/')[0])
		print("ACKN:"+str(frezNr))
		if frezNr == 1:
			timeACKreceived[0] = time.time()
		elif frezNr == 2:
			timeACKreceived[1] = time.time()


def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_message_kuehlung(client, userdata, message):
	#print("%s %s" % (message.topic, message.payload))

	# get nr of the freezer which send the mesage
	dstr =  "###mqtt message### "  # Debug String
	frezNr = int(message.topic.partition('/freezer/f')[-1].rpartition('/')[0])
	dstr += ("frezzerNR: %s")%(frezNr)

	data = json.loads(message.payload)

	for key,value in data.iteritems():
		if key == 'beerTemp':
			dstr += "- beer:"+str(value)
			freezer[frezNr-1].temp_beer = value
		if key == 'airTemp':
			dstr += " - air:"+str(value)
			freezer[frezNr-1].temp_air = value

	dstr += " ###"
	#print dstr
	freezer[frezNr-1].write2db_temps()


freezer = [] # abstraction list of freezer

# Initiate MQTT Client
mqttc = mqtt.Client()


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
	
	# initialize freezer raay
	for i in range(len(db.Header.select())):
			# get headers			
			freezer.append(db.Freezer(i+1))
			freezer[i].updateValues()  # import data


	##### //// MQTT /////// ######
	#client = mqtt.Client()
	# client.on_connect = on_connect
	#client.on_message = on_message

	#client.connect("seebier.local", 1883, 60)

	#TODO: add QoS!!!
	# subscribe.callback(on_message_kuehlung, "/freezer/+/isValues", hostname=MQTT_BROKER)
	mqttc.on_message = on_message
	mqttc.on_connect = on_connect
	# mqttc.on_publish = on_publish
	# mqttc.on_subscribe = on_subscribe

	# Connect
	mqttc.connect(MQTT_BROKER)



	try:
		

		while True:
			print " "
			print("-START LOOP------------")
			mqttc.loop()

			for f in freezer:
				# 1) get the freezer temp and get last databse values
				f.updateValues()

				if f.isRunning() is True:
					print "----------FREEZER ["+ str(f.id) +"] started:"+str(f.isStarted) +" - runtimeEnded:"+str(f.runtimeEnded)
					# print "startime", frez.starttime
					print "Main Duration  :", f.overallRuntime
					print ("Runtime        : " + str(f.runtime) +" (" + f.getRuntimeStr() + ")" )
					print "Traget Duration:", f.getTargetDurationStr()


					# 2) get sollwert from database
					f.getTargetTemp()

					mqttMsg = {}
					# 3) compare temp values and set freezer on/off
					mqttMsg = {"relay": f.setRelay()}

					# 4) pack value sin json and send to freezer
					mqttMsg["targetTemp"] = str(f.temp_target)
					#mqttMsg["targetDurationStr"] = f.getTargetDurationStr()
					mqttMsg["runtimeStr"] = f.getRuntimeStr()
					# mqttMsg["leftRuntimeStr"] = f.getLeftRuntimeStr()
					
					mqttMsg = json.dumps(mqttMsg, separators=(',',':'))
					print "JSON1: "+ mqttMsg

					## SEND FIRST MSG
					mqttTopic = string.replace(MQTT_TOPIC_SEND_TO_FREEZER, "*", str(f.id))
					mqttc.publish(mqttTopic, mqttMsg, 2)

					# mqttMsg = {}
					# mqttMsg["targetDurationStr"] = f.getTargetDurationStr()
					# mqttMsg = json.dumps(mqttMsg, separators=(',',':'))
					# print "JSON2: "+ mqttMsg
					# mqttc.publish(mqttTopic, mqttMsg, 2)

					## TODO: when freezer mqtt com is down -> give signal!!
					
				else:
					print "----------FREEZER ["+ str(f.id) +"] started:"+str(f.isStarted) +" - runtimeEnded:"+str(f.runtimeEnded)

					# 1) look if system is still running (then hold certain temp)
					#TODO

					# 2) send mqtt message
					mqttMsg = {"relay": "0"}
					mqttMsg["targetTemp"] = str(f.temp_target)
					mqttMsg["targetDurationStr"] = f.getTargetDurationStr()
					mqttMsg["runtimeStr"] = f.getRuntimeStr() # is = ENDED when programm has no more targetTemps to go
					
					mqttMsg = json.dumps(mqttMsg, separators=(',',':'))

					mqttTopic = string.replace(MQTT_TOPIC_SEND_TO_FREEZER, "*", str(f.id))
					mqttc.publish(mqttTopic, mqttMsg, 2)
					


			



			# check if temp is t




			time.sleep(0.9)

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
		mqttc.loop_stop()

	# ---------------------------------------------------------------



