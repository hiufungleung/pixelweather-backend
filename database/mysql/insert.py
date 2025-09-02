import json
import mysql.connector

# 讀取 JSON 文件
with open('au_postcodes.json', 'r') as file:
    json_data = json.load(file)

# # Get states data
# s = set()
# for i, item in enumerate(json_data):
#     s.add((item['state_name'], item['state_code']))
#
# states, i = [], 0
# for name, code in s:
#     i += 1
#     states.append({'id': i, 'state_name': name, 'state_code': code})
# print(states)

# create a dict: state_code_id[state_code] = state_id
# state_code_id = {}
# for state in states:
#     state_code_id[state['state_code']] = state['id']
# print(state_code_id)

suburbs = []
for i, item in enumerate(json_data):
    if item['state_code'] != 'QLD':
        continue
    suburbs.append({'suburb_name': item['place_name'],
                    'postcode': item['postcode'],
                    'latitude': item['latitude'],
                    'longitude': item['longitude'],
                    'state_code': 'QLD'})


# print(suburbs)
# 連接 MySQL
connection = mysql.connector.connect(
    host='149.28.188.65',
    user='yakiniku',
    password='30624700',
    database='pixel_weather'
)
cursor = connection.cursor()

# 插入 JSON 數據
# for item in states:
#     sql = "INSERT INTO states (id, state_name, state_code) VALUES (%s, %s, %s)"
#     cursor.execute(sql, (item['id'], item['state_name'], item['state_code']))
i = 0
for item in suburbs:
    i += 1
    sql = "INSERT INTO suburbs (suburb_name, postcode, latitude, longitude, state_code) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (item['suburb_name'], item['postcode'], item['latitude'], item['longitude'], item['state_code']))
    print(f'inserted {i}')

# 提交事務
connection.commit()
cursor.close()
connection.close()