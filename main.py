import ijson
import requests
import os
import zipfile
import io
# import sqlite3

dalink = "https://healthy.kaiserpermanente.org/pricing/innetwork/nc/2024-04-01_KFHP_NC-COMMERCIAL_in-network-rates.zip"

pathvar = os.path.abspath("./"+dalink.split("/")[-1])

'''con = sqlite3.connect("kpncal")
cur = con.cursor()
cur.execute("CREATE TABLE provider_references(id, NPIs, type, value)")
'''

if os.path.exists(pathvar):
    pass
else:
    r = requests.get(dalink)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(pathvar)

jsonfile = dalink.split("/")[-1].replace(".zip", ".json")
f = open(pathvar+"/"+jsonfile)

parser = ijson.parse(f)
i = 1
sql_row = "INSERT INTO"
for prefix, event, value in parser:
    if 'provider_references' in prefix:
        if [prefix, value] == ['provider_references.item', 'provider_group_id']:
            row = {}
    
        if prefix == 'provider_references.item.provider_group_id':
            row = {'group_id': value}
    
        elif [prefix, event] == ['provider_references.item.provider_groups.item.npi', 'start_array']:
            row['NPIs'] = []

        elif prefix == 'provider_references.item.provider_groups.item.npi.item':
            row['NPIs'].append(value)

        elif prefix == 'provider_references.item.provider_groups.item.tin.type':
            row['type'] = value 
        
        elif prefix == 'provider_references.item.provider_groups.item.tin.value':
            row['value'] = value # unfortunately a bit confusing here
    
        if [prefix, event] == ['provider_references.item', 'end_map']:
            '''placeholder = ', '.join(["%s"] * len(row))
            print(f"INSERT INTO TABLE {','.join(row.keys())} VALUES {placeholder}")
            print(list(row.values()))'''
            pass
    
    if 'in_network' in prefix:
        if [prefix, value] == ['in_network.item', 'negotiation_arrangement']:
            row = {}
    
        if prefix == 'in_network.item.negotiation_arrangement':
            row = {'negotiation_arrangement': value}
        
        elif prefix == 'in_network.item.name':
            row['name'] = value
        
        elif prefix == 'in_network.item.billing_code_type':
            row['billing_code_type'] = value
        
        elif prefix == 'in_network.item.billing_code_type_version':
            row['billing_code_type_version'] = value
        
        elif prefix == 'in_network.item.billing_code':
            row['billing_code'] = value
            row['id'] = i
            
        elif prefix == 'in_network.item.description':
            row['description'] = value


        if [prefix, event] == ['in_network.item.negotiated_rates', 'start_array']:

            if prefix == 'so': 
                row2 = {}


            pass

        if [prefix, event] == ['in_network.item', 'end_map']:
            pass
            ### insert SQL


    '''try:
        if 'negotiated_rates' in prefix:
            print([prefix, event, value])
            break
    except:
        pass'''



    if i >= 0:
        print([prefix, event, value])

    if i == 50:
        # print([prefix, event, value]) 
        break
    i += 1

