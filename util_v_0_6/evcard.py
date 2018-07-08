# -*- coding: utf-8 -*-

import math

from config import Config_dev


class Evcard(object):
    def __init__(self, distance=Config_dev.evcard_distance, db=Config_dev.db_evcard):
        self.distance_th = distance  # 查找evcard的距离
        self.db = db
        self.shanghai_all = None
        if self.shanghai_all is None:
            self.shanghai_all = self.read_data_from_mongo()

    def read_data_from_mongo(self):
        try:
            data = self.db.shanghai.find()
            return [i for i in data]
        except Exception:
            return None

    @classmethod
    def init(cls, app):
        app.evcard_algo = cls()

    def plan_trip(self, o_lat, o_lng):
        dis,key =  self.find_nearest_evcard_station(o_lat, o_lng, self.distance_th)
        return self.evcard_out_put(dis,key)

    def find_nearest_evcard_station(self, o_lat, o_lng, dis):
        o_dmin = [dis, None]
        ominlat, omaxlat, ominlng, omaxlng = self.get_area(o_lat, o_lng, dis / 1000)  # 只需要起点的
        # dminlat, dmaxlat, dminlng, dmaxlng = self.get_area(d_lat, d_lng, dis / 1000)
        if self.shanghai_all is None:
            self.shanghai_all = self.read_data_from_mongo()
        if self.shanghai_all is None:
            return o_dmin
        for key in self.shanghai_all:
            t_lat, t_lng = key['lat_bd'], key['long_bd']
            if t_lat > ominlat and t_lat < omaxlat and t_lng > ominlng and t_lng < omaxlng:
                o_d = self.get_distance(o_lat, o_lng, t_lat, t_lng)
                o_dmin = ([o_d, key] if o_d < o_dmin[0] else o_dmin)

        return o_dmin

    def evcard_out_put(self, dis, key):
        """
        :param dis: 距离
        :param key: 站点信息
        :return:
        """
        ret = {}
        ret['dis'] = dis
        if key is None:
            ret['shop'] = {}
            return ret
        ret['shop'] = {}
        for k in Config_dev.evcard_filds:
            try:
                ret['shop'][k] = key[k]
            except KeyError:
                ret['shop'][k] = None
        return ret

    def get_area(self, latitude, longitude, dis):
        r = 6371.137
        dlng = 2 * math.asin(math.sin(dis / (2 * r)) / math.cos(latitude))
        dlng = math.degrees(dlng)
        dlat = dis / r
        dlat = math.degrees(dlat)
        minlat = latitude - dlat
        maxlat = latitude + dlat
        minlng = longitude - dlng
        maxlng = longitude + dlng
        return minlat, maxlat, minlng, maxlng

    # 根据经纬度坐标获取两点间距离(米)
    def get_distance(self, lat1, lng1, lat2, lng2):
        lng1, lat1, lng2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])
        dlng = lng2 - lng1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371
        return c * r * 1000

if __name__ == '__main__':
    lat,long = 31.2851314007,121.1705021627
    ev = Evcard()
    print(ev.plan_trip(lat,long))
    # dis,key = ev.plan_trip(lat,long)
    # print(int(dis),key)