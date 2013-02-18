#!/usr/bin/python
#(C) Copyright Juan Antonio Nache Ramos. 2008-2013
#Under GPL License

#cargamos modulos necesarios
import urllib2
import urllib
import cookielib
import os
import urlparse
import socket
from time import sleep
from BeautifulSoup import BeautifulSoup
try:
	import cPickle as pickle
except:
	import pickle


def limpia_url(link,host):
	if len(link[1]) > 0 and link[0] != "javascript": #si el enlace no omite el propio host
		if len(link[4]) > 0: #si el enlace contiene parametros
			enlace=link[0]+ "://" + link[1]+link[2]+link[3]+"?"+link[4] #metemos un ?
		elif len(link[4]) == 0: #si no contiene parametros
			enlace=link[0]+ "://" + link[1]+link[2]+link[3]+link[4] #lo mostramos sin ? perdo dejamos link[4] por si se hace la picha un lio
	elif len(link[1]) == 0: #si el enlace omite el propio host
		if len(link[4]) > 0:#si tiene parametros
			enlace=link[0]+ "://" + host+"/"+link[2]+link[3]+"?"+link[4]
		else:#si no tiene parametros
			enlace=link[0]+ "://" + host+"/"+link[2]+link[3]+link[4]
	else:#en caso de que falle link[1] (quien sabe)
		print "enlace no parseado por razon desconozida"

	if len(enlace) > 0:#comprobamos la variable enlace
		return enlace
	else:#si esta chunga, lo comunicamos y la definimos como None
		print "Enlace vacio"
		enlace=None

	#return enlace #devolvemos la url construida correctamente


def extrae_enlaces(url):
	urls_final=[]#array que contendra enlaces y descargas

	cj = cookielib.LWPCookieJar() #objeto LWPCookieJar dentro del modulo cookielib
	COOKIEFILE = 'cookies.lwp' #fichero que usaremos para almacenar cookies


	if os.path.isfile(COOKIEFILE): #si el archivo de cookies existe
		cj.load(COOKIEFILE) #lo cargamos (cj es el objeto LWPCookieJar)


	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)

	#variables necesarias para la conexion
	#la url a la que nos conectamos se pasa como parametro a la funcion
	sourceurl=urlparse.urlparse(url)
	host=sourceurl[1]
	enlaces="EN http://"+host #lo usaremos para concatenar los enlaces separados por espacios. como primer parametro el comando necesario y el host donde se encuentra
	enlaces2=[]#almacenaremos todos los enlaces
	global cache#almacenaremos cierto numero de enlaces y descargas ya enviadas al servidor para no repetirlas
	descargas="DE "+url  #lo usaremos para concatenar las descargas separadas por espacios, el primer parametro es la url donde hemos buscado
	descargas2=[]#almacenaremos todas las descargas
	txheaders = {'User-agent' : 'Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.8.1.14) Gecko/20080404 Iceweasel/2.0.0.14 PezonOS-2.0.0.14-0etch1)','Keep-Alive' : '300', 'Connection' : 'keep-alive'} #user agent y demas

	try:
		req = urllib2.Request(url, None, txheaders) #la consulta
		sock = urllib2.urlopen(req) #el socket
		print url
		mimetype=sock.info().getheader("Content-Type")
		mimetype2=mimetype[:9]
		######################
		print mimetype
		if mimetype2=="text/html" or mimetype2=="text/xml;": #si el archivo es html:
			soup = BeautifulSoup(sock.read()) #mandamos el html al modulo BeautifoulSoup que se encarga de parsearlo, soup es el objeto

			# print soup.head.title.string #imprime el titulo de la pagina, cuidado, si la pagina no tiene titulo el programa peta
			i=0;#variable que incrementamos, la usaremos para ir seccionando las descargas de 10 en 10 o menos
			j=0;#lo mismo pero con los enlaces
			condescargas=""
			conenlaces=""
			for item in soup('a'):#extraemos todos los enlaces en la pagina
				try:#comprobamos que la variable es correcta
					item['href']
				except:#si no, la definimos como el propio host a buscar
					item['href']="http://"+host

				if len(item['href']) > 0: #si el href no esta vacio, cosa que el try anterir se encarga de hacer...
					link =  urlparse.urlparse(item['href'],"http") #desguazamos el enlace en el array link (scheme, dominio, script, argumentos...)
					enlace=limpia_url(link,host) #esto limpiara el link devolviendonoslo con shcheme y demas correctamente. url es la url a limpiar y host es le url donde se encuentra el enlace (en el caso de encontrar una url tipo /descargas.php)

					if enlace !=None: #si la variable no es None (no contiene nada), la almacenamos en el array enlaces
						link = urlparse.urlparse(enlace) #volvemos a desguazar el enlace, pero esta vez limpio
						#print "Dominio: " + link[1]
						# originally here was a large if because i was looking for something
						# but now it is not necesary. I delete this before do the first commit
						if 1 == 2:
							if descargas2.count(enlace) <= 0 and cache.count(enlace) <= 0:#si el enlace no esta guardado
								#print "Guardamos: "+enlace
								descargas2.append(enlace)#almacenamos el enlace en el array
								cache.append(enlace)
						else:
							if enlaces2.count(enlace) <= 0 and cache.count(enlace) <= 0:
								#print "Guardamos: "+enlace
								enlaces2.append(enlace)
								cache.append(enlace)
				else:
					print "href vacio, se ignora"
			#construimos los comandos a enviar
			if len(enlaces2) >0:#si hay enlaces
				for actualenlace in enlaces2:
					i=i+1#incrementamos
					if i >=6:#si ya hemos concatenado 6 o 5 enlaces:
						comando=enlaces+conenlaces
						urls_final.append(comando) #lo guardamos en el array que devolveremos
						i=0 #reseteamos el contador
						conenlaces=""#reseteamos la variable de concatenacion
					else:#si no, concatenamos
						conenlaces=conenlaces+" "+actualenlace
				#volvemos a construir para los datos que se han quedado fuera del for
				comando=enlaces+conenlaces
				urls_final.append(comando)
			i=0#reseteamos contador
			if len(descargas2) >0:#si hay descargas
				for actualdescarga in descargas2:
					i=i+1#incrementamos
					if i >=6:#si ya hemos concatenado 6 o 5 descargas:
						comando=descargas+condescargas
						urls_final.append(comando) #lo guardamos en el array que devolveremos
						i=0 #reseteamos el contador
						condescargas=""#reseteamos la variable de concatenacion
					else:#si no, concatenamos
						condescargas=condescargas+" "+actualdescarga
				#para los datos que se han quedado fuera del for, volvemos a construir
				comando=descargas+condescargas
				urls_final.append(comando)

			if len(cache) >= 8000:#si el cache contiene ya 8000 urls, vamos borrando las mas viejas
				cache.pop(8000)#borramos la url mas vieja
			return urls_final#enviamos los comandos
		##################
		else:#si el archivo no es html, lo mandamos como descarga
			print "*************No es un archivo html: "+mimetype+" **************"
			try:
				descargas=descargas+" "+url #definimos la url que nos han pasado como descarga
				#urls_final.append(enlaces) #metemos los enlaces en el array a retornar, en este caso vacio
				#urls_final.append(descargas) #metemos las descarags en el enlace a retornar en este caso es la url que debiamos explorar, ya que detectamos que no era un archivo de texto plano (html,txt,etc..)
				mimes="MI "+url+" "+mimetype
				print mimes
				urls_final.append(mimes) #construimos el comando que identifica el mimetype de la url
				#return urls_final
				return urls_final
			except:
				print "No se pudo enviar la informacion de la descarga"

	except:
		print "*********************************************************"
		print "**********Fallo extrayendo enlaces y descargas***********"
		print "*********************************************************"
		#urls_final.append(enlaces) #metemos en el array el contenido de enlaces que en este caso solo contendra la url en la que buscar y ningun enlace
		#urls_final.append(descargas) #lo mismo que con las descargas
		return urls_final #enviamos el buffer al programa principal (en este caso nada)


def procesa_respuesta(msg):
	print "Procesando respuesta del servidor"
	data=pickle.loads(msg) #des-serializamos los datos
	comando=data[0] #el index 0 contiene el comando
	for asdf in data:
		print asdf
	if comando == "S":
		print "Buscamos en:"
		for pagina in data[1:]:
			print pagina


print "Contectando..."
s = socket.socket()
try:#Probamos por el puerto 8510
	s.connect(("localhost", 8510))
	print "Conexion por el puerto 8510"
except:#Si no hay nada en ese puerto, probamos por el 8511
	print "Conexion por el puerto 8511"
	s.connect(("localhost", 8511))

#accion="Inicio"#accion la usaremos para los mensajes del servidor, antes de entrar en el bucle la definimos como Inicio para que el script pregunte al servidor que hacer
data=[] #almacenaremos los datos a enviar
print "---\nYeeeeeah.\n---"
while True:

	try:
		s.settimeout(1)
		accion=s.recv(4096)
		procesa_respuesta(accion)
	except socket.timeout:
		print "El servidor no tiene nada para nosotros por lo visto, vamos a pedirle algo..."
		data.append("Q?")
		s.send(pickle.dumps(data,1))#Enviamos al servidor los datos


print "Cliente fuera"
s.close()


