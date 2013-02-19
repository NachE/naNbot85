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

def guarda_enlaces(msg):
	global cursor
	global cache
	if len(cache) > 2: #si en la cache hemos alcanzado los 100 comandos, procedemos a guardar, es importante tener suficentes urls a explorar, si no esto falla
		print "Cache lleno, volcando en la base de datos..."
		for msg2 in cache:
			#try:#separamos cada enlace en un array ignorando los 3 primeros caractres que corresponden con "EN "
			enlaces=msg2[3:].split(" ")
			host=enlaces.pop(0)
			if len(enlaces) > 0:
				for enlace in enlaces: #vamos extraiendo los enlaces uno a uno
					#r=cursor.execute("select * from enlaces where url='"+enlace+"'") #comprobamos si existe el enlace
					enlace=enlace.replace("'","%27")
					enlace=enlace.replace("\'","%27")
					enlace=enlace.replace("//","/")
					enlace=enlace.replace("///","/")
					enlace=enlace.replace("////","/")
					enlace=enlace.replace("http:/","http://")
					consulta="insert into enlaces (url,urlorigen) values ('"+enlace+"','"+host+"')"
					print (consulta)
					r=copyenlaces.count(enlace)
					if r <= 0:# si el enlace no existe
						try:
							cursor.execute(consulta)
							copyenlaces.append(enlace)
						except:
							print "Fallo al procesar el enlace "+enlace+ "Host: "+host
							print "Consulta: "+consulta
			#except: #en caso de fallo, informamos
			#	print "No se pudieron procesar los enlaces: "+msg
		cache[:]=[]#vaciamos la cache
	else:
		#print "\r Cache: %s" % (str(len(cache)))
		cache.append(msg)


def guarda_descargas(msg):
	global cursor
	try:
		descargas=msg[3:].split(" ")
		host=descargas.pop(0)#extraemos el host donde se encntraban los enlaces
		if len(descargas) > 0: #si una vez extraido el comando y el host principal hay datos en "descargas" significa que son las descargas que guardaremos en la db
			print "Descargas encontradas"
			for descarga in descargas:#vamos extraiendo las descargas una a una
				r=cursor.execute("select * from descargas where url='"+descarga+"'")#comprobamos si existe la descarga en la db
				if r <= 0:#si no existe la descarga
					cursor.execute("insert into descargas (url,origen) values ('"+descarga+"','"+host+"')")
	except:
		print "No se guardaron las descargas: "+msg


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
		self.cache=[] #definimos la cache de todos los datos encontrados, mas tarde procesaremos todo
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

	def msgClient(msg):
		#client found links
		if   msg[:2] == "EN":
			guarda_enlaces(msg)
			return "OK"


		#client found downloads
		elif msg[:2] == "DE": 
			guarda_descargas(msg)
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




