# encoding: utf-8
# The original spatiotemporal flow clustering method we used was proposed by Yao et al.(2018). The article is linked as follows:
# https://doi.org/10.1109/ACCESS.2018.2864662

from shapely import Point, LineString
from utils import time_to_hour, hour_to_time


class SpatioTemporalFlowCluster:
    def __init__(self, _stfc_id, _sfc_id, _flow_geom, _sfc_record_num, _start_time,
                 _end_time, _record_detail):
        if isinstance(_stfc_id, int):
            self.stfc_id = f'stfc{str(_stfc_id).zfill(3)}_{_sfc_id}'
        else:
            self.stfc_id = _stfc_id
        self.sfc_id = _sfc_id
        self.flow = _flow_geom
        self.start_time = _start_time
        self.end_time = _end_time
        self.including_record_detail = _record_detail
        self.sfc_record_num = _sfc_record_num
        self.stfc_record_num = len(self.including_record_detail)
        self.time_span = [time_to_hour(_start_time), time_to_hour(_end_time)]
        self.record_start_time_list = [time_to_hour(_start_time)]
        self.record_end_time_list = [time_to_hour(_end_time)]
        self.has_merged = False

    # Calculate the start and end times of the spatiotemporal flow cluster without considering the specific date on which the ride occurred
    def calculate_flow_start_and_end_time(self):
        if max(self.record_start_time_list) - min(self.record_start_time_list) > 12:
            self.record_start_time_list = [i - 24 if i > 12 else i for i in self.record_start_time_list]
        if max(self.record_end_time_list) - min(self.record_end_time_list) > 12:
            self.record_end_time_list = [i - 24 if i > 12 else i for i in self.record_end_time_list]
        _start_time = sum(self.record_start_time_list) / len(self.record_start_time_list)
        _end_time = sum(self.record_end_time_list) / len(self.record_end_time_list)
        self.time_span = [_start_time + 24 if _start_time < 0 else _start_time,
                          _end_time + 24 if _end_time < 0 else _end_time]
        self.start_time = hour_to_time(self.time_span[0])
        self.end_time = hour_to_time(self.time_span[1])


    def add_flow(self, _another_record_detail):
        _another_record_uuid_list = list(_another_record_detail.keys())
        for _uuid in _another_record_uuid_list:
            if _uuid not in self.including_record_detail.keys():
                self.including_record_detail[_uuid] = _another_record_detail[_uuid]
                self.record_start_time_list.append(time_to_hour(_another_record_detail[_uuid]['start_time']))
                self.record_end_time_list.append(time_to_hour(_another_record_detail[_uuid]['end_time']))
            self.calculate_flow_start_and_end_time()
            self.stfc_record_num = len(self.including_record_detail)

    def merge_neighbor_tfc(self, _neighbor_stfc):
        _neighbor_stfc_origin = _neighbor_stfc.flow.coords[0]
        _neighbor_stfc_destination = _neighbor_stfc.flow.coords[1]
        _self_origin = self.flow.coords[0]
        _self_destination = self.flow.coords[1]
        _merged_origin = [(_self_origin[0] + _neighbor_stfc_origin[0]) / 2,
                          (_self_origin[1] + _neighbor_stfc_origin[1]) / 2]
        _merged_destination = [(_self_destination[0] + _neighbor_stfc_destination[0]) / 2,
                               (_self_destination[1] + _neighbor_stfc_destination[1]) / 2]
        self.flow = LineString([_merged_origin, _merged_destination])
        self.add_flow(_neighbor_stfc.including_record_detail)
        self.sfc_record_num += _neighbor_stfc.sfc_record_num
        self.sfc_id = f'{self.sfc_id}_and_{_neighbor_stfc.sfc_id}'
        self.has_merged = True


def init_bike_record_with_stfc_obj(_sfc_obj):
    """
    For each spatial flow cluster, create initial spatiotemporal flow clusters corresponding to each ride record it contains.
    Parameters:
         _sfc_obj (SpatialClusterFlow): A given spatial flow cluster object
    Returns:
         tuple: the initial spatiotemporal flow cluster dictionary corresponding to each ride record UUID
    """
    _init_temporal_spatial_flow_cluster_dict = {}
    # Sort the cycling records by start time to ensure that ride records with nearby trip times can be better clustered.
    sorted_including_record_detail = sorted(_sfc_obj.including_record_detail.items(),
                                                         key=lambda item: time_to_hour(item[1]['start_time']))
    for _num, (_uuid, _record_info) in enumerate(sorted_including_record_detail):
        _stfc = SpatioTemporalFlowCluster(_num,
                                           _sfc_obj.sfc_id,
                                           _sfc_obj.flow,
                                           _sfc_obj.record_num,
                                           _record_info['start_time'],
                                           _record_info['end_time'],
                                           {_uuid: _record_info})
        _init_temporal_spatial_flow_cluster_dict[_uuid] = _stfc
    return _init_temporal_spatial_flow_cluster_dict


def t1_is_earlier_than_t2(_t1, _t2):
    """
    Determine if time t1 is earlier than t2 without considering the specific dates.
    taking into account the cyclical nature of time. It uses two conditions: one where _t1 is within 12 hours
    of _t2, and another where _t1 is more than 12 hours before _t2.
    Parameters:
        _t1 (int): The first time point, representing a moment in a day.
        _t2 (int): The second time point, used for comparison with _t1.
    Returns:
        bool: True if _t1 is earlier than _t2, False otherwise.
    """
    return 12 > (_t1 - _t2) >= 0 or (_t1 - _t2) < -12


def get_time_different(_t1, _t2):
    """
    Calculate the shortest different between two time without considering the specific dates.
    The different between two time can be either the direct distance or the indirect distance through the 24-hour cycle, whichever is smaller.
    Parameters:
        _t1 (int): The first time point in hours.
        _t2 (int): The second time point in hours.
    Returns:
        int: The shortest distance between the two time points.
    """
    return min(abs(_t1 - _t2), 24 - abs(_t1 - _t2))


# 0.5h = 30min
def calculate_temporal_similarity(_time_span1, _time_span2, _expansion_coefficient=0.5):
    """
    Calculate the temporal similarity coefficient between two ride records, which was first proposed by Yao et al.(2018).
    In our study, we added the expansion coefficient and did not consider the specific date of the ride record during clustering
    Parameters:
        _time_span1: list, represents the time span of the first ride record.
        _time_span2: list, represents the time span of the second ride record.
        _expansion_coefficient: float, the expansion coefficient for the time span, default is 0.5.
    Returns:
        float, the temporal similarity coefficient between the two ride records.
    """
    _extended_time_span1 = [_time_span1[0] - _expansion_coefficient, _time_span1[1] + _expansion_coefficient]
    _extended_time_span2 = [_time_span2[0] - _expansion_coefficient, _time_span2[1] + _expansion_coefficient]

    # Ensure the corrected time span does not exceed 24 hours
    if _extended_time_span1[0] - _expansion_coefficient < 0:
        _extended_time_span1[0] += 24
    if _extended_time_span1[1] + _expansion_coefficient >= 24:
        _extended_time_span1[1] -= 24
    if _extended_time_span2[0] - _expansion_coefficient < 0:
        _extended_time_span2[0] += 24
    if _extended_time_span2[1] + _expansion_coefficient >= 24:
        _extended_time_span2[1] -= 24
    # Calculate the temporal similarity coefficient based on different time span scenarios
    if t1_is_earlier_than_t2(_extended_time_span1[0], _extended_time_span2[0]) is True and t1_is_earlier_than_t2(
            _extended_time_span1[1], _extended_time_span2[1]) is False:
        return 1 if get_time_different(_extended_time_span1[0], _extended_time_span1[1]) < get_time_different(
            _extended_time_span2[0],
            _extended_time_span2[1]) else 0
    elif t1_is_earlier_than_t2(_extended_time_span1[0], _extended_time_span2[0]) is False and t1_is_earlier_than_t2(
            _extended_time_span1[1], _extended_time_span2[1]) is True:
        return 1 if get_time_different(_extended_time_span2[0], _extended_time_span2[1]) < get_time_different(
            _extended_time_span1[0],
            _extended_time_span1[1]) else 0
    elif t1_is_earlier_than_t2(_extended_time_span1[1], _extended_time_span2[0]) is False or t1_is_earlier_than_t2(
            _extended_time_span2[1], _extended_time_span1[0]) is False:
        return 0
    else:
        _laser_flow_end_time = max(_extended_time_span1[1], _extended_time_span2[1])
        _earlier_flow_end_time = min(_extended_time_span1[1], _extended_time_span2[1])
        _laser_flow_start_time = max(_extended_time_span1[0], _extended_time_span2[0])
        _earlier_flow_start_time = min(_extended_time_span1[0], _extended_time_span2[0])
        return get_time_different(_earlier_flow_end_time, _laser_flow_start_time) / get_time_different(_earlier_flow_start_time,
                                                                                             _laser_flow_end_time)
