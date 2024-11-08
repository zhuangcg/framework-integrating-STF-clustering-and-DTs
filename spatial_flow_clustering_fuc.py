# encoding: utf-8
import math

from shapely import Point, LineString
import folium
from folium.plugins import AntPath, Fullscreen
from utils import webmercator_to_wgs84, get_distance


class SpatialClusterFlow:
    def __init__(self, _sfc_id, _flow_geom, _record_detail):
        if isinstance(_sfc_id, int):
            self.sfc_id = f'sfc{str(_sfc_id).zfill(3)}'
        else:
            self.sfc_id = _sfc_id
        self.flow = _flow_geom
        self.origin = Point(_flow_geom.coords[0][0], _flow_geom.coords[0][1])
        self.destination = Point(_flow_geom.coords[1][0], _flow_geom.coords[1][1])
        self.including_record_detail = _record_detail
        self.record_num = len(self.including_record_detail)

    def add_flow_geometry(self, _another_flow_geom, _self_weight=0.5, _another_weight=0.5):
        another_flow_origin = Point(_another_flow_geom.coords[0][0], _another_flow_geom.coords[0][1])
        another_flow_destination = Point(_another_flow_geom.coords[1][0], _another_flow_geom.coords[1][1])
        self.origin = Point((self.origin.x * _self_weight + another_flow_origin.x * _another_weight),
                            (self.origin.y * _self_weight + another_flow_origin.y * _another_weight))
        self.destination = Point(
            (self.destination.x * _self_weight + another_flow_destination.x * _another_weight),
            (self.destination.y * _self_weight + another_flow_destination.y * _another_weight))
        self.flow = LineString([self.origin, self.destination])

    def add_flow(self, _another_flow_geom, _another_record_detail, _weight=False):
        if not isinstance(_another_record_detail, dict):
            raise TypeError('_another_record_uuid_list must be a dict')
        else:
            _another_record_uuid_list = list(_another_record_detail.keys())
            if _weight:
                self_weight = len(self.including_record_detail) / (
                        len(_another_record_uuid_list) + len(self.including_record_detail))
                another_weight = len(_another_record_uuid_list) / (
                        len(_another_record_uuid_list) + len(self.including_record_detail))
                self.add_flow_geometry(_another_flow_geom, self_weight, another_weight)
            else:
                self.add_flow_geometry(_another_flow_geom)
            for _uuid in _another_record_uuid_list:
                if _uuid not in self.including_record_detail.keys():
                    self.including_record_detail[_uuid] = _another_record_detail[_uuid]
            self.record_num = len(self.including_record_detail)


def init_bike_record_with_sfc_obj(_record_list):
    # return
    _bike_record_dict = {}
    _init_spatial_flow_cluster_dict = {}
    for _row, _record_info in enumerate(_record_list):
        _uuid = _record_info['uuid']
        _origin = [_record_info['origin_x'], _record_info['origin_y']]
        _destination = [_record_info['destination_x'], _record_info['destination_y']]
        _flow_geom = LineString([_origin, _destination])

        # create init sfc and
        _init_spatial_flow_cluster = SpatialClusterFlow(
            int(_row), _flow_geom, {
                _uuid: {
                    'origin': _origin, 'destination': _destination,
                    'start_time': _record_info['start_time'],
                    'end_time': _record_info['end_time'], 'date': _record_info['date']}})
        _init_spatial_flow_cluster_dict[_uuid] = _init_spatial_flow_cluster

        _bike_record_dict[_uuid] = {'sfc_id': _init_spatial_flow_cluster.sfc_id,
                                    'centroid': [(_origin[0] + _destination[0]) / 2,
                                                 (_origin[1] + _destination[1]) / 2],
                                    'distance': _flow_geom.length}

    return _bike_record_dict, _init_spatial_flow_cluster_dict


def get_near_record_uuid_list(_record_dict, _this_uuid, _this_sfc_id, _size_coefficient=0.3):
    _this_flow_centroid = _record_dict[_this_uuid]['centroid']
    _this_flow_length = _record_dict[_this_uuid]['distance']
    _near_record_uuid_list = []
    _distance_threshold = 1.4142 * _this_flow_length * _size_coefficient
    for _uuid, _record_detail in _record_dict.items():
        _sfc_id = _record_detail['sfc_id']
        if _uuid != _this_uuid and _sfc_id != _this_sfc_id:
            _flow_centroid = _record_detail['centroid']
            if get_distance(_flow_centroid, _this_flow_centroid) <= _distance_threshold:
                _near_record_uuid_list.append(_uuid)
    return _near_record_uuid_list


def calculate_spatial_dissimilarity(_sf1, _sf2, _size_coefficient=0.3, _max_circle_boundary_radius=200):
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
    sd_0 = get_distance([_sf1_origin.x, _sf1_origin.y], [_sf2_origin.x, _sf2_origin.y]) / _circle_boundary_radius
    sd_1 = get_distance([_sf1_destination.x, _sf1_destination.y],
                        [_sf2_destination.x, _sf2_destination.y]) / _circle_boundary_radius
    return math.sqrt(sd_0 ** 2 + sd_1 ** 2)


def plot_sfc_obj(_sfc_obj, _uid='Test'):
    if isinstance(_sfc_obj, SpatialClusterFlow):
        _lon_list, _lat_list = [], []
        _wgs84_sfc_origin = webmercator_to_wgs84(
            _sfc_obj.origin.x, _sfc_obj.origin.y)
        _wgs84_sfc_destination = webmercator_to_wgs84(
            _sfc_obj.destination.x, _sfc_obj.destination.y)
        _sfc_origin = [_wgs84_sfc_origin[1], _wgs84_sfc_origin[0]]
        _sfc_destination = [_wgs84_sfc_destination[1], _wgs84_sfc_destination[0]]

        _record_od_list = []
        for _uuid, _record_info in _sfc_obj.including_record_detail.items():
            _wgs84_origin = webmercator_to_wgs84(*_record_info['origin'])
            _wgs84_destination = webmercator_to_wgs84(*_record_info['destination'])
            _record_od_list.append([_wgs84_origin, _wgs84_destination, _record_info['date']])
            _lon_list.extend([_wgs84_origin[0], _wgs84_destination[0]])
            _lat_list.extend([_wgs84_origin[1], _wgs84_destination[1]])

        _bound = [[min(_lat_list), min(_lon_list)], [max(_lat_list), max(_lon_list)]]
        _m = folium.Map(zoom_start=8)
        _m.fit_bounds(_bound)
        _radius = 200
        folium.Circle(location=_sfc_origin, radius=_radius, color='red', fill=True, fill_color='red', fill_opacity=0.1
                      ).add_to(_m)
        folium.Circle(location=_sfc_destination, radius=_radius, color='red', fill=True, fill_color='Red',
                      fill_opacity=0.1  # 填充透明度
                      ).add_to(_m)

        for _record_od in _record_od_list:
            AntPath([[_record_od[0][1], _record_od[0][0]], [_record_od[1][1], _record_od[1][0]]],
                    tooltip=_record_od[-1],
                    color="red", weight=0.75, dash_array='15,15', delay=2000).add_to(_m)

        folium.Marker(_sfc_origin,
                      tooltip="Origin",
                      icon=folium.Icon(icon="fa-solid fa-o", prefix='fa', color="green")).add_to(_m)
        folium.Marker(_sfc_destination, tooltip="Destination",
                      icon=folium.Icon(icon="fa-solid fa-d", prefix='fa')).add_to(_m)
        folium.PolyLine([_sfc_origin, _sfc_destination], tooltip=_sfc_obj.sfc_id,
                        color="red", weight=5).add_to(_m)

        # 创建一个 HTML 标题
        title_html = f'''
        <div style="position: absolute; 
                   top: 10px; 
                   left: 50px; 
                   background-color: rgba(255, 255, 255, 0.8); 
                   padding: 10px; 
                   border: 1px solid #ccc; 
                   border-radius: 5px; 
                   z-index: 1000;">
            <h3 style="margin: 0; font-size: 16px;"><b>User ID: {_uid}; SFC ID: {_sfc_obj.sfc_id}</b></h3>
        </div>
        '''
        _m.get_root().html.add_child(folium.Element(title_html))
        Fullscreen().add_to(_m)
        return _m

    else:
        raise TypeError('_another_record_uuid_list must be a SpatialClusterFlow class')
