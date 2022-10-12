import pymongo

class Mymongo:
    def __init__(self, dbname, colname):
        self.myclient = pymongo.MongoClient('127.0.0.1:27017')
        self.mydb = self.myclient[dbname]
        self.mycol = self.mydb[colname]

    def insert_one(self, ip):
        self.mycol.insert_one(ip)

    def removeall(self):
        self.mycol.delete_many({})

    def count_ip(self, ip):
        return self.mycol.count_documents({"ip":ip})

    def find_ip(self):
        ip_list=self.mycol.find({},{ "_id": 0,"ip":1,"port":1})
        return ip_list


#ipmongo = Mymongo("proxy_db", "ip_list")
ipmongo = Mymongo("proxy_new", "ip_list")


