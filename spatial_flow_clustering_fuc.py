# encoding: utf-8
# The original spatial flow clustering method we used was proposed by Gao et al.(2020). The article is linked as follows:
# https://doi.org/10.1109/ACCESS.2020.3040852

import math
import numpy as np
from shapely import Point, LineString
from utils import get_distance

class SpatialClusterFlow:
    def __init__(self, _sfc_id, _flow_geom, _record_detail):
        if isinstance(_sfc_id, int):
            self.sfc_id = f'sfc{str(_sfc_id).zfill(3)}'
        else:
            self.sfc_id = _sfc_id
        self.flow = _flow_geom
        self.origin = _flow_geom.coords[0]
        self.destination = _flow_geom.coords[1]
        self.including_record_detail = _record_detail
        self.record_num = len(self.including_record_detail)

    # The OD point of a spatial flow cluster is determined by the mean of the OD points of all the ride records it includes
    def add_flow_geometry(self, _another_record_detail):
        _flow_origin_list = []
        _flow_destination_list = []
        for _uuid, _record_info in _another_record_detail.items():
            _flow_origin_list.append(_record_info['origin'])
            _flow_destination_list.append(_record_info['destination'])
        for _uuid, _record_info in self.including_record_detail.items():
            _flow_origin_list.append(_record_info['origin'])
            _flow_destination_list.append(_record_info['destination'])
        self.origin = np.mean(_flow_origin_list, axis=0)
        self.destination = np.mean(_flow_destination_list, axis=0)
        self.flow = LineString([self.origin, self.destination])

    def add_flow(self, _another_record_detail):
        if not isinstance(_another_record_detail, dict):
            raise TypeError('_another_record_uuid_list must be a dict')
        else:
            _another_record_uuid_list = list(_another_record_detail.keys())
            self.add_flow_geometry(_another_record_detail)
            for _uuid in _another_record_uuid_list:
                if _uuid not in self.including_record_detail.keys():
                    self.including_record_detail[_uuid] = _another_record_detail[_uuid]
            self.record_num = len(self.including_record_detail)


#
def init_bike_record_with_sfc_obj(_record_list):
    """
       Creat initial spatial flow clusters corresponding to each ride riding record.
       Parameters:
            -_record_list (list): A list containing bike ride record information, where each record is a dictionary containing origin, destination, start time, end time, and date.
       Returns:
            -tuple: A tuple containing two dictionaries, the first is the bike ride record dictionary (including belonging SFC ID), the second is the initial spatial flow cluster dictionary.
    """
    _bike_record_dict = {}
    _init_spatial_flow_cluster_dict = {}
    for _row, _record_info in enumerate(_record_list):
        _uuid = _record_info['uuid']
        _origin = [_record_info['origin_x'], _record_info['origin_y']]
        _destination = [_record_info['destination_x'], _record_info['destination_y']]
        _flow_geom = LineString([_origin, _destination])

        _init_spatial_flow_cluster = SpatialClusterFlow(
            int(_row), _flow_geom, {
                _uuid: {
                    'origin': _origin, 'destination': _destination,
                    'start_time': _record_info['start_time'],
                    'end_time': _record_info['end_time'], 'date': _record_info['date']}})
        _init_spatial_flow_cluster_dict[_uuid] = _init_spatial_flow_cluster
        # The centroid and distance attributes is used for subsequent clustering processing
        _bike_record_dict[_uuid] = {'sfc_id': _init_spatial_flow_cluster.sfc_id,
                                    'centroid': [(_origin[0] + _destination[0]) / 2,
                                                 (_origin[1] + _destination[1]) / 2],
                                    'distance': _flow_geom.length}

    return _bike_record_dict, _init_spatial_flow_cluster_dict



def get_near_record_uuid_list(_record_dict, _this_uuid, _this_sfc_id, _size_coefficient=0.3):
    """
        Get a list of UUIDs for ride records that are near the given ride record.
        Parameters:
            _record_dict (dict): A dictionary containing all records, where each key is a UUID and the value is a dictionary of record details.
            _this_uuid (str): The UUID of the current ride record.
            _this_sfc_id (int): The SFC ID to whom the current ride record belongs.
            _size_coefficient (float): The coefficient for the distance threshold, default is 0.3 with reference to Gao et al.(2020).
        Returns:
            list: A list of UUIDs for nearby ride records.
    """
    _this_flow_centroid = _record_dict[_this_uuid]['centroid']
    _this_flow_length = _record_dict[_this_uuid]['distance']
    _near_record_uuid_list = []
    # 1.4142 is equal to sqrt(2)
    _distance_threshold = 1.4142 * _this_flow_length * _size_coefficient
    for _uuid, _record_detail in _record_dict.items():
        _sfc_id = _record_detail['sfc_id']
        if _uuid != _this_uuid and _sfc_id != _this_sfc_id:
            _flow_centroid = _record_detail['centroid']
            if get_distance(_flow_centroid, _this_flow_centroid) <= _distance_threshold:
                _near_record_uuid_list.append(_uuid)
    return _near_record_uuid_list


def calculate_spatial_dissimilarity(_sf1, _sf2, _size_coefficient=0.3, _max_circle_boundary_radius=200):
    """
        Calculate the spatial dissimilarity coefficient between two spatial flow clusters, which was proposed by Gao et al.(2020).
        Parameters:
            _sf1: SpatialFlow object representing the first spatial flow.
            _sf2: SpatialFlow object representing the second spatial flow.
            _size_coefficient: float, the size coefficient used to calculate the circle boundary radius, default is 0.3.
            _max_circle_boundary_radius: int, the maximum value for the circle boundary radius, default is 200.
        Returns:
            float, the spatial dissimilarity coefficient between the two spatial flow clusters.
    """
    _sf1_origin = _sf1.origin
    _sf1_destination = _sf1.destination
    _sf1_distance = _sf1.flow.length
    _sf2_origin = _sf2.origin
    _sf2_destination = _sf2.destination
    _sf2_distance = _sf2.flow.length
    _min_flow_length = float(min([_sf1_distance, _sf2_distance]))
    if _min_flow_length  * _size_coefficient >= _max_circle_boundary_radius:
        _circle_boundary_radius = _max_circle_boundary_radius
    else:
        _circle_boundary_radius = _min_flow_length  * _size_coefficient
    sd_0 = get_distance(_sf1_origin, _sf2_origin) / _circle_boundary_radius
    sd_1 = get_distance(_sf1_destination, _sf2_destination) / _circle_boundary_radius
    return math.sqrt(sd_0 ** 2 + sd_1 ** 2)

