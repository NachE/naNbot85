#!/usr/bin/python
#(C) Copyright Juan Antonio Nache Ramos. 2008-2013
#Under GPL License

import socket
import select
import re
import sys
from time import sleep
import MySQLdb
try:
	import cPickle as pickle
except:
	import pickle

def mysql_conect():
	db=MySQLdb.connect(host='localhost',user='user_of_naNbot85',passwd='pass_of_naNbot85',db='nanbot85')
	cursor=db.cursor()
	return cursor


def aceptar_conexiones():
    try:
        global server
        global desc
        newsock, (remhost, remport) = server.accept()
        server.settimeout(.1)
        print "Ahaha! Nuevo cliente: %s:%s" % (str(remhost), str(remport))
        desc.append(newsock)
    except:
        pass


#funcion que procesa los envios del cliente
def procesa(msg):
	data=pickle.loads(msg) #des-serializamos los datos
	comando=data[0] #el index 0 contiene el comando
	if comando == "Q?":
		print "Cliente pregunta que hacer, enviamos algunas paginas"
		data2=[]
		data2.append("S")
		i=0
		while i < 900:
			i=i+1
			print i
			data2.append("http://www.nada"+str(i)+".com")
		print "Enviando" + str( len(data2) ) + "paginas"
		return pickle.dumps(data2,1) #retornamos los datos serializados


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

# Obsolete:
# print "PyDirect Server V0.1\n(C) Juan Antonio Nache. 2008"
print "naNbot85 Server v0.1\n(C) Juan Antonio Nache. 2008-2013"

print "Fumando esperooo un cliente que no veooo... (Esperando clientes)"
global server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:#Probamos por el puerto 8510
	server.bind(("", 8510))
	print "Puerto de escucha: 8510"
except:#Si por el puerto anterior no podemos, probamos con el 8511
	server.bind(("", 8511))
	print "Puerto de escucha: 8511"

server.listen(999)#numero maximo de conexiones
global desc
cache=[] #definimos la cache de todos los datos encontrados, mas tarde procesaremos todo
desc = [server]
while 1:
	aceptar_conexiones() #aceptamos conexiones por un tiempo breve
	(sread, swrite, sexc) = select.select(desc, [], [])
	for sock in sread:
		if sock != server: #si el socket no es el del servidor (??)
			try:
				msg=sock.recv(1024)#recibimos datos del cliente
				sock.settimeout(.1)
				respuesta=procesa(msg) #funcion que procesa el mensaje y devuelve una respuesta
				if len(respuesta) > 0:
					sock.send(respuesta) #se la enviamos al cliente.
				else:
					print "Ninguna orden para el cliente"
			except:
				#host, port=sock.getpeername()
				#print "[%s:%s] Desconectado." % (str(host), str(port))
				print "Un cliente ha caido o hubo error procesando mensaje del cliente"
				desc.remove(sock)
