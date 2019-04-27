import psycopg2
import json
import zipfile
import os



conn = psycopg2.connect(host="35.206.67.212", database="postgres", user="postgres")
cur = conn.cursor()
#Get client list
cur.execute("SELECT id, name, is_eligible FROM teams ORDER BY id")
#Store client list
rows = cur.fetchall()
clients = []
for x in rows:
    clients.append({"id":x[0], "name":x[1], "eligible":x[2], "language":None, "client_file":None, "version":-1})
    print clients

#Get submissions
cur.execute("SELECT id, team_id, version, data, lang FROM submissions ORDER BY id")
rows = cur.fetchall()
for x in rows:
    for y in clients:
        if x[1] == y["id"] and x[2] > y["version"]:
            y["language"] = x[4]
            y["client_file"] = x[3]
            y["version"] = x[2]
            break
conn.close()
#Create client files
for x in clients:
    if x["version"] is not -1:
        work_dir = os.path.dirname(__file__)
        rel_path = "../../var/static/gladiator"
        print work_dir + rel_path
        with open(os.path.join(work_dir, rel_path) + "/" + x["name"] + ".zip", 'wb') as f:
            f.write(x["client_file"])
        
#write team file        
output = []
for x in clients:
    if x["version"] is not -1:
        myzip = zipfile.ZipFile("var/static/gladiator/" + x["name"] + ".zip", 'r')
        output.append({"tag":{"name":x["name"], "commit":x["version"]},
                       "repository":{"path":str(str(myzip.namelist()[0]).split('/')[0])},
                       "team":{"slug":x["name"], "eligible_to_win":x["eligible"]},
                       "language":x["language"]})
    
with open("clients.txt", 'w') as f:
    json.dump(output, f)
