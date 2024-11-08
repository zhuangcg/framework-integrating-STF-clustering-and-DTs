# encoding: utf-8
import math

def get_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def wgs84_to_webmercator(lng, lat):
    '''
    实现WGS84向web墨卡托的转换
    :param lng: WGS84经度
    :param lat: WGS84纬度
    :return: 转换后的web墨卡托坐标
    '''
    x = lng * 20037508.342789 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34789 / 180
    return x, y


def webmercator_to_wgs84(x, y):
    '''
    实现web墨卡托向WGS84的转换
    :param x: web墨卡托x坐标
    :param y: web墨卡托y坐标
    :return: 转换后的WGS84经纬度
    '''
    lng = x / 20037508.34 * 180
    lat = y / 20037508.34 * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lng, lat

def time_to_hour(_time_str:str):
    time_list = _time_str.split(':')
    return int(time_list[0]) + int(time_list[1]) / 60 + int(time_list[2]) / 3600

def hour_to_time(_hour:float):
    if _hour < 0:
        _hour += 24
    _hh = int(_hour)
    _mm = int((_hour - _hh) * 3600 / 60)
    _ss = int((_hour - _hh) * 3600 - (60 * _mm))
    return f'{str(_hh).zfill(2)}:{str(_mm).zfill(2)}:{str(_ss).zfill(2)}'

