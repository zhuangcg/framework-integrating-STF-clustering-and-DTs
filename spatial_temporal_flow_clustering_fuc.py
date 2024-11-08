# encoding: utf-8
from shapely import Point, LineString
from utils import time_to_hour


class SpatialTemporalFlowCluster:
    def __init__(self, _stfc_id, _sfc_id, _flow_geom, _sfc_record_num, _start_time,
                 _end_time, _record_detail):
        if isinstance(_stfc_id, int):
            self.stfc_id = f'stfc{str(_stfc_id).zfill(3)}'
        else:
            self.stfc_id = _stfc_id
        self.sfc_id = _sfc_id
        self.flow = _flow_geom
        self.sfc_record_num = _sfc_record_num
        self.start_time = _start_time
        self.end_time = _end_time
        self.including_record_detail = _record_detail
        self.time_span = [time_to_hour(_start_time), time_to_hour(_end_time)]
        self.record_start_time_list = [time_to_hour(_start_time)]
        self.record_end_time_list = [time_to_hour(_end_time)]
        self.stfc_record_num = len(self.including_record_detail)

    def calculate_flow_start_and_end_time(self):
        if min(self.record_start_time_list) - max(self.record_start_time_list) > 12:
            self.record_start_time_list = [i - 24 if i > 12 else i for i in self.record_start_time_list]
        if min(self.record_end_time_list) - max(self.record_end_time_list) > 12:
            self.record_end_time_list = [i - 24 if i > 12 else i for i in self.record_end_time_list]
        self.start_time = sum(self.record_start_time_list) / len(self.record_start_time_list)
        self.end_time = sum(self.record_end_time_list) / len(self.record_end_time_list)
        self.start_time = self.start_time + 24 if self.start_time < 0 else self.start_time
        self.end_time = self.end_time + 24 if self.end_time < 0 else self.end_time
        self.time_span = [self.start_time, self.end_time]
        print(self.time_span)


    def add_flow(self, _another_record_detail):
        _another_record_uuid_list = list(_another_record_detail.keys())
        for _uuid in _another_record_uuid_list:
            if _uuid not in self.including_record_detail.keys():
                self.including_record_detail[_uuid] = _another_record_detail[_uuid]
                self.record_start_time_list.append(time_to_hour(_another_record_detail[_uuid]['start_time']))
                self.record_end_time_list.append(time_to_hour(_another_record_detail[_uuid]['end_time']))
            self.calculate_flow_start_and_end_time()
            self.stfc_record_num = len(self.including_record_detail)


    def merge_another_flow(self, tfc):
        _flow_id_list = tfc.including_flow_id_list
        _flow_flow_weight = len(tfc.including_flow_id_list) / (
                len(tfc.including_flow_id_list) + len(self.including_flow_id_list))
        _self_flow_weight = len(self.including_flow_id_list) / (
                len(tfc.including_flow_id_list) + len(self.including_flow_id_list))
        _start_time = tfc.start_time
        _end_time = tfc.end_time
        _date_list = tfc.record_date_list
        _flow_origin = Point(tfc.flow.coords[0][0], tfc.flow.coords[0][1])
        _flow_destination = Point(tfc.flow.coords[1][0], tfc.flow.coords[1][1])
        _self_origin = Point(self.flow.coords[0][0], self.flow.coords[0][1])
        _self_destination = Point(self.flow.coords[1][0], self.flow.coords[1][1])
        merge_origin = Point(
            (_flow_origin.x * _flow_flow_weight + _self_origin.x * _self_flow_weight),
            (_flow_origin.y * _flow_flow_weight + _self_origin.y * _self_flow_weight)
        )
        merge_destination = Point(
            (_flow_destination.x * _flow_flow_weight + _self_destination.x * _self_flow_weight),
            (_flow_destination.y * _flow_flow_weight + _self_destination.y * _self_flow_weight)
        )
        self.flow = LineString([merge_origin, merge_destination])
        self.has_merge = True
        self.add_flow(_flow_id_list, _start_time, _end_time, _date_list, tfc.flow_detail)
        self.merge_num_list.append(len(self.including_flow_id_list))
        self.merge_num_list.append(len(tfc.including_flow_id_list))
        self.spatial_flow_cluster_num += tfc.spatial_flow_cluster_num
