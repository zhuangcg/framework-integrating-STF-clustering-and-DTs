# encoding: utf-8
import math

def get_distance(p1, p2):
    """
    Calculate the Euclidean distance between two points in a 2D plane.
    Parameters:
        p1: A list or tuple containing two elements representing the x and y coordinates of the first point.
        p2: A list or tuple containing two elements representing the x and y coordinates of the second point.
    Returns:
        The straight-line distance between the two points.
    """
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def are_endpoints_far_apart(line1, line2, threshold):
    """
    Determine if the endpoints of two lines are farther apart than a specified threshold.
    Parameters:
        line1: List of endpoint coordinates for the first line.
        line2: List of endpoint coordinates for the second line.
        threshold: The distance threshold used to determine if endpoints are far apart.
    Returns:
        True if any pair of endpoints is farther apart than the threshold, otherwise False.
    """
    distances = []
    for point1 in line1:
        for point2 in line2:
            distance = get_distance(point1, point2)
            distances.append(distance)

    for distance in distances:
        if distance < threshold:
            return False
    return True

def wgs84_to_webmercator(lng, lat):
    """
    Convert coordinates from the WGS84 coordinate system to the Web Mercator coordinate system.
    Parameters:
        lng (float): Longitude in the WGS84 coordinate system.
        lat (float): Latitude in the WGS84 coordinate system.
    Returns:
        tuple: x and y coordinates in the Web Mercator coordinate system.
    """
    x = lng * 20037508.342789 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34789 / 180
    return x, y


def webmercator_to_wgs84(x, y):
    """
    Convert coordinates from the Web Mercator coordinate system to WGS84 coordinate system.
    Parameters:
        x (float): The X coordinate in the Web Mercator coordinate system.
        y (float): The Y coordinate in the Web Mercator coordinate system.
    Returns:
        tuple: A tuple containing two floats, representing the longitude (lng) and latitude (lat).
    """
    lng = x / 20037508.34 * 180
    lat = y / 20037508.34 * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lng, lat

def time_to_hour(_time_str:str):
    """
    Convert time string in the format HH:MM:SS and converts it to the total number of hours.
    Parameters:
        _time_str: str - Time string in the format HH:MM:SS.
    Returns:
        float - Total hours.
    """
    time_list = _time_str.split(':')
    return int(time_list[0]) + int(time_list[1]) / 60 + int(time_list[2]) / 3600

def hour_to_time(_hour:float):
    """
    Converts a floating-point number representing hours into a time string in HH:MM:SS format.
    Parameters:
        _hour: A floating-point number representing hours
    Returns:
         A string representing the time in HH:MM:SS format
    """
    if _hour < 0:
        _hour += 24
    _hh = int(_hour)
    _mm = int((_hour - _hh) * 3600 / 60)
    _ss = int((_hour - _hh) * 3600 - (60 * _mm))
    return f'{str(_hh).zfill(2)}:{str(_mm).zfill(2)}:{str(_ss).zfill(2)}'
