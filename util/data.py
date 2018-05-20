import datetime
import json
import os
import copy
from util.yd_class import Station,Line
from util.common_func import get_area,get_distance

base_folder = '/home/hyfgreg/PycharmProjects/yidong_algo'

# 读取线路列表的json文件
# input_file=open('routeListSet2018-04-23.json', 'r',encoding='utf-8')
# ldata=json.load(input_file)
with open(base_folder+'/data/routeListSet2018-04-23.json','r',encoding='utf-8') as f:
    ldata = json.loads(f.read())

# 读取站点列表的json文件
# input_file=open('routeStationList.json', 'r',encoding='utf-8')
# sdata=json.load(input_file)
with open(base_folder+'/data/routeStationList2018-04-23.json', 'r',encoding='utf-8') as f:
    sdata = json.loads(f.read())

# 读取各站时刻表的json文件
# input_file=open('routeStationTime2018-04-23.json', 'r',encoding='utf-8')
# tdata=json.load(input_file)

with open(base_folder+'/data/routeStationTime2018-04-23.json', 'r',encoding='utf-8') as f:
    tdata = json.loads(f.read())
# In[609]:


# 读取地铁站点列表的json文件
sbw_sdata=[]
# input_file=open('stations_bd.json', 'r',encoding='utf-8')
# for line in input_file.readlines():
#     sbw_sdata.append(json.loads(line))
with open(base_folder+'/data/stations_bd.dat', 'r',encoding='utf-8') as f:
    for line in f.readlines():
        sbw_sdata.append(json.loads(line))

# 获取当前可预订的线路（tline），key是routeSeq，value为线路名称，（saleType==0，其他判断为企业内部班线）
tline = {}
for i in range(len(ldata)):
    linename = ldata[i]['routeName']
    lineid = str(ldata[i]['routeSeq'])
    linetype = ldata[i]['saleType']
    if linetype == 0:
        tline[lineid] = linename

# In[611]:


# 获取可预订线路上的站点列表（stop），站点列表的名称和站点类中主键一致，由json中站点名称和上下行标识组合而成‘stationName，type’
# 环线为区分起终点，起点名称标记为‘stationName，type（环线起始）’
stop = []
for key in sdata:
    isCircle = False
    if key in tline:
        for k in sdata[key]:
            if sdata[key][k] == []:
                continue
            if sdata[key][k][0]['stationName'].strip() == sdata[key][k][-1]['stationName'].strip():
                isCircle = True
            for i in range(len(sdata[key][k])):
                if i == 0 and isCircle == True:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type']) + '（环线起始）'
                else:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type'])
                stop.append(name)
        isCircle = False
stop = list({}.fromkeys(stop).keys())

# In[612]:


# 为整理DICT YDSTATION/YDLINE 做准备
# stopline字典中各站name为key，value为经过该站点的线路list，此处线路item为‘routeSeq，type’）
stopline = {}
for i in stop:
    stopline[i] = []
for key in sdata:
    isCircle = False
    if key in tline:
        for k in sdata[key]:
            if sdata[key][k] == []:
                continue
            if sdata[key][k][0]['stationName'].strip() == sdata[key][k][-1]['stationName'].strip():
                isCircle = True
            for i in range(len(sdata[key][k])):
                if i == 0 and isCircle == True:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type']) + '（环线起始）'
                else:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type'])
                lines = stopline[name]
                lines.append(key + ',' + k)
                stopline[name] = lines

# In[613]:


#  DICT YDLINE
# 将获取到的驿动json线路数据整理成线路类的形式，存在key为定义线路id+type的‘routeSeq，type’，value为线路类的字典中
ydline = {}
for key in tline:
    isCircle = False
    if key in sdata:
        for k in sdata[key]:
            if sdata[key][k] == []:
                continue
            if sdata[key][k][0]['stationName'].strip() == sdata[key][k][-1]['stationName'].strip():
                isCircle = True
            ydlinekey = key + ',' + k
            stops = {}
            for i in range(len(sdata[key][k])):
                if i == 0 and isCircle == True:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type']) + '（环线起始）'
                else:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type'])
                id = sdata[key][k][i]['flag']
                stops[name] = [id, copy.deepcopy(stopline[name])]
            ydline[ydlinekey] = Line(ydlinekey, tline[key], k, stops, isCircle)
            isCircle = False

# In[614]:


#  DICT YDSTATION
# 将获取到的驿动json站点数据整理成站点类的形式，存在key为定义站点name‘stationName，type’，value为站点类的字典中
ydstation = {}
num = 1
for key in sdata:
    isCircle = False
    if key in tline:
        for k in sdata[key]:
            if sdata[key][k] == []:
                continue
            if sdata[key][k][0]['stationName'].strip() == sdata[key][k][-1]['stationName'].strip():
                isCircle = True
            for i in range(len(sdata[key][k])):
                id = num
                if i == 0 and isCircle == True:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type']) + '（环线起始）'
                else:
                    name = sdata[key][k][i]['stationName'].strip() + ',' + str(sdata[key][k][i]['type'])
                lat = sdata[key][k][i]['latitude']
                lng = sdata[key][k][i]['longitude']
                if lat < 100:
                    location = [lat, lng]
                else:
                    location = [lng, lat]
                sline = copy.deepcopy(stopline[name])
                ydstation[name] = Station(id, name, location, sline)
                num += 1

# 站点半径500米内其他站点定义为周边站点【0】，获取周边站点集合并添加到对应站点类中
nearby_stops = {}
for i in stop:
    nearby_stops[i] = []
    [c_lat, c_lng] = ydstation[i].get_location()
    minlat, maxlat, minlng, maxlng = get_area(c_lat, c_lng, 0.5)
    n_stops = []
    for j in stop:
        [t_lat, t_lng] = ydstation[j].get_location()
        if t_lat > minlat and t_lat < maxlat and t_lng > minlng and t_lng < maxlng:
            n_stops.append(j)
    n_stops.remove(i)
    nearby_stops[i] = copy.deepcopy(n_stops)
for key in ydstation:
    stopsdict = {0: copy.deepcopy(nearby_stops[key])}
    ydstation[key].set_stops(stopsdict)

# In[615]:


# DICT SBWSTATION
# 将获取到的地铁json站点数据整理成站点类的形式，存在key为地铁站点id，value为站点类的字典中
sbwstation = {}
for i in range(len(sbw_sdata)):
    id = sbw_sdata[i]['id']
    name = sbw_sdata[i]['name']
    lat = float(sbw_sdata[i]['lat_bd'])
    lng = float(sbw_sdata[i]['long_bd'])
    location = [lat, lng]
    sline = list(sbw_sdata[i]['line_id'])
    sbwstation[id] = Station(id, name, location, sline)

# yd站点半径500米内地铁站点定义为周边站点【1】，获取周边站点集合并添加到对应站点类中
nearby_sbwstops = {}
for key in ydstation:
    nearby_sbwstops[key] = []
    [c_lat, c_lng] = ydstation[key].get_location()
    minlat, maxlat, minlng, maxlng = get_area(c_lat, c_lng, 0.5)
    n_stops = []
    for key2 in sbwstation:
        [t_lat, t_lng] = sbwstation[key2].get_location()
        if t_lat > minlat and t_lat < maxlat and t_lng > minlng and t_lng < maxlng:
            n_stops.append(key2)
    nearby_stops[key] = copy.deepcopy(n_stops)
for key in ydstation:
    stopdict = ydstation[key].get_stops()
    stopdict[1] = copy.deepcopy(nearby_stops[key])
    ydstation[key].set_stops(stopdict)

# In[616]:


# DICT STATIONTIME
# 将获取到的驿动站点时刻表数据整理成字典 stationTime
# stationTime,key为线路id，value为班次dict（key为班次的routeCode,value为各站[线路顺序index，到站时间]的list列表）
stationTime = {}
for key in tdata:
    if key in tline:
        for k in tdata[key]:
            lineid = key + ',' + k
            code = {}
            for c in tdata[key][k]:
                sts = {}
                for i in range(len(tdata[key][k][c])):
                    id = tdata[key][k][c][i]['stationFlag']
                    timeStr = tdata[key][k][c][i]['time'].strip().replace('：', ':')
                    if timeStr != '':
                        t = datetime.datetime.strptime(timeStr, '%H:%M')
                        sts[id] = t
                code[c] = copy.deepcopy(sts)
            stationTime[lineid] = copy.deepcopy(code)