import os
import pyodbc
import logging
class odbc_mysql():    
    def __init__(self):
         try:
               self.Cnx=pyodbc.connect("Driver={%s};Server=%s;Database=%s;UID=%s;PWD=%s;Trusted_Connection=no;" % (os.getenv('SQL_DRIVER'), os.getenv('SQL_SERVER'),os.getenv('SQL_DB'), os.getenv('SQL_USR'),os.getenv('SQL_PASS')))  
         except pyodbc.Error as ex:
             print("Error")              
    def execute(self,sql_in):
        try:
             self.Cnx.cursor()
             res=self.Cnx.execute(sql_in)         
             Datos=res.fetchall()  
                            
             return Datos             
        except pyodbc.Error as ex:
             print("Error") 
    def in_up_del_sql(self,sql):
        try:
             self.Cnx.cursor()
             self.Cnx.execute(sql)  
             self.Cnx.commit()   
                
             return True               
        except pyodbc.Error as ex:
             logging.error("Error"+str(ex.args[0])+" | "+str(ex.args[1]))
             return False
