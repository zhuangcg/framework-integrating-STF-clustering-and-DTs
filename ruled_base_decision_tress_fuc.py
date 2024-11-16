# encoding: utf-8
# Construct multiple decision trees to identify users' commuting patterns and commuting categories from their spatiotemporal flow clusters

from scipy.optimize import brent
from shapely import LineString
from utils import time_to_hour, get_distance, are_endpoints_far_apart


class SimplifiedCommutingFlow:
    def __init__(self, _earlier_stfc, _later_stfc):
        self.cf_id = f'{_earlier_stfc.stfc_id}_{_later_stfc.stfc_id}'
        self.earlier_stfc = _earlier_stfc
        self.later_stfc = _later_stfc
        self.earlier_travel_time = self.earlier_stfc.start_time
        self.later_travel_time = self.later_stfc.start_time
        self.earlier_cycling_duration = abs(
            time_to_hour(self.earlier_stfc.start_time) - time_to_hour(self.earlier_stfc.end_time))
        self.later_cycling_duration = abs(
            time_to_hour(self.later_stfc.start_time) - time_to_hour(self.later_stfc.end_time))
        self.flow = self.get_cf_flow()
        self.commuting_distance = get_distance(*self.flow.coords)
        self.working_hour = time_to_hour(self.later_stfc.start_time) - time_to_hour(self.earlier_stfc.end_time)
        self.total_record_num = self.earlier_stfc.stfc_record_num + self.later_stfc.stfc_record_num
        self.cycling_round_trip_rate = self.earlier_stfc.stfc_record_num / self.total_record_num
        self.transfer_type = None
        self.transfer_station_id = None
        self.transfer_station_location = None

    def get_cf_flow(self, _self_weight=0.5, _another_weight=0.5):
        _earlier_origin, _earlier_destination = self.earlier_stfc.flow.coords
        _later_origin, _later_destination = self.later_stfc.flow.coords
        _origin = [(_earlier_origin[0] * _self_weight + _later_destination[0] * _another_weight),
                   (_earlier_origin[1] * _self_weight + _later_destination[1] * _another_weight)]
        _destination = [(_earlier_destination[0] * _self_weight + _later_origin[0] * _another_weight),
                        (_earlier_destination[1] * _self_weight + _later_origin[1] * _another_weight)]
        return LineString([_origin, _destination])


class DailyCommutingFlow:
    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], SimplifiedCommutingFlow):
            _dcf = args[0]
            self.dcf_id = _dcf.cf_id
            self.cycling_round_trip_rate = _dcf.cycling_round_trip_rate
            self.total_record_num = _dcf.total_record_num
            if _dcf.transfer_type is None:
                self.home_location = _dcf.flow.coords[0]
                self.work_location = _dcf.flow.coords[1]
                self.to_transit_location = None
                self.to_transit_station_id = None
                self.to_transit_station_location = None
                self.from_transit_location = None
                self.from_transit_station_id = None
                self.from_transit_station_location = None
                self.moment_leave_home = _dcf.earlier_travel_time
                self.moment_leave_work = _dcf.later_travel_time
                self.duration_to_work = _dcf.earlier_cycling_duration
                self.duration_back_home = _dcf.later_cycling_duration
                self.commuting_distance = _dcf.commuting_distance
                self.working_hours = _dcf.working_hour
                self.commuting_category = 'Only-biking'
            elif _dcf.transfer_type == 'transit_biking':
                self.home_location = None
                self.work_location = _dcf.flow.coords[1]
                self.to_transit_location = None
                self.to_transit_station_id = None
                self.to_transit_station_location = None
                self.from_transit_location = _dcf.flow.coords[0]
                self.from_transit_station_id = _dcf.transfer_station_id
                self.from_transit_station_location = _dcf.transfer_station_location
                self.moment_leave_home = None
                self.moment_leave_work = _dcf.later_travel_time
                self.duration_to_work = None
                self.duration_back_home = None
                self.commuting_distance = None
                self.working_hours = _dcf.working_hour
                self.commuting_category = 'Transit-biking'
            elif _dcf.transfer_type == 'biking_transit':
                self.home_location = _dcf.flow.coords[0]
                self.work_location = None
                self.to_transit_location = _dcf.flow.coords[1]
                self.to_transit_station_id = _dcf.transfer_station_id
                self.to_transit_station_location = _dcf.transfer_station_location
                self.from_transit_location = None
                self.from_transit_station_id = None
                self.from_transit_station_location = None
                self.moment_leave_home = _dcf.earlier_travel_time
                self.moment_leave_work = None
                self.duration_to_work = None
                self.duration_back_home = None
                self.commuting_distance = None
                self.working_hours = None
                self.commuting_category = 'Biking-transit'
            else:
                raise ValueError('transfer type error')
        elif len(args) == 2 and isinstance(args[0], SimplifiedCommutingFlow) and isinstance(args[1],
                                                                                            SimplifiedCommutingFlow):
            _dcf, _adcf = args
            if _dcf.transfer_type == 'transit_biking' and _adcf.transfer_type == 'biking_transit':
                self.dcf_id = f'{_adcf.cf_id}_&_{_dcf.cf_id}'
                self.cycling_round_trip_rate = round((_dcf.cycling_round_trip_rate + _adcf.cycling_round_trip_rate) / 2,
                                                     3)
                self.total_record_num = _dcf.total_record_num + _adcf.total_record_num
                self.home_location = _adcf.flow.coords[0]
                self.work_location = _dcf.flow.coords[1]
                self.to_transit_location = _adcf.flow.coords[1]
                self.to_transit_station_id = _adcf.transfer_station_id
                self.to_transit_station_location = _adcf.transfer_station_location
                self.from_transit_location = _dcf.flow.coords[0]
                self.from_transit_station_id = _dcf.transfer_station_id
                self.from_transit_station_location = _dcf.transfer_station_location
                self.moment_leave_home = _adcf.earlier_travel_time
                self.moment_leave_work = _dcf.later_travel_time
                self.duration_to_work = abs(time_to_hour(_dcf.earlier_travel_time) - time_to_hour(
                    _adcf.earlier_travel_time)) + _dcf.earlier_cycling_duration
                self.duration_back_home = abs(time_to_hour(_adcf.later_travel_time) - time_to_hour(
                    _dcf.later_travel_time)) + _adcf.later_cycling_duration
                self.commuting_distance = get_distance(self.home_location, self.work_location)
                self.working_hours = _dcf.working_hour
                self.commuting_category = 'Biking-transit-biking'
            elif _dcf.transfer_type == 'biking_transit' and _adcf.transfer_type == 'transit_biking':
                self.dcf_id = f'{_dcf.cf_id}_&_{_adcf.cf_id}'
                self.cycling_round_trip_rate = round((_dcf.cycling_round_trip_rate + _adcf.cycling_round_trip_rate) / 2,
                                                     3)
                self.total_record_num = _dcf.total_record_num + _adcf.total_record_num
                self.home_location = _dcf.flow.coords[0]
                self.work_location = _adcf.flow.coords[1]
                self.to_transit_location = _dcf.flow.coords[1]
                self.to_transit_station_id = _dcf.transfer_station_id
                self.to_transit_station_location = _dcf.transfer_station_location
                self.from_transit_location = _adcf.flow.coords[0]
                self.from_transit_station_id = _adcf.transfer_station_id
                self.from_transit_station_location = _adcf.transfer_station_location
                self.moment_leave_home = _dcf.earlier_travel_time
                self.moment_leave_work = _adcf.later_travel_time
                self.duration_to_work = abs(time_to_hour(_adcf.earlier_travel_time) - time_to_hour(
                    _dcf.earlier_travel_time)) + _adcf.earlier_cycling_duration
                self.duration_back_home = abs(time_to_hour(_dcf.later_travel_time) - time_to_hour(
                    _adcf.later_travel_time)) + _dcf.later_cycling_duration
                self.commuting_distance = get_distance(self.home_location, self.work_location)
                self.working_hours = _adcf.working_hour
                self.commuting_category = 'Biking-transit-biking'
            else:
                raise ValueError(
                    f'transfer types for cf1 and cf2 are {args[0].transfer_type} and {args[1].transfer_type}, they do not fulfil the input requirements')
        else:
            raise ValueError('Only input one SimplifiedCommutingFlow or two SimplifiedCommutingFlows')


def identify_candidate_commuting_flow(_stfc1_obj, _stfc2_obj, _boundary_circle_radius=200, _working_hours_threshold=4):
    """
    Identify and return possible commuting flows based on two spatiotemporal flow clusters.
    Parameters:
        _stfc1_obj, _stfc2_obj (Flow): Two spatiotemporal flow clusters (stfc) to be evaluated.
        _boundary_circle_radius (int): The radius defining the boundary circle around the start and end points, used to determine  the proximity of the two opposite end points of two stfc, default is 200.
        _working_hours_threshold (int): The minimum number of hours required between the end time of the earlier flow and the start time of the later flow to be considered commuting, default is 4.
    Returns:
        SimplifiedCommutingFlow: Returns a simplified commuting flow object if the two stfc meet the commuting conditions.
        bool: Returns False if the two stfc do not meet the commuting conditions.
    """
    if abs(time_to_hour(_stfc1_obj.start_time) - 8) < abs(time_to_hour(_stfc2_obj.start_time) - 8):
        _earlier_stfc, _later_stfc = _stfc1_obj, _stfc2_obj
    else:
        _earlier_stfc, _later_stfc = _stfc2_obj, _stfc1_obj
    _earlier_stfc_o, _earlier_stfc_d = _stfc1_obj.flow.coords
    _later_stfc_o, _later_stfc_d = _stfc2_obj.flow.coords

    if get_distance(_earlier_stfc_o, _later_stfc_d) <= 2 * _boundary_circle_radius and get_distance(_earlier_stfc_d,
                                                                                                    _later_stfc_o) <= 2 * _boundary_circle_radius:
        _earlier_stfc_end_time = time_to_hour(_earlier_stfc.end_time)
        _later_stfc_start_time = time_to_hour(_later_stfc.start_time)
        _working_hours = _later_stfc_start_time - _earlier_stfc_end_time
        if _working_hours < 0:
            _working_hours += 24
        if _working_hours >= _working_hours_threshold:
            if _working_hours < 16:
                return SimplifiedCommutingFlow(_earlier_stfc, _later_stfc)
            else:
                return SimplifiedCommutingFlow(_later_stfc, _earlier_stfc)

    return False


def identify_transfer_commuting_flow(_cf_obj, _public_station_k_tree, _public_station_df, _transfer_distance_threshold):
    """
    Identify and set the transfer type and station information for commuting flows that satisfy the conditions.
    Parameters:
        _cf_obj: Object representing the commuting flow, containing information such as travel time, origin and destination coordinates, and flow length.
        _public_station_k_tree: A k-d tree data structure for quickly querying the nearest metro entrances or bus station.
        _public_station_df: A DataFrame containing information about metro entrances or bus station, such as coordinates and station IDs.
        _transfer_distance_threshold: The maximum distance threshold for determining whether a transfer is possible.
    Returns:
        _cf_obj: The input commuting flow object, with its transfer type and, if applicable, station information set.
    """
    if 6 < time_to_hour(_cf_obj.earlier_travel_time) < 23.5:
        _cf_origin = _cf_obj.flow.coords[0]
        _cf_destination = _cf_obj.flow.coords[1]
        _cf_distance = _cf_obj.flow.length
        _origin_nearest_entrance_dist, _origin_nearest_entrance_id = _public_station_k_tree.query(_cf_origin)
        _destination_nearest_entrance_dist, _metro_destination_entrance_id = _public_station_k_tree.query(
            _cf_destination)

        if _origin_nearest_entrance_dist <= _transfer_distance_threshold and _origin_nearest_entrance_dist < _destination_nearest_entrance_dist and _destination_nearest_entrance_dist * 2 > _cf_distance:
            _cf_obj.transfer_type = 'transit_biking'
            # The code in this section is not flexible enough and needs to be adapted to the specific fields of the public transport station data
            _transfer_station_info = _public_station_df.iloc[_origin_nearest_entrance_id, :].to_dict()
            _cf_obj.transfer_station_id = _transfer_station_info['pid']
            _cf_obj.transfer_station_location = [_transfer_station_info['x_coord'], _transfer_station_info['y_coord']]
        elif _destination_nearest_entrance_dist <= _transfer_distance_threshold and _destination_nearest_entrance_dist < _origin_nearest_entrance_dist and _origin_nearest_entrance_dist * 2 > _cf_distance:
            _cf_obj.transfer_type = 'biking_transit'
            # The code in this section is not flexible enough and needs to be adapted to the specific fields of the public transport station data
            _transfer_station_info = _public_station_df.iloc[_metro_destination_entrance_id, :].to_dict()
            _cf_obj.transfer_station_id = _transfer_station_info['pid']
            _cf_obj.transfer_station_location = [_transfer_station_info['x_coord'], _transfer_station_info['y_coord']]
        else:
            # including _origin_nearest_entrance_dist > _transfer_distance_threshold and _destination_nearest_entrance_dist > _transfer_distance_threshold
            pass
    return _cf_obj


def identify_user_commuting_category(_cf_set_dict):
    """
    Identify the user's commuting category based on their commuting flows set.
    Parameters:
        - _cf_set_dict: dict, containing travel record objects for different transportation modes.
    Returns:
        - An instance of DailyCommutingFlow representing the user's commuting category.
    Raises:
        - TypeError: If the `transfer_type` attribute value is not as expected.
    """
    _dcf_id, _dcf_obj = sorted(_cf_set_dict.items(), key=lambda item: item[1].total_record_num, reverse=True)[0]
    if _dcf_obj.transfer_type is None:
        return DailyCommutingFlow(_dcf_obj)
    elif _dcf_obj.transfer_type == 'transit_biking':
        _adcf = find_another_daily_commuting_flow(_dcf_obj, _cf_set_dict)
        if _adcf:
            return DailyCommutingFlow(_dcf_obj, _adcf)
        else:
            return DailyCommutingFlow(_dcf_obj)
    elif _dcf_obj.transfer_type == 'biking_transit':
        _adcf = find_another_daily_commuting_flow(_dcf_obj, _cf_set_dict)
        if _adcf:
            return DailyCommutingFlow(_dcf_obj, _adcf)
        else:
            return DailyCommutingFlow(_dcf_obj)
    else:
        raise TypeError('transfer_type error')


def find_another_daily_commuting_flow(_dcf_obj, _cf_set_dict):
    """
    Find another commuting flow object that meets specific conditions based on the given daily commuting flow object and a dictionary of commuting flow sets.
    Parameters:
        _dcf_obj: A DailyCommutingFlow object representing a daily commuting flow.
        _cf_set_dict: A dictionary containing multiple CommutingFlow objects, where the keys are commuting flow IDs and the values are CommutingFlow objects.
    Returns:
        If a suitable CommutingFlow object is found, it is returned; otherwise, False is returned.
    """
    if len(_cf_set_dict) > 1:
        _sorted_cf_set = sorted(_cf_set_dict.items(), key=lambda item: item[1].total_record_num, reverse=True)
        _dcf_transfer_type = _dcf_obj.transfer_type
        _dcf_flow_coords = _dcf_obj.flow.coords
        for _cf_id, _cf_obj in _sorted_cf_set:
            if _cf_id != _dcf_obj.cf_id and _cf_obj.transfer_type and _cf_obj.transfer_type != _dcf_transfer_type and _cf_obj.transfer_station_id != _dcf_obj.transfer_station_id:
                if abs(time_to_hour(_cf_obj.later_travel_time) - time_to_hour(_dcf_obj.later_travel_time) - _dcf_obj.later_cycling_duration) <= 2 or abs(
                        time_to_hour(_cf_obj.earlier_travel_time) - time_to_hour(_dcf_obj.earlier_travel_time) - _cf_obj.earlier_cycling_duration) <= 2:
                    _cf_flow_coords = _cf_obj.flow.coords
                    _dist_threshold = min(_dcf_obj.flow.length, _cf_obj.flow.length) * 0.3
                    _dist_threshold = 200 if _dist_threshold > 200 else _dist_threshold
                    if are_endpoints_far_apart(_cf_flow_coords, _dcf_flow_coords, _dist_threshold * 2):
                        return _cf_obj

    return False
