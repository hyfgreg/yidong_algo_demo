import math

def get_area(latitude, longitude, dis):
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


# In[606]:


# 根据经纬度坐标获取两点间距离(米)
def get_distance(lat1, lng1, lat2, lng2):
    lng1, lat1, lng2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r * 1000