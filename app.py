from flask import Flask, render_template,redirect,url_for, jsonify,request
from gevent.pywsgi import WSGIServer
from database import odbc
from datetime import datetime

import os
import time
import json
import pickle
import requests
import threading

cnx=odbc.odbc_mysql()

template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(template_dir,'src','template')

app=Flask(__name__,template_folder=template_dir)

#APP ROUTE
@app.route('/')
def home():
   datos=cnx.execute("SELECT ROW_NUMBER() OVER(ORDER BY TBFechaMov DESC) AS Row#, PDANombreCliente , TBNumeroDocCliente , PDATelefonoContacto,TBOP , TBProducto , TBCantidad , TBIMEI,TBBodega,TBFechaMov  FROM TareasBot INNER JOIN PedidosDatosAnexos ON PedidosDatosAnexos.PDAOp = TareasBot.TBOP AND PedidosDatosAnexos.PDACliente = TareasBOT.TBCliente WHERE  TBProceso = 'SERIES_BOT'  AND TBTomado = 0 AND TBBodega IN ('Telemarketing','B2B') ORDER BY TBFechaMov DESC") 
   insertobjets=[]
   columnas_name= ['Row','Nombre','DocClient','Tel','Orden','Producto','Cantidad','EMEI','Bodega','Fecha']
   for record in datos:
        insertobjets.append(dict(zip(columnas_name,record)))        
   return render_template('index.html',data=insertobjets)

#APP DELETTE FILE RECIBE WEB
@app.route('/delete/<string:id>')
def delete(id):    
    cnx.in_up_del_sql("DELETE Registro WHERE RegNDB='Series' AND RegOP='"+str(id)+"'")    
    return redirect(url_for('home'))


#APP ACTUALIZAR FILE RECIBE WEB
@app.route('/UpDateError/<string:id>')
def UpDateError(id):
    print(id)
    cnx.in_up_del_sql("UPDATE Registro SET RegEstado='APPROVED' WHERE RegNDB='Series' AND RegOP='"+str(id)+"'")
    return redirect(url_for('home')) 

#-------------------------------------------------------------------------------------------------------------------------------------------------
#APP RECIBIR DATA JSON
@app.route('/RecibeData',methods=['POST'])
def RecibeData():   
     content = request.json    
     datos=cnx.execute("SELECT PDANombreCliente , TBNumeroDocCliente , PDATelefonoContacto,TBOP , TBProducto , TBCantidad , TBIMEI ,TBBodega FROM TareasBot INNER JOIN PedidosDatosAnexos ON PedidosDatosAnexos.PDAOp = TareasBot.TBOP AND PedidosDatosAnexos.PDACliente = TareasBOT.TBCliente WHERE  TBProceso = '"+str(content['mytext'])+"'  AND TBTomado = 0 AND TBBodega IN ('Telemarketing','B2B') ORDER BY TBFechaMov ASC")  
     insertobjets=[]
     Registros=len(datos)
     if Registros > 0:
         columnas_name= ['Nombre Cliente', 'Doc Cliente','Teléfono','Orden','Producto','Cantidad','IMEI','Bodega']
         for record in datos:
                 insertobjets.append(dict(zip(columnas_name,record)))              
         return jsonify({"Bot":content['mytext'],
                         "Registros":Registros,
                        "Data":insertobjets}) 
     else:
         return jsonify({"Error":"No existen registro Para "+content['mytext']}) 
         
#-------------OBTENER ADATOS DE VEHICULOS-------------
@app.route('/GetVehicles',methods=['GET'])
def GetVehicles(): 
    Array1=[]
    url= os.getenv('GetVehicles')#GURADAMOS LA URL DONDE ESTAS¿N LOS DATOS DEL VEHICULO
    token={"token": os.getenv('Token')}#EL TOKEN
    PlacasAutos= requests.post(url,json=token)
    if PlacasAutos.status_code==200:
         PlacasAutos=PlacasAutos.json()        
         for Placas in PlacasAutos:#Recorremos Todas las Placas                  
                 try:                  
                        Serial= Placas["serialNumber"] 
                 except:
                        Serial= "S/N"                 
                 PRODUCTO={
                           "Placa": Placas["plate"] ,
                           "Series": Serial,
                           "Nombre": Placas["name"],
                           "Odometro": Placas["lastLocation"]["odometer"]                        
                            }
                 Array1.append(PRODUCTO)                     
         return jsonify({"Autos":Array1})
    else:         
         return jsonify({"Message":"Error"})
#---------------------------MOSTRAR PRODUCTOS CON EL METODO GET-------------------------------------
@app.route('/GetRoute',methods=['GET'])
def GetRoute():
     Array=[]
     DateStar="2023-08-03T08:00:00"
     DateEnd="2023-08-03T08:23:59"
     Vehiculo="STP 5845"
     url=os.getenv('GetRoute')
     token={"token": os.getenv('TOKEN'), "plate": Vehiculo,"fromDate": DateStar, "toDate": DateEnd}
     DatosAuto= requests.post(url,json=token)
     if(DatosAuto.status_code==200):
             DatosAuto=DatosAuto.json()
             if(len(DatosAuto)!=0):
                 for sensor in DatosAuto[0]["sensors"]:
                       new_prod={"idIo": sensor["idIo"],
                                 "Valor": sensor["val"],
                                 "Fecha": sensor["timestamp"]["Date"],
                                 "pos x": sensor["location"]["coordinates"][0],
                                 "pos y": sensor["location"]["coordinates"][1]    
                                 }
                       Array.append(new_prod)                     
                 return jsonify({Vehiculo:Array})
             else:
                     return jsonify({"Message":"Placa No Encontrada"})
     else:    
             return jsonify({"Message":"Placa No Encontrada"}) 
         
#------------Obtener Registros By Fecha ------------------
@app.route('/GetSeriesBot',methods=['GET'])
def GetSeriesBot(): 
     filename = 'BotSeriesData.json'    
     with open(filename, "r+") as file:
              data = json.load(file)
     return jsonify(data) 

#----------------------------------------------------------  
#ACTUALIZAR UN JSON CON DATOS SERIES DE LOS FICHEROS        
def BotDataJson():
      lista=["Validados"]
      for PORCESO in lista:             
           filename = 'BotSeriesData.json'
           with open(filename, "r+") as file:
              data = json.load(file)
              dataadd=data["Verificacion"]
              entry = {"Time": str(datetime.now()), "Cantidad": str(len(cnx.execute("SELECT * FROM TareasBot INNER JOIN PedidosDatosAnexos ON PedidosDatosAnexos.PDAOp = TareasBot.TBOP AND PedidosDatosAnexos.PDACliente = TareasBOT.TBCliente WHERE  TBProceso = 'VALIDADOS'  AND TBTomado = 0 AND TBBodega IN ('Telemarketing','B2B') ORDER BY TBFechaMov ASC"))) }
              dataadd.pop()
              dataadd.insert(0,entry)              
              actdata={ "Bot": "Validacion",
                        "Verificacion": dataadd}            
              file.seek(0)
              json.dump(actdata, file)
#-------------------------------------------------------------             
def write_json():
     filename = 'data.json'
     entry = {"Time": str(datetime.now()), "Cantidad": 27}
     with open(filename, "r+") as file:
              data = json.load(file)              
              data.insert(0,entry)
              #data.append(entry)
              file.seek(0)
              json.dump(data, file)
   
#CRITERIO DE ARRANQUE: SE REGULA SEGÚN A CLIENTE
def timer(timer_runs):  
    while timer_runs.is_set():        
        #write_json()     
        BotDataJson()#Actualizar Json Con Datos de los Bots
     

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  
        time.sleep(10)   #ACA SE REGULA EL TIEMPO DE EJECUCION DEL BOT     
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ 
#Arrancamos el Sustema Cada Minuntos Despues de Realizar Cada Caso  
timer_runs = threading.Event()
timer_runs.set()
t = threading.Thread(target=timer, args=(timer_runs,)) 
t.start()   
                  
if __name__=='__main__':
    http_server = WSGIServer(('', 4000), app)
    http_server.serve_forever()
    
