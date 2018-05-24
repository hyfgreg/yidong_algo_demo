
# coding: utf-8

# In[1]:


import json
import copy
import math
from math import *
import datetime
import operator


# In[2]:


## 自定义类


# In[3]:


# 站点类
#站点id（int，地铁类站点以此为唯一标识），名称（string，驿动类站点以此为唯一标识，由驿动api中站点名称和上下行标识组合而成‘stationName，type’），
#经纬度（list,[lat,lng],lat/lng-float），该站点经过的线路(list,元素是线路类的id，string)，该站点的临近站（list,元素是站点名称，string）
class Station(object):
    def __init__(self,id,name,location,lines=[],stops={}):
        self.__id=id
        self.__name=name
        self.__location=location
        self.__lines=lines
        self.__stops=stops
    
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
    
    def set_lines(self,lines):
        self.__lines=lines
    
    def set_stops(self,stops):
        self.__stops=stops    


# In[4]:


# 线路类
#线路id（string，唯一标识，驿动api中线路名称和上下行标识组合‘routeSeq，type’
#名称（string）,上下行标识（string）0-去程 1-返程 
#该线路上的站点(dict,key是站点name，value是[在该线路上的经过顺序id,经过该站点的线路集list]）
# 是否为环线
class Line(object):
    def __init__(self,id,name,type,stops={},isCircle=False,price=[]):
        self.__id=id
        self.__name=name
        self.__type=type
        self.__stops=stops
        self.__isCircle=isCircle
        self.__price=price
    
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
    
    def add_stop(self,id,name,transferLine=[]):
        self.__stops[name]=[id,transferLine]
        
    def search_stop(self,stopname):
        if stopname in self.__stops:
            return self.__stops[name]


# In[5]:


## 自定义方法，空间判断


# In[6]:


# 获取以中心点为中心，2倍dis（千米）为边长的矩形区域的顶点坐标（用来判断站点是否在中心站的周边范围内）
def get_area(latitude, longitude, dis):
    r = 6371.137
    dlng = 2 * math.asin(math.sin(dis / (2 * r)) / math.cos(latitude ))
    dlng = math.degrees(dlng)
    dlat = dis / r
    dlat = math.degrees(dlat)
    minlat = latitude - dlat
    maxlat = latitude + dlat
    minlng = longitude - dlng
    maxlng = longitude + dlng
    return minlat, maxlat, minlng, maxlng


# In[7]:


# 根据经纬度坐标获取两点间距离(米)
def get_distance(lat1,lng1,lat2,lng2):      
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])  
    dlng = lng2 - lng1   
    dlat = lat2 - lat1   
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2  
    c = 2 * asin(sqrt(a))   
    r = 6371  
    return c * r * 1000 


# In[8]:


## 驿动json数据读取，数据准备


# In[9]:


# 读取线路列表的json文件
input_file=open('routeListSet2018-05-18.json', 'r',encoding='utf-8') 
ldata=json.load(input_file)
# 读取站点列表的json文件
input_file=open('routeStationList2018-05-18.json', 'r',encoding='utf-8') 
sdata=json.load(input_file)
# 读取各站时刻表的json文件
input_file=open('routeStationTime2018-05-18.json', 'r',encoding='utf-8') 
tdata=json.load(input_file)
# 读取排班表的json文件
input_file=open('busSchedule2018-05-18.json', 'r',encoding='utf-8') 
bdata=json.load(input_file)


# In[10]:


# 读取站点列表的json文件
sbw_sdata=[]
input_file=open('stations_bd.json', 'r',encoding='utf-8') 
for line in input_file.readlines():
    sbw_sdata.append(json.loads(line))


# In[11]:


# 获取当前可预订的线路（tline），key是routeSeq，value为线路名称，（saleType==0，其他判断为企业内部班线）
# 线路价格lineprice
tline={}
for i in range(len(ldata)):
    linename=ldata[i]['routeName']
    lineid=str(ldata[i]['routeSeq'])
    linetype=ldata[i]['saleType']
    lineprice=ldata[i]['ticketPrice']
    if linetype==0:
        tline[lineid]=[linename,lineprice]


# In[12]:


# 获取可预订线路上的站点列表（stop），站点列表的名称和站点类中主键一致，由json中站点名称和上下行标识组合而成‘stationName，type’
# 环线为区分起终点，起点名称标记为‘stationName，type（环线起始）’
stop=[]
for key in sdata:
    isCircle=False
    if key in tline:
        for k in sdata[key]:
            if sdata[key][k]==[]:
                continue
            if sdata[key][k][0]['stationName'].strip()==sdata[key][k][-1]['stationName'].strip():
                isCircle=True
            for i in range(len(sdata[key][k])):
                if i==0 and isCircle==True:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])+'（环线起始）'
                else:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])
                stop.append(name)
        isCircle=False
stop=list({}.fromkeys(stop).keys())


# In[13]:


# 为整理DICT YDSTATION/YDLINE 做准备
# stopline字典中各站name为key，value为经过该站点的线路list，此处线路item为‘routeSeq，type’）
stopline={}
for i in stop:
    stopline[i]=[]
for key in sdata:
    isCircle=False
    if key in tline:
        for k in sdata[key]:
            if sdata[key][k]==[]:
                continue
            if sdata[key][k][0]['stationName'].strip()==sdata[key][k][-1]['stationName'].strip():
                isCircle=True
            for i in range(len(sdata[key][k])):
                if i==0 and isCircle==True:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])+'（环线起始）'
                else:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])
                lines=stopline[name]
                lines.append(key+','+k)
                stopline[name]=lines


# In[14]:


#  DICT YDLINE 
# 将获取到的驿动json线路数据整理成线路类的形式，存在key为定义线路id+type的‘routeSeq，type’，value为线路类的字典中
ydline={}
for key in tline:
    isCircle=False
    if key in sdata:
        for k in sdata[key]:
            price=[]
            if sdata[key][k]==[]:
                continue
            if sdata[key][k][0]['stationName'].strip()==sdata[key][k][-1]['stationName'].strip():
                 isCircle=True
            ydlinekey=key+','+k
            stops={}
            for i in range(len(sdata[key][k])):
                if i==0 and isCircle==True:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])+'（环线起始）'
                else:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])
                id=sdata[key][k][i]['flag']
                stops[name]=[id,copy.deepcopy(stopline[name])]
            num_of_stops=len(stops)
            for i in range(num_of_stops):
                price.append([])
                for j in range(num_of_stops):
                    price[i].append([])
                    if i==j:
                        price[i][j]=0
                    else:
                        price[i][j]=tline[key][1]
            # 此处价格矩阵全部为线路价格，不区分站点
            ydline[ydlinekey]=Line(ydlinekey,tline[key][0],k,stops,isCircle,price)
            isCircle=False


# In[15]:


#  DICT YDSTATION
# 将获取到的驿动json站点数据整理成站点类的形式，存在key为定义站点name‘stationName，type’，value为站点类的字典中
ydstation={}
num=1
for key in sdata:
    isCircle=False
    if key in tline:
        for k in sdata[key]:
            if sdata[key][k]==[]:
                continue
            if sdata[key][k][0]['stationName'].strip()==sdata[key][k][-1]['stationName'].strip():
                 isCircle=True
            for i in range(len(sdata[key][k])):
                id=sdata[key][k][i]['id']
                if i==0 and isCircle==True:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])+'（环线起始）'
                else:
                    name=sdata[key][k][i]['stationName'].strip()+','+str(sdata[key][k][i]['type'])
                lat=sdata[key][k][i]['latitude']
                lng=sdata[key][k][i]['longitude']
                if lat<100:
                    location=[lat,lng]
                else:
                    location=[lng,lat]
                sline=copy.deepcopy(stopline[name])
                ydstation[name]=Station(id,name,location,sline)
                num+=1

# 站点半径500米内其他站点定义为周边站点【0】，获取周边站点集合并添加到对应站点类中
nearby_stops={}
for i in stop:
    nearby_stops[i]=[]
    [c_lat,c_lng]=ydstation[i].get_location()
    minlat, maxlat, minlng, maxlng=get_area(c_lat,c_lng,0.5)
    n_stops={}
    for j in stop:
        [t_lat,t_lng]=ydstation[j].get_location()
        if t_lat>minlat and t_lat<maxlat and t_lng>minlng and t_lng< maxlng:
            n_stops[j]=get_distance(c_lat,c_lng,t_lat,t_lng)
    n_stops.pop(i)
    nearby_stops[i]=copy.deepcopy(n_stops)  
for key in ydstation:
    stopsdict={0:copy.deepcopy(nearby_stops[key])}
    ydstation[key].set_stops(stopsdict)


# In[16]:


# DICT SBWSTATION
# 将获取到的地铁json站点数据整理成站点类的形式，存在key为地铁站点id，value为站点类的字典中
sbwstation={}
for i in range(len(sbw_sdata)):
    id=sbw_sdata[i]['id']
    name=sbw_sdata[i]['name']
    lat=float(sbw_sdata[i]['lat_bd'])
    lng=float(sbw_sdata[i]['long_bd'])
    location=[lat,lng]
    sline=list(sbw_sdata[i]['line_id'])
    sbwstation[id]=Station(id,name,location,sline)
    
# yd站点半径500米内地铁站点定义为周边站点【1】，获取周边站点集合并添加到对应站点类中
nearby_sbwstops={}
for key in ydstation:
    nearby_sbwstops[key]=[]
    [c_lat,c_lng]=ydstation[key].get_location()
    minlat, maxlat, minlng, maxlng=get_area(c_lat,c_lng,0.5)
    n_stops={}
    for key2 in sbwstation :
        [t_lat,t_lng]=sbwstation[key2].get_location()
        if t_lat>minlat and t_lat<maxlat and t_lng>minlng and t_lng< maxlng:
            n_stops[key2]=get_distance(c_lat,c_lng,t_lat,t_lng)
    nearby_stops[key]=copy.deepcopy(n_stops)  
for key in ydstation:
    stopdict=ydstation[key].get_stops()
    stopdict[1]=copy.deepcopy(nearby_stops[key])
    ydstation[key].set_stops(stopdict)


# In[17]:


# DICT STATIONTIME
# 将获取到的驿动站点时刻表数据整理成字典 stationTime
# stationTime,key为线路id，value为班次dict（key为班次的routeCode,value为各站[线路顺序index，到站时间]的list列表）
stationTime={}
for key in tdata:
    if key in tline:
        for k in tdata[key]:
            lineid=key+','+k
            code={}
            for c in tdata[key][k]:
                sts={}
                for i in range(len(tdata[key][k][c])):
                    id=tdata[key][k][c][i]['stationFlag']
                    timeStr=tdata[key][k][c][i]['time'].strip().replace('：',':')
                    if timeStr!='':
                        t = datetime.datetime.strptime(timeStr,'%H:%M')
                        sts[id]=t
                code[c]=copy.deepcopy(sts)
            stationTime[lineid]=copy.deepcopy(code)


# In[18]:


# DICT BUSSCHEDULE
# 将获取到的驿动排班数据整理成字典 busSchedule
# stationTime,key为线路id，value 为 dict key为班次id，value 为 车牌号
busSchedule={}
for key in bdata:
    lineid0=str(key)+',0'
    lineid1=str(key)+',1'
    busSchedule[lineid0]={}
    busSchedule[lineid1]={}
    for i in range(len(bdata[key])):
        type=bdata[key][i]['type']
        lineid=str(key)+','+str(type)
        code=bdata[key][i]['routeCodeStr']
        vehicleNo=bdata[key][i]['vehicleNo']
        busSchedule[lineid][code]=vehicleNo


# In[19]:


# method GET_SBWPLAN
# 地铁站 matrix 获取出行方案
#示例：ss_plan=[['step1地铁上车站','step1地铁线路','step1地铁方向','step1地铁下车站'],['step2地铁上车站','step2地铁线路','step2地铁方向','step2地铁下车站']]
def get_sbwplan(sbw_oid,sbw_did):
    ss_plan=[[sbwstation[sbw_oid].get_name(),'step1地铁线路','step1地铁方向','step1地铁下车站'],['step2地铁上车站','step2地铁线路','step2地铁方向',sbwstation[sbw_did].get_name()]]
    # ss_plan 是oid和did两个地铁站间出行时间最短的地铁方案列表，ss_plan是一个step的list
    #每个step包含[上车站点，线路名称，方向（如果matrix里有的话），下车站点]
    duration=90 # 该方案的总时长，单位是 分钟 
    price=5 # 该方案的总价格，单位是 元
    plantype=True # 如果有两站间的方案，plantype为true，没有则false
    return plantype,duration,price,ss_plan


# In[20]:


## 自定义方法，需要用到数据准备中的线路、站点、时刻表的字典
## dict ydline/dict ydstation/dict stationTime/dict sbwstation


# In[21]:


# 获取经过站点集的所有线路的集合
def get_lines_by_stops(stops):
    nlines=[]
    for i in stops:
        lines=ydstation[i].get_lines()
        nlines.extend(lines)
    nlines=list({}.fromkeys(nlines).keys())
    return nlines


# In[22]:


def get_nearby_stops(stops):
    nearby_stops=[]
    for s in stops:
        nearby_stop=copy.deepcopy(ydstation[s].get_stops()[0])
        if nearby_stop != None:
            nearby_stops.extend(list(nearby_stop.keys()))
    return nearby_stops


# In[23]:


# 获取线路集上及周边的所有站点的集合
def get_stops_by_lines(lines):
    nstops=[]
    for line in lines:
        nstops.extend(list(ydline[line].get_stops().keys()))
    nstops=list({}.fromkeys(nstops).keys())
    nearby_stops=get_nearby_stops(nstops)
    nstops.extend(nearby_stops)
    nstops=list({}.fromkeys(nstops).keys())
    return nstops


# In[24]:


# ——根据od站点获取驿动内部出行方案


# In[25]:


# 获取驿动内部规划方案，路径可行，不考虑时间约束
# 输入出发站名称，到达站名称，输出方案（list，换乘会有多个step
#每一个step是两站间的出行方案（出发站，出发线路，上下行，终点站））
# 输出换乘次数，具体方案；没有可行方案反馈-1，和none
def yd_yd_plan(os_name,ds_name,olatlng,dlatlng):
    plans=[]
    o_nstops=get_nearby_stops([os_name])
    o_nstops.append(os_name)
    d_nstops=get_nearby_stops([ds_name])
    d_nstops.append(ds_name)
    plan0,result0=yyplan0(o_nstops,d_nstops,oclatlng=olatlng,dclatlng=dlatlng)
    if plan0==True:
        for p0 in result0:
            plans.append([p0])
        return 0,plans
    else:
        o_nlines=result0[0]
        plan1,result1=yyplan1(o_nstops,o_nlines,d_nstops,olatlng,dlatlng)
        if plan1==True:
            for p1 in result1:
                plans.append(p1)
            return 1,plans
        else:
            d_nlines=result0[1]
            o_nstops1=result1[0]
            o_nlines1=result1[1]
            plan2,result2=yyplan2(o_nstops,o_nstops1,o_nlines1,d_nlines,d_nstops,olatlng,dlatlng) 
            if plan2==True:
                for p2 in result2:
                    plans.append(p2)
                return 2,plans
            else:
                return -1,None
    return -1,None


# In[26]:


# 驿动与驿动直达的算法，输入出发站点集list，到达站点集list
# 如果有方案，输出true及方案
# 如果没有，输出false及一次换乘需要的相关输入参数（可减少重复计算）
def yyplan0(o_nstops,d_nstops,o_nlines=[],d_nlines=[],oclatlng=None,dclatlng=None):
    planline=[]
    plans=[]
    if o_nlines==[]:
        o_nlines=get_lines_by_stops(o_nstops) 
    if d_nlines==[]:
        d_nlines=get_lines_by_stops(d_nstops)
    for i in o_nlines:
        if i in d_nlines:
            planline.append(i)
    if len(planline)>0:
        for i in planline:
            s=ydline[i].get_stops()
            o_ps=[]
            d_ps=[]
            mind=10000
            for j in o_nstops:
                if j in s and j.find('仅下客')==-1:
                    if oclatlng!=None:
                        jlatlng=ydstation[j].get_location()
                        d=get_distance(jlatlng[0],jlatlng[1],oclatlng[0],oclatlng[1])
                        if d<mind:
                            mind=d
                            o_ps=[[j,s[j][0]]]
                        else:
                            continue
                    else:
                        o_ps.append([j,s[j][0]])
            mind=10000
            for k in d_nstops:
                if k in s:
                    if dclatlng!=None:
                        klatlng=ydstation[k].get_location()
                        d=get_distance(klatlng[0],klatlng[1],dclatlng[0],dclatlng[1])
                        if d<mind:
                            mind=d
                            d_ps=[[k,s[k][0]]]
                        else:
                            continue
                    else:
                        d_ps.append([k,s[k][0]])
            for ops in o_ps:
                for dps in d_ps:
                    if ops[1]<dps[1]:
                        if ydline[i].get_isCircle()==True:
                            num=len(s)
                            n=dps[1]-ops[1]
                            if n<=(num-n):
                                pl=[ydline[i].get_name(),ydline[i].get_type(),ydline[i].get_id()]
                                plans.append([ops,pl,dps])
                        else:
                            pl=[ydline[i].get_name(),ydline[i].get_type(),ydline[i].get_id()]
                            plans.append([ops,pl,dps])
        if len(plans)>0:
            return True,plans
        else:
            return False,[o_nlines,d_nlines]
    else:
        return False,[o_nlines,d_nlines]


# In[27]:


# 驿动和驿动一次换乘的算法，输入出发站点集list，经过出发站点集的线路list（即可能的step1的线路），到达站点集list
# 如果有方案，输出true及方案
# 如果没有，输出false及二次换乘需要的相关输入参数（可减少重复计算）
def yyplan1(o_nstops,o_nlines,d_nstops,olatlng,dlatlng):
    plans=[]
    o_nstops1=get_stops_by_lines(o_nlines)
    for i in o_nstops:
        o_nstops1.remove(i)
    plan1_1,result1_1=yyplan0(o_nstops1,d_nstops,dclatlng=dlatlng)
    if plan1_1==True:
        for p1 in result1_1:
            tstop=p1[0][0]
            tstops=get_nearby_stops([tstop])
            tstops.append(tstop)
            dclatlng=ydstation[tstop].get_location()
            plan1_2,result1_2=yyplan0(o_nstops,tstops,oclatlng=olatlng,dclatlng=dclatlng)
            if plan1_2==True:
                for p2 in result1_2:
                    plans.append( [p2,p1])
        if len(plans)>0:
            return True,plans
        else:
            o_nlines1=result1_1[0]
            return False,[o_nstops1,o_nlines1]
    else:
        o_nlines1=result1_1[0]
        return False,[o_nstops1,o_nlines1]


# In[28]:


# 驿动和驿动两次换乘的算法，输入出发站点集list，可能的第一个换乘站点集，可能的step2的线路，到达站点集list
# 如果有方案，输出true及方案
# 如果没有，输出false及None，停止计算
def yyplan2(o_nstops,o_nstops1,o_nlines1,d_nlines,d_nstops,olatlng,dlatlng):
    plans=[]
    d_nstops1=get_stops_by_lines(d_nlines)
    for i in d_nstops:
        d_nstops1.remove(i)
    plan2_1,result2_1=yyplan0(o_nstops1,d_nstops1,o_nlines1)
    if plan2_1==True:
        for p1 in result2_1:
            tstop1=p1[0][0]
            tstops1=get_nearby_stops([tstop1])
            tstops1.append(tstop1)
            dclatlng=ydstation[tstop1].get_location()
            plan2_0,result2_0=yyplan0(o_nstops,tstops1,oclatlng=olatlng,dclatlng=dclatlng)
            tstop2=p1[2][0]
            tstops2=get_nearby_stops([tstop2])
            tstops2.append(tstop2)
            oclatlng=ydstation[tstop2].get_location()
            plan2_2,result2_2=yyplan0(tstops2,d_nstops,oclatlng=oclatlng,dclatlng=dlatlng)
            if plan2_0==True and plan2_2==True:
                for p0 in result2_0:
                    for p2 in result2_2:
                        plan=[]
                        plan.append(p0)
                        plan.append(p1)
                        plan.append(p2)
                        plans.append(plan)
        if len(plans)>0:
            return True,plans
        else:
            return False,None
    else:
        return False,None


# In[29]:


# 对于驿动内部方案，根据时间获取方案的可行班次


# In[30]:


# 获取每一步方案的可行班次，目前设置为出发时间后小于三十分钟以内的等待时间最小的班次
def get_step_routeCode(o_id,lineid,d_id,otime):
    codes=[]
    for code in stationTime[lineid]:
        if (o_id in stationTime[lineid][code]) and (d_id in stationTime[lineid][code]):
            ct=stationTime[lineid][code][o_id]
            td=ct-otime
            waittime=int(td.total_seconds())/60
            if waittime>0 and waittime<15:
                if code in busSchedule[lineid]:
                    dtime=stationTime[lineid][code][d_id]
                    vehicleNo=busSchedule[lineid][code]
                    codes.append([otime.strftime('%H:%M'),waittime,ct.strftime('%H:%M'),dtime.strftime('%H:%M'),vehicleNo,code])
        else:
            continue
    if len(codes)>0:
        codes.sort(key=operator.itemgetter(1))
        return codes[0]
    else:
        return None


# In[31]:


# 获取总方案的可行班次，返回一个列表，没有可行班次的为None
def get_routeCode(otime,plantype,plans):
    codes=[]
    if plantype==0:
        for i in range(len(plans)):
            codes.append([])
            lineid=plans[i][0][1][-1]
            o_id=plans[i][0][0][-1]
            d_id=plans[i][0][2][-1]
            c=get_step_routeCode(o_id,lineid,d_id,otime)
            if c!=None:
                codes[i]=[c]
            else:
                codes[i]=None
    else: 
        for i in range(len(plans)):
            codes.append([])
            ot=otime
            for j in range(len(plans[i])):
                lineid=plans[i][j][1][-1]
                o_id=plans[i][j][0][-1]
                d_id=plans[i][j][2][-1]
                step_code=get_step_routeCode(o_id,lineid,d_id,ot)
                if step_code!=None:
                    transfertime=datetime.timedelta(seconds=300) # 加上换乘步行时间，此处设为5分钟，
                    ot=datetime.datetime.strptime(step_code[-3],'%H:%M')+transfertime
                    codes[i].append(step_code)
                else:
                    codes[i]=None
                    break               
    return codes


# In[32]:


# 对于驿动内部方案，根据班次和方案获取出行时长


# In[33]:


# 获取每一步方案的出行时长
def get_step_duration(o_id,lineid,d_id,code):
    otime=stationTime[lineid][code][o_id]
    dtime=stationTime[lineid][code][d_id]
    duration=dtime-otime
    return duration


# In[34]:


# 获取总方案的出行时长
def get_plan_duration(plantype,plans,codes):
    pds=[]
    if plantype==0:
        for i in range(len(plans)):
            td=get_step_duration(plans[i][0][0][-1],plans[i][0][1][-1],plans[i][0][2][-1],codes[i][0][-1])
            pd=int(td.total_seconds())/60+codes[i][0][1]
            pds.append(pd)
    else: 
        for i in range(len(plans)):
            pd=0
            for j in range(len(plans[i])):
                td=get_step_duration(plans[i][j][0][-1],plans[i][j][1][-1],plans[i][j][2][-1],codes[i][j][-1])
                pd+=int(td.total_seconds())/60+codes[i][j][1]
            pd+=plantype*5 # 中间换乘步行时间，此处设为5分钟，
            pds.append(pd)
    return pds


# In[35]:


# 获取方案的价格
def get_plan_price(membertype,ydplan):
    if membertype==0:
        discount=1
    elif membertype==1:
        discount=0.3
    elif membertype==2:
        discount=0.2
    price=0
    pricelist=[]
    for step in ydplan:
        o_id=step[0][-1]-1
        d_id=step[2][-1]-1
        lineid=step[1][-1]
        stepprice=discount*ydline[lineid].get_price()[o_id][d_id]/100 #元
        pricelist.append(stepprice)
        price+=stepprice
    price=round(price,2)
    return price,pricelist


# In[36]:


# 对路径上可行的驿动内部方案，根据出行时间和班次，输出时间约束下可行的驿动内部的行程
def out_put_yd_trip(otime,plantype,plans,o_wt=0,d_wt=0,membertype=0):
    o_walktime=datetime.timedelta(seconds=o_wt*60)# 获取从起点到出发站点的步行时间，timedelta类型，此处大小与上一致（单位秒）
    otime1=otime+o_walktime # 根据出发时刻和步行的timedelta，获取到达出发站点的时刻
    ps=[]
    cs=[]
    codes=get_routeCode(otime1,plantype,plans)
    for i in range(len(codes)):
        if codes[i]!=None:
            ps.append(plans[i])
            cs.append(codes[i])
    if len(ps)>0:
        pc=[]
        pds=get_plan_duration(plantype,ps,cs)
        for i in range(len(ps)):
            pc.append([])
            t_price,pricelist=get_plan_price(membertype,ps[i])
            pc[i].append(ps[i])
            pc[i].append(cs[i])
            pc[i].append(pricelist)
            pds[i]+=d_wt+o_wt
            pc[i].insert(0,int(pds[i]))
            td_duration=pds[i]*60
            dtime=otime+datetime.timedelta(seconds=td_duration)
            o_time=otime.strftime('%H:%M')
            d_time=dtime.strftime('%H:%M')
            pc[i].insert(1,o_time)
            pc[i].insert(2,d_time)
            pc[i].insert(3,t_price)
            pc[i]
        pc.sort(key=operator.itemgetter(0))
        return pc
    else:
        return None


# In[37]:


# ——根据od站点获取驿动与地铁的换乘方案（驿动-地铁，地铁-驿动）


# In[38]:


# 查找驿动直达及一次换乘内站点周边的地铁站，获取与已知地铁站间的出行方案
def yd_sbw_plan(os_name,o_type,ds_name,d_type,olatlng,dlatlng):
    if o_type==0 and d_type==1:
        o_nstops=get_nearby_stops([os_name])
        o_nstops.append(os_name)
        yline0=get_lines_by_stops(o_nstops)
        sbw_s=ds_name
    elif o_type==1 and d_type==0:
        d_nstops=get_nearby_stops([ds_name])
        d_nstops.append(ds_name)
        yline0=get_lines_by_stops(d_nstops)
        sbw_s=os_name
    # 获取给定驿动站点的直达站点集
    ystation0=get_stops_by_lines(yline0)
    nearby_stops=get_nearby_stops(ystation0)
    ystation0.extend(nearby_stops)
    ystation0=list({}.fromkeys(ystation0).keys())
    # 获取给定驿动站点的直达和一次换乘站点集
    yline1=get_lines_by_stops(ystation0)
    ystation1=get_stops_by_lines(yline1)
    nearby_stops=get_nearby_stops(ystation1)
    ystation1.extend(nearby_stops)
    ystation1=list({}.fromkeys(ystation1).keys())
    # 获取上述站点周边地铁站
    nearby_sbws={}
    for ys in ystation1:
        for sbws in ydstation[ys].get_stops()[1]:
            nearby_sbws[sbws]=[]
    for ys in ystation1:
        for sbws in ydstation[ys].get_stops()[1]:
            d=ydstation[ys].get_stops()[1][sbws]
            nearby_sbws[sbws].append([ys,d])
    # 获取周边地铁站与给定地铁站间的出行方案ss_plan
    tsf_plans=[]
    nearbysbw=list(nearby_sbws.keys())
    if sbw_s in nearbysbw:
        nearbysbw.remove(sbw_s)
    for sbws in nearbysbw:
        nearby_ys=[nearby_sbws[sbws][0],nearby_sbws[sbws][1]]
        nearby_ys.sort(key=operator.itemgetter(1))
        ys=nearby_ys[0][0]
        slatlng=ydstation[ys].get_location()
        if o_type==0 and d_type==1:
            plantype,duration,price,ss_plan=get_sbwplan(sbws,sbw_s)
            if plantype==False:
                continue
            if os_name==ys:
                continue
            ypt,ydplans=yd_yd_plan(os_name,ys,olatlng,slatlng)
        elif o_type==1 and d_type==0:
            plantype,duration,price,ss_plan=get_sbwplan(sbw_s,sbws)
            if plantype==False:
                continue
            if ds_name==ys:
                continue
            ypt,ydplans=yd_yd_plan(ys,ds_name,slatlng,dlatlng)
        if ypt!=-1:
            for p in ydplans:
                plan=[]
                plan.append([ypt,[p]])
                plan.append([duration,price,ss_plan])
                tsf_plans.append(plan)
        else:
            continue
    # 输出驿动站点与给定地铁站间的出行方案tsf_plan
    if len(tsf_plans)==0:
        return -2,None
    else:
        return 3,tsf_plans


# In[39]:


# 对路径上可行的地铁方案，根据出行时间，输出包含时刻信息的地铁方案
def out_put_sbw_trip(otime,duration,price,sbwplans,o_wt=0,d_wt=0):
    o_walktime=datetime.timedelta(seconds=o_wt*60)# 获取从起点到出发站点的步行时间，timedelta类型，此处大小与上一致（单位秒）
    otime1=otime+o_walktime # 根据出发时刻和步行的timedelta，获取到达出发站点的时刻
    pc=[]
    total_d=int(duration)+d_wt+o_wt
    pc.append(total_d)
    pc.append(sbwplans)
    td_duration=total_d*60
    o_time=otime.strftime('%H:%M')
    dtime=otime+datetime.timedelta(seconds=td_duration)
    d_time=dtime.strftime('%H:%M')
    pc.insert(1,o_time)
    pc.insert(2,d_time)
    pc.insert(3,price)
    return pc


# In[40]:


# ——根据od经纬度和时间计算出行方案


# In[41]:


# 找出od最近的驿动站点（后面的计算中会包含该站点周边站，故此处只考虑距离最近的即可）
def get_odstops(o_lat,o_lng,d_lat,d_lng):
    #设置驿动最远阈值1000米范围内
    o_dmin=[500,None]
    d_dmin=[500,None]
    for key in ydstation:
        o_d=get_distance(o_lat,o_lng,ydstation[key].get_location()[0],ydstation[key].get_location()[1])
        d_d=get_distance(d_lat,d_lng,ydstation[key].get_location()[0],ydstation[key].get_location()[1])
        o_dmin=([o_d,key] if o_d<o_dmin[0] else o_dmin )
        d_dmin=([d_d,key] if d_d<d_dmin[0] else d_dmin )
    return o_dmin,d_dmin

# 寻找公交站点可用百度地图周边poi接口


# In[42]:


# 找出最近的地铁站点（后面的计算中会包含该站点周边站，故此处只考虑距离最近的即可）
def get_sbwstops(lat,lng):
    #设置最远阈值1000米范围内
    dmin=[500,None]
    for key in sbwstation:
        d=get_distance(lat,lng,sbwstation[key].get_location()[0],sbwstation[key].get_location()[1])
        dmin=([d,key] if d<dmin[0] else dmin )
    return dmin


# In[43]:


# 规划驿动内部的行程
def plan_yd_yd_trip(os,ds,otime,olatlng,dlatlng,membertype=0):
    o_wt=int(os[0]/60)# 获取从起点到出发站点的步行时长，可以调百度api，此处速度1m/s
    d_wt=int(ds[0]/60)# 获取从到达站点到目的地的步行时间，可以调百度api，此处速度1m/s
    plantype,plans=yd_yd_plan(os[1],ds[1],olatlng,dlatlng)
    if plantype!=-1:
        plans=out_put_yd_trip(otime,plantype,plans,o_wt,d_wt,membertype)
        if plans!=None:
            return yd_json_out_put(plans)
        else:
            return None
    else:
        return None


# In[44]:


def yd_json_out_put(plans):
    joutput={}
    n=0
    for plan in plans:
        n+=1
        i='ydPlan'+str(n)
        joutput[i]={}
        joutput[i]['totalDuration']=plan[0]
        joutput[i]['departTime']=plan[1]
        joutput[i]['arriveTime']=plan[2]
        joutput[i]['totalPrice']=plan[3]
        joutput[i]['planStep']={}
        for j in range(len(plan[4])):
            stepnum=str(j+1)
            stepcode=plan[5][j]
            otime=datetime.datetime.strptime(stepcode[0],'%H:%M')
            dtime=datetime.datetime.strptime(stepcode[3],'%H:%M')
            duration=dtime-otime
            joutput[i]['planStep'][stepnum]={}
            joutput[i]['planStep'][stepnum]['duration']=int(duration.total_seconds())/60
            joutput[i]['planStep'][stepnum]['departTime']=stepcode[0]
            joutput[i]['planStep'][stepnum]['arriveTime']=stepcode[3]
            joutput[i]['planStep'][stepnum]['price']=plan[6][j]
            step=plan[4][j]
            stepo=step[0]
            stepo_name,stepo_type=stepo[0].split(',',1)
            stepo_id=ydstation[stepo[0]].get_id()
            joutput[i]['planStep'][stepnum]['o_station']={}
            joutput[i]['planStep'][stepnum]['o_station']['id']=stepo_id
            joutput[i]['planStep'][stepnum]['o_station']['name']=stepo_name
            joutput[i]['planStep'][stepnum]['o_station']['type']=stepo_type
            joutput[i]['planStep'][stepnum]['o_station']['flag']=stepo[1]
            stepd=step[2]
            stepd_name,stepd_type=stepd[0].split(',',1)
            stepd_id=ydstation[stepd[0]].get_id()
            joutput[i]['planStep'][stepnum]['d_station']={}
            joutput[i]['planStep'][stepnum]['d_station']['id']=stepd_id
            joutput[i]['planStep'][stepnum]['d_station']['name']=stepd_name
            joutput[i]['planStep'][stepnum]['d_station']['type']=stepd_type
            joutput[i]['planStep'][stepnum]['d_station']['flag']=stepd[1]
            stepline=step[1]
            stepline_id,stepline_type=stepline[-1].split(',',1)
            joutput[i]['planStep'][stepnum]['route']={}
            joutput[i]['planStep'][stepnum]['route']['id']= stepline_id
            joutput[i]['planStep'][stepnum]['route']['name']=stepline[0]
            joutput[i]['planStep'][stepnum]['route']['type']=stepline_type
            joutput[i]['planStep'][stepnum]['route']['code']=stepcode[-1]
            joutput[i]['planStep'][stepnum]['route']['vehicleNo']=stepcode[-2]
            joutput[i]['planStep'][stepnum]['route']['waitTime']=stepcode[1]
            joutput[i]['planStep'][stepnum]['route']['busArriveOStationTime']=stepcode[2]
    return joutput


# In[45]:


def sbw_json_out_put(plan):
    joutput={}
    joutput['totalDuration']=plan[0]
    joutput['departTime']=plan[1]
    joutput['arriveTime']=plan[2]
    joutput['totalPrice']=plan[3]
    joutput['planStep']={}
    for j in range(len(plan[4])):
        stepnum=str(j+1)
        step=plan[4][j]
        joutput['planStep'][stepnum]={}
        joutput['planStep'][stepnum]['o_station']=step[0]
        joutput['planStep'][stepnum]['d_station']=step[-1]
        joutput['planStep'][stepnum]['route']={}
        joutput['planStep'][stepnum]['route']['name']= step[1]
        joutput['planStep'][stepnum]['route']['direction']=step[2]
    return joutput


# In[46]:


def yd_sbw_json_out_put(plans,type):
    joutput={}
    n=0
    for plan in plans:
        n+=1
        i='yd-subwayPlan'+str(n)
        joutput[i]={}
        joutput[i]['totalDuration']=plan[0]
        joutput[i]['departTime']=plan[1]
        joutput[i]['arriveTime']=plan[2]
        joutput[i]['totalPrice']=plan[3]
        joutput[i]['part']={}
        joutput[i]['part'][type+1]={'ydplan':yd_json_out_put([plan[type+4]])['ydPlan1']}
        joutput[i]['part'][1-type+1]={'subwayplan':sbw_json_out_put(plan[5-type])}
    return joutput


# In[47]:


# 规划驿动-地铁的行程
def plan_yd_sbw_trip(os,sbw_ds,otime,olatlng,dlatlng,membertype=0):
    o_wt=int(os[0]/60)# 获取从起点到出发站点的步行时长，可以调百度api，此处速度1m/s
    d_wt=int(sbw_ds[0]/60)# 获取从到达站点到目的地的步行时间，可以调百度api，此处速度1m/s
    plantype,plans=yd_sbw_plan(os[1],0,sbw_ds[1],1,olatlng,dlatlng)
    outputs=[]
    tsf_wt=5 # 换乘时间
    if plantype!=-2:
        for plan in plans:
            [ydplantype,ydplans]=plan[0]
            [sbw_duration,sbw_price,sbwplans]=plan[1]
            ydstep=out_put_yd_trip(otime,ydplantype,ydplans,o_wt,tsf_wt,membertype)
            if ydstep==None:
                continue
            for yds in ydstep:
                yd_dtime=datetime.datetime.strptime(yds[2],'%H:%M')
                sbwstep=out_put_sbw_trip(yd_dtime,sbw_duration,sbw_price,sbwplans,tsf_wt,d_wt)
                output=[]
                total_d=yds[0]+sbwstep[0]
                t_duration=total_d*60
                total_p=sbw_price+yds[3]
                output.append(total_d)
                output.append(total_p)
                output.append(yds)
                output.append(sbwstep)
                o_time=otime.strftime('%H:%M')
                dtime=otime+datetime.timedelta(seconds=t_duration)
                d_time=dtime.strftime('%H:%M')
                output.insert(1,o_time)
                output.insert(2,d_time)
                outputs.append(output)
        outputs.sort(key=operator.itemgetter(0))
        if len(outputs)>0:
            if len(outputs)<4:
                plans=outputs
            else:
                plans=outputs[0:3]
            return yd_sbw_json_out_put(plans,0)
        else:
            return None
    else:
        return None


# In[48]:


# 规划地铁-驿动的行程
def plan_sbw_yd_trip(sbw_os,ds,otime,olatlng,dlatlng,membertype):
    o_wt=int(sbw_os[0]/60)# 获取从起点到出发站点的步行时长，可以调百度api，此处设为5分钟
    d_wt=int(ds[0]/60)# 获取从到达站点到目的地的步行时间，可以调百度api，此处设为5分钟
    plantype,plans=yd_sbw_plan(sbw_os[1],1,ds[1],0,olatlng,dlatlng)
    outputs=[]
    tsf_wt=5
    if plantype!=-2:
        for plan in plans:
            [ydplantype,ydplans]=plan[0]
            [sbw_duration,sbw_price,sbwplans]=plan[1]
            sbwstep=out_put_sbw_trip(otime,sbw_duration,sbw_price,sbwplans,o_wt,tsf_wt)
            sbw_dtime=datetime.datetime.strptime(sbwstep[2],'%H:%M')
            ydstep=out_put_yd_trip(sbw_dtime,ydplantype,ydplans,o_wt,tsf_wt,membertype)
            if ydstep==None:
                continue
            for yds in ydstep:
                output=[]
                total_d=yds[0]+sbwstep[0]
                t_duration=total_d*60
                total_p=sbw_price+yds[3]
                output.append(total_d)
                output.append(total_p)
                output.append(sbwstep)
                output.append(yds)
                o_time=otime.strftime('%H:%M')
                dtime=otime+datetime.timedelta(seconds=t_duration)
                d_time=dtime.strftime('%H:%M')
                output.insert(1,o_time)
                output.insert(2,d_time)
                outputs.append(output)
        outputs.sort(key=operator.itemgetter(0))
        if len(outputs)>0:
            if len(outputs)<4:
                plans=outputs
            else:
                plans= outputs[0:3]
            return yd_sbw_json_out_put(plans,1)
        else:
            return None
    else:
        return None


# In[49]:


# 利用上述method，输入出发地目的地的经纬度，和出发时刻，获取出行方案
# 输出优先级：驿动内部，驿动-地铁，地铁-驿动
def plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype=0):
    otime= datetime.datetime.strptime(o_time,'%H:%M')
    os,ds=get_odstops(o_lat,o_lng,d_lat,d_lng)
    olatlng=[o_lat,o_lng]
    dlatlng=[d_lat,d_lng]
    if os[1]!=None and ds[1]!=None and os[1]!=ds[1]:
        trip=plan_yd_yd_trip(os,ds,otime,olatlng,dlatlng,membertype)
        if trip!=None:
            return trip
    if (os[1]!=None or ds[1]!=None) and os[1]!=ds[1]:
        sbw_ds=get_sbwstops(d_lat,d_lng)
        if os[1]!=None and sbw_ds[1]!=None:
            trip=plan_yd_sbw_trip(os,sbw_ds,otime,olatlng,dlatlng,membertype)
            if trip!=None:
                return trip 
        sbw_os=get_sbwstops(o_lat,o_lng)
        if ds[1]!=None and sbw_os[1]!=None:
            trip=plan_sbw_yd_trip(sbw_os,ds,otime,olatlng,dlatlng,membertype)
            if trip!=None:
                return trip 
    return None


# In[50]:


## 测试用例 


# In[51]:


# o-柏林映象周边，d-安亭新镇周边
# 驿动内直达换乘
o_lat=31.2712
o_lng=121.178615
d_lat=31.277159
d_lng=121.175772
o_time='07:10'
membertype=0
plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype)


# In[52]:


# o-安亭新镇周边，d-中山公园周边
# 驿动内直达
o_lat=31.277159
o_lng=121.175772
d_lat=31.22415
d_lng=121.424639
o_time='07:30'
membertype=1
plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype)


# In[53]:


# o-柏林映象周边，d-中山公园周边
# 驿动内一次换乘
o_lat=31.2712
o_lng=121.178615
d_lat=31.22415
d_lng=121.424639
o_time='07:10'
membertype=2
plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype)


# In[54]:


# o-同济大学周边，d-中山公园周边
# 驿动换乘地铁
o_lat=31.29188
o_lng=121.22063
d_lat=31.22415
d_lng=121.424639
o_time='07:20'
membertype=2
plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype)


# In[55]:


# o-中山公园周边，d-安亭新镇周边
# 地铁换乘驿动，该类方案的总时长合理性需要利用 百度api 获取到公交出行的时间进行判断，如果长于两地直接公交，那么方案需剔除
o_lat=31.22415
o_lng=121.424639
d_lat=31.277159
d_lng=121.175772
o_time='16:50'
plan_trip(o_lat,o_lng,d_lat,d_lng,o_time)

