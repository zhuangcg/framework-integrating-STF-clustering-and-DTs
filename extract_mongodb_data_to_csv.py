# encoding: utf-8
"""
@author: Zcg
@license: (C) Copyright 2017-2023, Personal exclusive right.
@contact: zcg46580121@163.com
@software: PyCharm
@application: TwoLayerFramework
@file: extract_mongodb_data_to_csv.py
@time: 2024/11/07 21:26
@desc: 
"""

from Mongodb_Manage import MongoDB
import pandas as pd

if __name__ == '__main__':
    mongodb = MongoDB('users_flow_cluster', 'bike_user_part1')

    cycling_record_list = []
    for user_info in mongodb.find({'user_id': "945a5b919ea73a83eeee7c**********"}):
        trajectory_list = user_info['trajectory_list']
        for cycling_record in trajectory_list:
            cycling_record_list.append({
                'uid': user_info['user_id'],
                'uuid': cycling_record['uuid'],
                'origin_x': cycling_record['origin'][0],
                'origin_y': cycling_record['origin'][1],
                'destination_x': cycling_record['destination'][0],
                'destination_y': cycling_record['destination'][1],
                'date': cycling_record['date'],
                'start_time': cycling_record['start_time'],
                'end_time': cycling_record['end_time'],
                'spend_time': cycling_record['spend_time'],
                'distance': cycling_record['direct_distance']
            })
    df = pd.DataFrame(cycling_record_list)
    df.to_csv('sample_bike_records.csv', index=False)

