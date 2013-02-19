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
		db=MySQLdb.connect(host='localhost',user='naNbot85',passwd='naNbot85',db='naNbot85')
		self.cursor=db.cursor()

	def exec(self,query):
		return self.cursor.execute(query)		


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
				self.processLInks(links)

	def processLinks(self,links):
		host = links.pop(0) #extract host (first element)
		for link in links:
			# TODO here we clean the link
			# TODO insert only if link does not exist
			self.DB.exec("insert into enlaces (url,urlorigen) values ('"+link+"','"+host+"')")
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
			self.DB.exec("insert into descargas (url,origen) values ('"+descarga+"','"+host+"')")



#funcion que extraera enlaces de la DB segun su numero de visitas: esperemos que funcione correctamente cuando tenga un numero de clientes elevado :S
def extrae_enlace():
	global cursor
	r=cursor.execute("select url from enlaces order by explorado asc limit 1")#obtenemos uno de los enlaces menos visitados para no repetir
	if r > 0:#si encontro un enlace listo para ser explorado en la DB
		resultado=cursor.fetchall()#extraemos los datos
		for result in resultado:#esto deberemos arreglarlo mas adelante, no es elegante usar un foreach cuando solo hemos extraido un solo dato (buscar documentacion sobre el modulo de mysql)
			cursor.execute("update enlaces set explorado=explorado+1 where url='"+result[0]+"'") #aumentamos el contador de veces que hemos explorado el enlace
		return result[0] #devolvemos el enlace que queremos explorar
	else:
		return "http://localhost" # si algo salio mal o si no hay enlaces ordenamos al cliente que espere (copon!!)

def guarda_mime(msg):
	global cursor
	try:
		print "Descarga encontrada"
		mime=msg[3:].split(" ")
		descarga=mime.pop(0)
		mimetype=mime.pop(0)
		cursor.execute("insert into descargas (url,mimetype) values ('"+descarga+"','"+mimetype+"')")
	except:
		print "No se Guardo la descarga con mimetype"


# print "PyDirect Server V0.1\n(C) Juan Antonio Nache. 2008"
print "naNbot85 Server v0.1\n(C) Juan Antonio Nache. 2008-2013"

print "Conectando a la base de datos..."
try:#no conectamos a la base de datos
	cursor=mysql_conect()
except:#si no pudimos lo comunicamos por pantalla y cerramos el programa
	print "No se pudo establecer conexion con la base de datos. Cerrando"
	sys.exit()

print "Almacenando una copia de la base de datos en memoria."
copyenlaces=[]
copydescargas=[]

print "Paso 1/2 Almacenando enlaces..."
cursor.execute("select url from enlaces")
resultado=cursor.fetchall()
for result in resultado:
	copyenlaces.append(result[0])
print "Numero de enlaces: %s" % (str(len(copyenlaces)))

print "Paso 2/2 Almacenando descargas..."
cursor.execute("select url from descargas")
resultado=cursor.fetchall()
for result in resultado:
	copydescargas.append(result[0])
print "Numero de descargas: %s" % (str(len(copydescargas)))


class naNbotMain:
	def __init__(self):
		print "Fumando esperooo un cliente que no veooo... (Esperando clientes)"
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:#Probamos por el puerto 8510
			self.server.bind(("", 8510))
			print "Puerto de escucha: 8510"
		except:#Si por el anterior no podemos, probamos con el 8511
			self.server.bind(("", 8511))
			print "Puerto de escucha: 8511"

		self.server.listen(999) #max connections
		self.desc = [self.server] #store the server sock first, necesary?
		#self.cache=[] #definimos la cache de todos los datos encontrados, mas tarde procesaremos todo
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
		try:
			msg=sock.recv(1024)
			sock.settimeout(.1) #necesary?
			if msg == "quit": #if client want to quit
				sock.send("quit") #confirm to client
				self.desc.remove(sock) #delete from list
			else:
				if len(self.IA.msgClient(msg)) > 0:
					sock.send(res) #send response to client
				else:
					print("No response to client.")
		except:
			print ("Client out") #maybe not... review this
			self.desc.remove(sock)

	def waitcnx(self):
		try:
			newsock, (remhost, remport) = self.server.accept()
			self.server.settimeout(.1)
			print "Ahaha! Nuevo cliente: %s:%s" % (str(remhost), str(remport))
			self.desc.append(newsock)
		except:
			pass


class naNbotIA:
	def __init__(self):
		print ("[+] Starting IA 1+1=3...")
		self.worker = naNbotWorker()


	def msgClient(msg):
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
			try:#extraemos un enlace
				enlace=extrae_enlace()
				return enlace #devolvemos el enlace para que el cliente lo explore
			except:#si algo fue mal mandamos esperar al cliente
				return "WAIT"


		#client ask if we are ready
		elif msg[:2] == "RD":
			return "OK" #now always yes. Add flow control in future.


		#dont know yet
		elif msg[:2] == "MI":
			guarda_mime(msg)
			return "OK"


		#default option
		else:
			print "Algo extranio ha pasado. Un cliente ha muerto?"
			return "WAIT" 
			#Si el cliente muere inesperadamente es posible 
			#que el servidor se haga la picha un lio por 
			#algun tiempo, en ese caso enviamos WAIT. Si el 
			#cliente por algun fallo no envia nada tambien 
			#enviamos WAIT. Esto es poco eficiente, habra 
			#que mejorarlo mas adelante




