#!/usr/bin/python
#(C) Copyright Juan Antonio Nache Ramos. 2008-2013
#Under GPL License

import socket
import select
import re
import sys
from time import sleep
import MySQLdb

class naNbotDB:
	def __init__(self):
		print ("[+] Starting DB...")
		self.db=MySQLdb.connect(host='localhost',user='naNbot85',
			passwd='naNbot85',db='naNbot85')
		self.cursor=self.db.cursor()

	def query(self,query):
		print ("[i] DB exec query: %s" % query)
		try:
			ret = self.cursor.execute(query)
		except:
			self.db.rollback()
			raise #uncomment for debug
			ret = -1

		return ret

	def fetchall(self):
		return self.cursor.fetchall()

class naNbotWorker:
	def __init__(self):
		print("[+] Starting worker..")
		self.cache=[] #definimos la cache de todos los datos encontrados, mas tarde procesaremos todo
		self.maxLenCache = 2
		self.DB=naNbotDB()

	###
	def foundLinks(self,msg):
		self.cache.append(msg)
		if len(self.cache) > self.maxLenCache:
			self.unpackCache()	

	def unpackCache(self):
		for msg in self.cache:
			links = msg[3:].split(" ") #3 first words out ("EN ") and links to array
			if len(links) > 1: # >1 because first is the host and next the links
				self.processLinks(links)

	def processLinks(self,links):
		host = links.pop(0) #extract host (first element)
		for link in links:
			# TODO here we clean the link
			# TODO insert only if link does not exist
			self.DB.query("insert into enlaces (url,urlorigen) values ('"+link+"','"+host+"')")
			#enlace=enlace.replace("'","%27")
			#enlace=enlace.replace("\'","%27")
			#enlace=enlace.replace("//","/")
			#enlace=enlace.replace("///","/")
			#enlace=enlace.replace("////","/")
			#enlace=enlace.replace("http:/","http://")

	###
	def foundDownloads(self,msg):
		downs = msg[3:].split(" ")
		if downs > 1:
			self.processDownloads(downs)
			
	def processDownloads(self,downs):
		host = downs.pop(0)
		for down in downs:
			# TODO do it only if down dows not exist
			self.DB.query("insert into descargas (url,origen)",
					" values ('"+descarga+"','"+host+"')")


	###
	def getLink(self):
		if self.DB.query("select url from enlaces order by explorado asc limit 1") >= 1:
			result = self.DB.fetchall()
			self.DB.query("update enlaces set explorado=explorado+1"
					" where url='"+result[0][0]+"'")
			return str(result[0][0])
		else:
			return "http://localhost" #TODO or maybe WAIT

	
"""
This would be download also
"""
#	def guarda_mime(msg):
#	global cursor
#	try:
#		print "Descarga encontrada"
#		mime=msg[3:].split(" ")
#		descarga=mime.pop(0)
#		mimetype=mime.pop(0)
#		cursor.execute("insert into descargas (url,mimetype)"
#		" values ('"+descarga+"','"+mimetype+"')")
#	except:
#		print "No se Guardo la descarga con mimetype"

class naNbotMain:
	def __init__(self):
		print ("[i] Opening sockets..")
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try: #try port 8510
			self.server.bind(("", 8510))
			print "[i] Bind port: 8510"
		except:#try port 8511
			self.server.bind(("", 8511))
			print "[i] Bind port: 8511"

		self.server.listen(999) #max connections
		self.desc = [self.server] #store the server sock first, necesary?
		self.IA=naNbotIA()

	def mainLoop(self):
		while 1:
			self.waitcnx() #wait microsec for new conections
			self.forSocks()
	
	def forSocks(self):
		(sread, swrite, sexc) = select.select(self.desc, [], [])
		for sock in sread:
			if sock != self.server:
				self.readSock(sock)

	def readSock(self,sock):
		
		msg=sock.recv(1024)
		sock.settimeout(.1) #necesary?
		if msg == "quit": #if client want to quit
			sock.send("quit") #confirm to client
			self.desc.remove(sock) #delete from list
		else:
			sock.send( self.IA.msgClient(msg) ) #send response to client
	#	except:
	#		print ("Client out") #maybe not... review this
	#		self.desc.remove(sock)

	def waitcnx(self):
		try:
			newsock, (remhost, remport) = self.server.accept()
			self.server.settimeout(.1)
			print ("Ahaha! Nuevo cliente: %s:%s" % 
					(str(remhost), str(remport)))
			self.desc.append(newsock)
		except:
			pass


class naNbotIA:
	def __init__(self):
		print ("[+] Starting IA 1+1=3...")
		self.worker = naNbotWorker()


	def msgClient(self,msg):
		print "MSG", msg
		#client found links
		if   msg[:2] == "EN":
			self.worker.foundLinks(msg)
			return "OK"


		#client found downloads
		elif msg[:2] == "DE": 
			self.worker.foundDownloads(msg)
			return "OK"


		#client ask what to do
		elif msg[:2] == "Q?":
			return self.worker.getLink()


		#client ask if we are ready
		elif msg[:2] == "RD":
			return "OK" 
			"""
			TODO Now always yes
			Add flow contro in a future
			"""

		#dont know yet
		elif msg[:2] == "MI":
			guarda_mime(msg)
			return "OK"


		#default option
		else:
			print "Algo extranio ha pasado. Un cliente ha muerto?"
			return "WAIT"
			""" 
			Si el cliente muere inesperadamente es posible 
			que el servidor se haga la picha un lio por 
			algun tiempo, en ese caso enviamos WAIT. Si el 
			cliente por algun fallo no envia nada tambien 
			enviamos WAIT. Esto es poco eficiente, habra 
			que mejorarlo mas adelante
			"""	






# print "PyDirect Server V0.1\n(C) Juan Antonio Nache. 2008"
print "naNbot85 Server v0.1\n(C) Juan Antonio Nache. 2008-2013"
naNbot85 = naNbotMain()
naNbot85.mainLoop()

