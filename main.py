import ijson
import requests
import os
import zipfile
import io
from datetime import datetime
import sqlite3

def get_link():
    this_months = datetime.today().strftime("%Y-%m") + "-01"  # hopefully Kaiser uploads on the first of the month
    link = f'https://healthy.kaiserpermanente.org/pricing/innetwork/nc/{this_months}_KFHP_NC-COMMERCIAL_in-network-rates.zip'
    
    user_check = input(f"is the following link correct? [y/n]: {link} ")
    if 'Y' in user_check.upper():
        return link
    else:
        return input('what is the link? :')


def download_and_unzip_file(link):
    # check if file of same name already downloaded
    pathvar = os.path.abspath("./"+link.split("/")[-1])
    
    if not os.path.exists(pathvar):
        r = requests.get(link)
        if r.status_code == 200:
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(pathvar)
            
    return os.path.join(pathvar, os.listdir(pathvar)[0])


def connect_to_DB(title):
    con = sqlite3.connect(title)
    cur = con.cursor()
    cur.execute('CREATE TABLE provider_group(group_id, tin_type, tin_value)')
    cur.execute('CREATE TABLE in_network(id, billing_code,name, billing_code_type, billing_code_type_version, negotiation_arrangement, description)')
    cur.execute('CREATE TABLE negotiated_rates(negotiated_billing_code, provider_references, negotiated_type, negotiated_rates, expiration_date, billing_class, billing_code_modifier)')
    cur.execute('CREATE TABLE provider(NPI, provider_group_id)')
    con.commit()
    return con


def insert_into_table(con, table, row_vals):
    cur = con.cursor()
    placeholder = [":"+key for key in row_vals]
    sql_row = f"INSERT INTO {table} VALUES({', '.join(placeholder)})"
    try:
        cur.execute(sql_row, row_vals)
    except:
        print(sql_row)
        print(row_vals)
        exit()
    con.commit()

def insert_many_into_table(con, table, rows):
    cur = con.cursor()
    placeholder = [":"+key for key in rows[0]]
    sql_row = f"INSERT INTO {table} VALUES({', '.join(placeholder)})"
    cur.executemany(sql_row, rows)
    con.commit()



def close_sql_connection(con):
    con.close()


def JSON_to_SQL(JSONfile):
    f = open(JSONfile)
    parser = ijson.parse(f)
    id = 0
    if os.path.exists("KPNCAL.db"):
        os.remove("KPNCAL.db")
    con = connect_to_DB("KPNCAL.db")

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
            if [prefix, event] == ['provider_references.item', 'start_map']:
                provider_reference_vars = {'group_id': None, 
                                           'tin_type': None, 
                                           'tin_value': None
                                          }
            
            elif [prefix, event] == ['provider_references.item.provider_groups.item.npi', 'start_array']:
                NPI_rows: list = []

            elif prefix == 'provider_references.item.provider_groups.item.npi.item':
                NPI_rows.append({'NPI': value, 'provider_group_id': provider_reference_vars['group_id']})
                insert_many_into_table(con, 'provider', NPI_rows)
                # should change this into an execute many

            elif prefix in prov_ref:
                provider_reference_vars[prov_ref[prefix]] = value

            elif [prefix, event] == ['provider_references.item', 'end_map']:
                insert_into_table(con, "provider_group", provider_reference_vars)
                provider_reference_vars = {}  # just in case

        if 'in_network' in prefix:
            
            if [prefix, event] == ['in_network.item', 'start_map']:
                in_network_vars = {'id':None, 
                                   'billing_code': None,
                                   'name': None, 
                                   'billing_code_type': None, 
                                   'billing_code_type_version': None, 
                                   'negotiation_arrangement': None, 
                                   'description': None
                                  }

            elif prefix == 'in_network.item.billing_code':
                in_network_vars['billing_code'] = value
                in_network_vars['id'] = id  # dumb but ensures uniqueness
                
            elif prefix in in_net:
                in_network_vars[in_net[prefix]] = value

            elif 'negotiated_rates' in prefix:
                
                if [prefix, event] == ['in_network.item.negotiated_rates', 'start_array']:
                    negotiated_rates_vars = {'negotiated_billing_code': in_network_vars['id'], 
                                 'provider_references': '', 
                                 'negotiated_type': None, 
                                 'negotiated_rates': None, 
                                 'expiration_date': None, 
                                 'billing_class': None, 
                                 'billing_code_modifier': None
                                }

                elif [prefix, event] == ['in_network.item.negotiated_rates.item.provider_reference', 'start_array']:
                        negotiated_rates_vars['provider_references'] = ''

                elif prefix == 'in_network.item.negotiated_rates.item.provider_reference.item':
                        negotiated_rates_vars['provider_references'] = negotiated_rates_vars['provider_references'] + "|" + str(value)            

                elif 'negotiated_prices' in prefix:               
                        if prefix in neg_prices:
                            negotiated_rates_vars[neg_prices[prefix]] = value

                elif [prefix, event] == ['in_network.item.negotiated_rates', 'end_array']:
                    insert_into_table(con, 'negotiated_rates', negotiated_rates_vars)
                    negotiated_rates_vars = {}  # just in case

            elif [prefix, event] == ['in_network.item', 'end_map']:
                insert_into_table(con, 'in_network', in_network_vars)
                in_network_vars = {}  
        if id%10000 == 0:
            print(".", end="")
        if id >= 2000000:
            close_sql_connection(con)
            break
    close_sql_connection(con)

if __name__ == '__main__':
    link = get_link()
    file = download_and_unzip_file(link)
    if file is None:
        exit()
    else:
        JSON_to_SQL(file)
    


