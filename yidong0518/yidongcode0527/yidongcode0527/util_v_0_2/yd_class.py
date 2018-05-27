# 站点类
# 站点id（int，地铁类站点以此为唯一标识），名称（string，驿动类站点以此为唯一标识，由驿动api中站点名称和上下行标识组合而成‘stationName，type’），
# 经纬度（list,[lat,lng],lat/lng-float），该站点经过的线路(list,元素是线路类的id，string)，该站点的临近站（list,元素是站点名称，string）
class Station(object):
    def __init__(self, id, name, location, lines=[], stops={}):
        self.__id = id
        self.__name = name
        self.__location = location
        self.__lines = lines
        self.__stops = stops

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.__name

    def get_location(self):
        return self.__location

    def get_lines(self):
        return self.__lines

    def get_stops(self):
        return self.__stops

    def set_lines(self, lines):
        self.__lines = lines

    def set_stops(self, stops):
        self.__stops = stops

    # In[4]:


# 线路类
# 线路id（string，唯一标识，驿动api中线路名称和上下行标识组合‘routeSeq，type’
# 名称（string）,上下行标识（string）0-去程 1-返程
# 该线路上的站点(dict,key是站点name，value是[在该线路上的经过顺序id,经过该站点的线路集list]）
# 是否为环线
class Line(object):
    def __init__(self, id, name, type, stops={}, isCircle=False, price=[]):
        self.__id = id
        self.__name = name
        self.__type = type
        self.__stops = stops
        self.__isCircle = isCircle
        self.__price = price

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.__name

    def get_stops(self):
        return self.__stops

    def get_type(self):
        return self.__type

    def get_isCircle(self):
        return self.__isCircle

    def get_price(self):
        return self.__price

    def add_stop(self, id, name, transferLine=[]):
        self.__stops[name] = [id, transferLine]

    def search_stop(self, stopname):
        if stopname in self.__stops:
            return self.__stops[stopname]