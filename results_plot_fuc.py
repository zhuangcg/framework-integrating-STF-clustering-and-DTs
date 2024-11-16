# encoding: utf-8
# Visualizing the results of spatial flow clusters, spatiotemporal flow clusters and daily commuting flows

import folium
from folium.plugins import AntPath, Fullscreen
from utils import webmercator_to_wgs84, get_distance
from spatial_flow_clustering_fuc import SpatialClusterFlow
from spatiotemporal_flow_clustering_fuc import SpatioTemporalFlowCluster
from ruled_base_decision_tress_fuc import DailyCommutingFlow

# AN HTML template
_html_template = '''
<div style="position: absolute; 
           top: 10px; 
           left: 50px; 
           background-color: rgba(255, 255, 255, 0.8); 
           padding: 10px; 
           border: 1px solid #ccc; 
           border-radius: 5px; 
           z-index: 1000;">
           {0}
</div>
<div style="position: absolute; 
           bottom: 30px; 
           left: 20px; 
           background-color: rgba(255, 255, 255, 0.8); 
           padding: 10px; 
           border: 1px solid #ccc; 
           border-radius: 5px; 
           z-index: 1000;">
           {1}
</div>'''


def plot_sfc_obj(_sfc_obj, _uid='Test'):
    """
    Plot the origin and destination of a SpatialClusterFlow object on a folium map, along with related flow information.
    Parameters:
        - _sfc_obj: SpatialClusterFlow object, containing flow information including origin, destination, and detailed records.
        - _uid: User ID, used for display on the map interface. Default is 'Test'.
    Returns:
        - _m: folium.Map object, showing the spatial flow information including origin, destination, and flow paths.
    Raises:
        TypeError: If _sfc_obj is not an instance of SpatialClusterFlow.
    """
    if isinstance(_sfc_obj, SpatialClusterFlow):
        _wgs84_sfc_origin = webmercator_to_wgs84(
            *_sfc_obj.origin)
        _wgs84_sfc_destination = webmercator_to_wgs84(
            *_sfc_obj.destination)
        _sfc_origin = _wgs84_sfc_origin[::-1]
        _sfc_destination = _wgs84_sfc_destination[::-1]

        _record_od_list = []
        _lon_list, _lat_list = [], []
        for _uuid, _record_info in _sfc_obj.including_record_detail.items():
            _wgs84_origin = webmercator_to_wgs84(*_record_info['origin'])
            _wgs84_destination = webmercator_to_wgs84(*_record_info['destination'])
            _record_od_list.append([_wgs84_origin, _wgs84_destination, _record_info['date']])
            _lon_list.extend([_wgs84_origin[0], _wgs84_destination[0]])
            _lat_list.extend([_wgs84_origin[1], _wgs84_destination[1]])

        _bound = [[min(_lat_list), min(_lon_list)], [max(_lat_list), max(_lon_list)]]
        _m = folium.Map(zoom_start=8)
        _m.fit_bounds(_bound)
        folium.Circle(location=_sfc_origin, radius=200, color='#ca1d2a', fill=True, fill_color='#ca1d2a',
                      fill_opacity=0.1
                      ).add_to(_m)
        folium.Circle(location=_sfc_destination, radius=200, color='#ca1d2a', fill=True, fill_color='#ca1d2a',
                      fill_opacity=0.1
                      ).add_to(_m)

        for _record_od in _record_od_list:
            AntPath([_record_od[0][::-1], _record_od[1][::-1]],
                    tooltip=_record_od[-1],
                    color="#ca1d2a", weight=0.75, dash_array='15,15', delay=2000).add_to(_m)

        folium.Marker(_sfc_origin,
                      tooltip="Origin",
                      icon=folium.Icon(icon="fa-solid fa-o", prefix='fa', color="green")).add_to(_m)
        folium.Marker(_sfc_destination, tooltip="Destination",
                      icon=folium.Icon(icon="fa-solid fa-d", prefix='fa')).add_to(_m)
        folium.PolyLine([_sfc_origin, _sfc_destination], tooltip=_sfc_obj.sfc_id,
                        color="#ca1d2a", weight=5).add_to(_m)

        _html_content = f"""
            <h3 style="margin: 0; font-size: 16px;"><b>User ID: {_uid}</b></h3>
            <h3 style="margin: 0; font-size: 16px;"><b>SFC ID: {_sfc_obj.sfc_id}</b></h3>
            <h3 style="margin: 0; font-size: 16px;"><b>Flows Number: {_sfc_obj.record_num}</b></h3>
        """
        _html = _html_template.format(_html_content, '')
        _m.get_root().html.add_child(folium.Element(_html))
        Fullscreen().add_to(_m)
        return _m

    else:
        raise TypeError('_sfc_obj must be a SpatialClusterFlow class')


def plot_stfc_obj(_stfc_obj, _uid='Test'):
    """
    Plot the origin and destination of a SpatioTemporalFlowCluster object on a folium map, along with related flow information.
    Args:
        _stfc_obj: SpatialClusterFlow object, containing flow information including origin, destination, and detailed records.
        _uid: User ID, used for display on the map interface. Default is 'Test'.
    Returns:
        _m: folium.Map object, showing the spatiotemporal flow information including origin, destination, and flow paths.
    Raises:
        TypeError: If _stfc_obj is not an instance of SpatioTemporalFlowCluster.
    """
    if isinstance(_stfc_obj, SpatioTemporalFlowCluster):
        _wgs84_stfc_origin = webmercator_to_wgs84(
            *_stfc_obj.flow.coords[0])
        _wgs84_stfc_destination = webmercator_to_wgs84(
            *_stfc_obj.flow.coords[1])
        _stfc_origin = _wgs84_stfc_origin[::-1]
        _stfc_destination = _wgs84_stfc_destination[::-1]

        _record_od_list = []
        _lon_list, _lat_list = [], []
        for _uuid, _record_info in _stfc_obj.including_record_detail.items():
            _wgs84_origin = webmercator_to_wgs84(*_record_info['origin'])
            _wgs84_destination = webmercator_to_wgs84(*_record_info['destination'])
            _record_od_list.append([_wgs84_origin, _wgs84_destination, _record_info['date']])
            _lon_list.extend([_wgs84_origin[0], _wgs84_destination[0]])
            _lat_list.extend([_wgs84_origin[1], _wgs84_destination[1]])

        _bound = [[min(_lat_list), min(_lon_list)], [max(_lat_list), max(_lon_list)]]
        _m = folium.Map(zoom_start=8)
        _m.fit_bounds(_bound)

        folium.Circle(location=_stfc_origin, radius=200, color='#0ed145', fill=True, fill_color='#0ed145',
                      fill_opacity=0.1
                      ).add_to(_m)
        folium.Circle(location=_stfc_destination, radius=200, color='#0ed145', fill=True, fill_color='#0ed145',
                      fill_opacity=0.1
                      ).add_to(_m)

        for _record_od in _record_od_list:
            AntPath([_record_od[0][::-1], _record_od[1][::-1]],
                    tooltip=_record_od[-1],
                    color="#0ed145", weight=0.75, dash_array='15,15', delay=2000).add_to(_m)

        folium.Marker(_stfc_origin,
                      tooltip="Origin",
                      icon=folium.Icon(icon="fa-solid fa-o", prefix='fa', color="green")).add_to(_m)
        folium.Marker(_stfc_destination, tooltip="Destination",
                      icon=folium.Icon(icon="fa-solid fa-d", prefix='fa')).add_to(_m)
        folium.PolyLine([_stfc_origin, _stfc_destination], tooltip=_stfc_obj.stfc_id,
                        color="#0ed145", weight=5).add_to(_m)

        _html_content1 = f"""
            <h3 style="margin: 0; font-size: 16px;"><b>User ID: {_uid}</b></h3>
            <h3 style="margin: 0; font-size: 16px;"><b>SFC ID: {_stfc_obj.stfc_id}</b></h3>
            <h3 style="margin: 0; font-size: 16px;"><b>Associated SFC ID: {_stfc_obj.sfc_id}</b></h3>
            <h3 style="margin: 0; font-size: 16px;"><b>Flows Number: {_stfc_obj.stfc_record_num}</b></h3>
            <h3 style="margin: 0; font-size: 16px;"><b>Has Merge: {str(_stfc_obj.has_merged)}</b></h3>
        """
        _html_content2 = f"""
            <h3 style="margin: 0; font-size: 16px;"><b>Start Time: {_stfc_obj.start_time}</b></h3>
            <h3 style="margin: 0; font-size: 16px;"><b>End Time: {_stfc_obj.end_time}</b></h3>
        """
        _html = _html_template.format(_html_content1, _html_content2)
        _m.get_root().html.add_child(folium.Element(_html))
        Fullscreen().add_to(_m)
        return _m

    else:
        raise TypeError('_sfc_obj must be a SpatioTemporalFlowCluster class')


def plot_dcf_obj(_dcf_obj, _uid='Test'):
    """
    Plot a DailyCommutingFlow object on a folium map, along with related flow information.
    Args:
        _dcf_obj: DailyCommutingFlow object, containing flow information including origin, destination, and detailed records.
        _uid: User ID, used for display on the map interface. Default is 'Test'.
    Returns:
        _m: folium.Map object, showing the daily commuting flow information including origin, destination, and flow paths.
    Raises:
        TypeError: If _dcf_obj is not an instance of DailyCommutingFlow.
    """
    if isinstance(_dcf_obj, DailyCommutingFlow):
        _m = folium.Map(zoom_start=8)
        _lon_list, _lat_list = [], []
        if _dcf_obj.home_location:
            _wgs84_home_location = webmercator_to_wgs84(
                *_dcf_obj.home_location)
            _home_location = _wgs84_home_location[::-1]
            _lon_list.append(_home_location[1])
            _lat_list.append(_home_location[0])
            folium.Marker(_home_location, tooltip="Home Location",
                          icon=folium.Icon(icon="fa-solid fa-h", prefix='fa', color="green")).add_to(_m)
        else:
            _home_location = None
        if _dcf_obj.work_location:
            _wgs84_work_location = webmercator_to_wgs84(
                *_dcf_obj.work_location)
            _work_location = _wgs84_work_location[::-1]
            _lon_list.append(_work_location[1])
            _lat_list.append(_work_location[0])
            folium.Marker(_work_location, tooltip="Work Location",
                          icon=folium.Icon(icon="fa-solid fa-w", prefix='fa', color='red')).add_to(_m)
        else:
            _work_location = None
        if _dcf_obj.to_transit_location:
            _wgs84_to_transit_location = webmercator_to_wgs84(
                *_dcf_obj.to_transit_location)
            _to_transit_location = _wgs84_to_transit_location[::-1]
            _lon_list.append(_to_transit_location[1])
            _lat_list.append(_to_transit_location[0])
            folium.Marker(_to_transit_location, tooltip="To Transit Location",
                          icon=folium.Icon(icon="fa-solid fa-t", prefix='fa')).add_to(_m)
            _wgs84_to_transit_station_location = webmercator_to_wgs84(
                *_dcf_obj.to_transit_station_location)
            _to_transit_station_location = _wgs84_to_transit_station_location[::-1]
            _lon_list.append(_to_transit_station_location[1])
            _lat_list.append(_to_transit_station_location[0])
            folium.Circle(location=_to_transit_station_location, tooltip=_dcf_obj.to_transit_station_id, radius=60,
                          color='#0257a0', fill=True,
                          fill_color='#0257a0', fill_opacity=0.1
                          ).add_to(_m)
        else:
            _to_transit_location = None
        if _dcf_obj.from_transit_location:
            _wgs84_from_transit_location = webmercator_to_wgs84(
                *_dcf_obj.from_transit_location)
            _from_transit_location = _wgs84_from_transit_location[::-1]
            _lon_list.append(_from_transit_location[1])
            _lat_list.append(_from_transit_location[0])
            folium.Marker(_from_transit_location, tooltip="From Transit Location",
                          icon=folium.Icon(icon="fa-solid fa-f", prefix='fa')).add_to(_m)
            _wgs84_from_transit_station_location = webmercator_to_wgs84(
                *_dcf_obj.from_transit_station_location)
            _from_transit_station_location = _wgs84_from_transit_station_location[::-1]
            _lon_list.append(_from_transit_station_location[1])
            _lat_list.append(_from_transit_station_location[0])
            folium.Circle(location=_from_transit_station_location, tooltip=_dcf_obj.from_transit_station_id, radius=60,
                          color='#0257a0', fill=True,
                          fill_color='#0257a0', fill_opacity=0.1
                          ).add_to(_m)
        else:
            _from_transit_location = None

        _bound = [[min(_lat_list), min(_lon_list)], [max(_lat_list), max(_lon_list)]]
        _m.fit_bounds(_bound)
        if _dcf_obj.commuting_category == 'Only-biking' or _dcf_obj.commuting_category == 'Biking-transit-biking':
            _html_content1 = f"""
                <h3 style="margin: 0; font-size: 16px;"><b>User ID: {_uid}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>User Category: {_dcf_obj.commuting_category}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Flows Number: {_dcf_obj.total_record_num}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Cycling Round Trip Rate: {round(_dcf_obj.cycling_round_trip_rate,2)}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Commuting Distance: {int(_dcf_obj.commuting_distance)} m</b></h3>
            """
            _html_content2 = f"""
                <h3 style="margin: 0; font-size: 16px;"><b>Departure Time from Home: {_dcf_obj.moment_leave_home}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Departure Time from Work: {_dcf_obj.moment_leave_work}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Commuting Time to Work: {int(_dcf_obj.duration_to_work*60)} min</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Commuting Time back Home: {int(_dcf_obj.duration_back_home*60)} min</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Working Hours: {round(_dcf_obj.working_hours, 2)} h</b></h3>
            """
            _html = _html_template.format(_html_content1, _html_content2)
            _m.get_root().html.add_child(folium.Element(_html))
            if _dcf_obj.commuting_category == 'Only-biking':
                folium.PolyLine([_home_location, _work_location], tooltip='Only-biking',
                                color="#ca1d2a", weight=5).add_to(_m)
            else:
                folium.PolyLine([_home_location, _to_transit_location], tooltip='Biking-transit',
                                color="#ca1d2a", weight=5).add_to(_m)
                folium.PolyLine([_from_transit_location, _work_location], tooltip='Transit-biking',
                                color="#ca1d2a", weight=5).add_to(_m)
        elif _dcf_obj.commuting_category == 'Biking-transit':
            folium.PolyLine([_home_location, _to_transit_location], tooltip='Biking-transit',
                            color="#ca1d2a", weight=5).add_to(_m)
            _html_content1 = f"""
                <h3 style="margin: 0; font-size: 16px;"><b>User ID: {_uid}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>User Category: {_dcf_obj.commuting_category}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Flows Number: {_dcf_obj.total_record_num}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Cycling Round Trip Rate: {round(_dcf_obj.cycling_round_trip_rate,2)}</b></h3>
            """
            _html_content2 = f"""
                <h3 style="margin: 0; font-size: 16px;"><b>Departure Time from Home: {_dcf_obj.moment_leave_home}</b></h3>
            """
            _html = _html_template.format(_html_content1, _html_content2)
            _m.get_root().html.add_child(folium.Element(_html))
        elif _dcf_obj.commuting_category == 'Transit-biking':
            folium.PolyLine([_from_transit_location, _work_location], tooltip='Transit-biking',
                            color="#ca1d2a", weight=5).add_to(_m)
            _html_content1 = f"""
                <h3 style="margin: 0; font-size: 16px;"><b>User ID: {_uid}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>User Category: {_dcf_obj.commuting_category}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Flows Number: {_dcf_obj.total_record_num}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Cycling Round Trip Rate: {round(_dcf_obj.cycling_round_trip_rate, 2)}</b></h3>
            """
            _html_content2 = f"""
                <h3 style="margin: 0; font-size: 16px;"><b>Departure Time from Work: {_dcf_obj.moment_leave_work}</b></h3>
                <h3 style="margin: 0; font-size: 16px;"><b>Working Hours: {round(_dcf_obj.working_hours, 2)} h</b></h3>
            """
            _html = _html_template.format(_html_content1, _html_content2)
            _m.get_root().html.add_child(folium.Element(_html))
        else:
            raise TypeError('Commuter category does not exist')

        Fullscreen().add_to(_m)
        return _m
    else:
        raise TypeError('_sfc_obj must be a DailyCommutingFlow class')
