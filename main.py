import ijson
import requests
import os
import zipfile
import io
from datetime import datetime
import sqlite3

dalink = "https://healthy.kaiserpermanente.org/pricing/innetwork/nc/2024-04-01_KFHP_NC-COMMERCIAL_in-network-rates.zip"


def get_link():
    this_months = datetime.today().strftime("%Y-%m") + "-01"
    link = f'https://healthy.kaiserpermanente.org/pricing/innetwork/nc/{this_months}_KFHP_NC-COMMERCIAL_in-network-rates.zip'
    user_check = input(f"is the following link correct? [y/n]: {link}")
    if "y" in user_check.upper():
        return link
    else:
        return input('what is the link? ')


def download_and_unzip_file(link):
    # check if file of same name already downloaded
    pathvar = os.path.abspath("./"+link.split("/")[-1])
    
    if not os.path.exists(pathvar):
        r = requests.get(link)
        if r.status_code == 200:
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(pathvar)
            return os.listdir()[0]

        else:
            print('error with link. Please try again.')


'''con = sqlite3.connect("kpncal")
cur = con.cursor()
cur.execute("CREATE TABLE provider_references(id, NPIs, type, value)")
'''

def connect_to_DB(title):
    con = sqlite3.connect('kpncal.db')
    cur = con.cursor()
    cur.execute('CREATE TABLE provider_group(group_id, NPIs, tin_type, tin_value)')
    cur.execute('CREATE TABLE in_network(id, billing_code,name, billing_code_type, billing_code_type_version, negotiation_arrangement, description)')
    cur.execute('CREATE TABLE negotiated_rates(negotiated_billing_code, provider_references, negotiated_type, negotiated_rates, expiration_date, billing_class, billing_code_modifier)')
    return con

def insert_into_table(con, table, row_vars):
    cur = con.cursor()
    placeholder = ', '.join(["%s"] * len(row_vars))
    cur.execute(f"INSERT INTO {table} {','.join(row_vars.keys())} VALUES {placeholder}")


def JSON_to_SQL(JSONfile):
    f = open(JSONfile)
    parser = ijson.parse(f)
    id = 0
    for prefix, event, value in parser:
        id += 1
        prov_ref = {'provider_references.item.provider_group_id': 'group_id',
                    'provider_references.item.provider_groups.item.tin.type': 'tin_type',
                    'provider_references.item.provider_groups.item.tin.value': 'tin_value'
                    }
        
        in_net = {'in_network.item.negotiation_arrangement': 'negotiation_arrangement',
                  'in_network.item.name': 'name',
                  'in_network.item.billing_code_type': 'billing_code_type',
                  'in_network.item.billing_code_type_version': 'billing_code_type_version',
                  'in_network.item.description': 'description'
                  }
        
        neg_prices = {'in_network.item.negotiated_rates.item.negotiated_prices.negotiated_type': 'negotiated_type',
                     'in_network.item.negotiated_rates.item.negotiated_prices.negotiated_rate': 'negotiated_rate',
                     'in_network.item.negotiated_rates.item.negotiated_prices.expiration_date': 'expiration_date',
                     'in_network.item.negotiated_rates.item.negotiated_prices.billing_class': 'billing_class',
                     'in_network.item.negotiated_rates.item.negotiated_prices.billing_code_modifier': 'billing_code_modifier',
                     }

        if 'provider_references' in prefix:
            if [prefix, event] == ['provider_references', 'start_array']:
                row_vars = {}
            
            elif [prefix, event] == ['provider_references.item.provider_groups.item.npi', 'start_array']:
                row_vars['NPIs'] = []

            elif prefix == 'provider_references.item.provider_groups.item.npi.item':
                row_vars['NPIs'].append(value)

            elif prefix in prov_ref:
                row_vars[prov_ref[prefix]] = value

        if [prefix, event] == ['provider_references.item', 'end_map']:
            '''placeholder = ', '.join(["%s"] * len(row)) print(f"INSERT INTO TABLE {','.join(row.keys())} VALUES {placeholder}") print(list(row.values()))'''
            pass

        if 'in_network' in prefix:

            if [prefix, event] == ['in_network', 'start_array']:
                row_vars = {}

            elif prefix == 'in_network.item.billing_code':
                row_vars['billing_code'] = value
                row_vars['id'] = id  # dumb but unique
                
            elif prefix in in_net:
                row_vars[in_net[prefix]] = value

            elif 'negotiated_rates' in prefix:
                
                if [prefix, event] == ['in_network.item.negotiated_rates', 'start_array']:
                    row2_vars = {}
                    row2_vars['negotiated_billing_code'] = row_vars['id'] # we are talking about a combination of (billing code, negotation arrangement, billing_code_type)

                    if [prefix, event] == ['in_network.item.negotiated_rates.item.provider_reference', 'start_array']:
                        row2_vars['provider_references'] = []

                    elif prefix == 'in_network.item.negotiated_rates.item.provider_reference.item':
                        row2_vars['provider_references'].append(value)                

                    elif 'negotiated_prices' in prefix:               
                        if prefix in neg_prices:
                            row2_vars[neg_prices[prefix]] = value

                if [prefix, event] == ['in_network.item.negotiated_rates', 'end_array']:
                    # write SQL 
                    pass

            if [prefix, event] == ['in_network.item', 'end_map']:
                pass
                ### write SQL
        if id >= 10000:
            break


    '''try:
        if 'negotiated_rates' in prefix:
            print([prefix, event, value])
            break
    except:
        pass'''


