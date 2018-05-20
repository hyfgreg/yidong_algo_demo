import copy
import datetime
import operator
import pymongo
from util.common_func import get_distance, get_area

# import asyncio


client = pymongo.MongoClient("localhost", 27017)
db = client.metro


# method GET_SBWPLAN
# 地铁站 matrix 获取出行方案
# 示例：ss_plan=[['step1地铁上车站','step1地铁线路','step1地铁方向','step1地铁下车站'],['step2地铁上车站','step2地铁线路','step2地铁方向','step2地铁下车站']]
def get_sbwplan_prod(sbw_ostation, sbw_dstation):
    # print('sbw_o', sbw_ostation, 'sbw_d', sbw_dstation)
    sbw_ostation_list = db.stations.find_one({"id": sbw_ostation})
    sbw_dstation_list = db.stations.find_one({"id": sbw_dstation})
    sbw_ostation_name = sbw_ostation_list['name']
    sbw_dstation_name = sbw_dstation_list['name']
    # print(sbw_ostation_name, sbw_dstation_name)
    find_route = db.mt.find_one({"origin": sbw_ostation_name, "destination": sbw_dstation_name})
    # print(find_route)
    if find_route is not None:
        plantype = True
        transit = find_route['transits'][0]
        duration = int(transit['duration'])/60
        segment_list = transit['segments']
        ss_plan = []

        for segment in segment_list:
            try:
                ss_plan.append({0: {'上车站点': segment['bus']['buslines'][0]['departure_stop']['name'],
                                    '线路': segment['bus']['buslines'][0]['name'],
                                    '线路方向': segment['bus']['buslines'][0]['final_station'],
                                    '下车站点': segment['bus']['buslines'][0]['arrival_stop']['name']}})
            except KeyError:
                pass
    else:
        plantype = False
        duration = 1000000
        ss_plan = None

    # return plantype, {'起点': sbw_ostation_name}, {'终点': sbw_dstation_name}, duration, ss_plan
    return plantype,duration,ss_plan

def get_sbwplan_dev(sbw_oid,sbw_did):
    ss_plan=[[sbwstation[sbw_oid].get_name(),'step1地铁线路','step1地铁方向','step1地铁下车站'],['step2地铁上车站','step2地铁线路','step2地铁方向',sbwstation[sbw_did].get_name()]]
    # ss_plan 是oid和did两个地铁站间出行时间最短的地铁方案列表，ss_plan是一个step的list
    #每个step包含[上车站点，线路名称，方向（如果matrix里有的话），下车站点]
    duration=90 # 该方案的总时长，单位是 分钟
    plantype=True # 如果有两站间的方案，plantype为true，没有则false
    return plantype,duration,ss_plan

get_sbwplan = get_sbwplan_dev

from util.data import ydline, ydstation, stationTime, sbwstation


# 获取经过站点集的所有线路的集合
def get_lines_by_stops(stops):
    nlines = []
    for i in stops:
        lines = ydstation[i].get_lines()
        nlines.extend(lines)
    nlines = list({}.fromkeys(nlines).keys())
    return nlines


def get_nearby_stops(stops):
    nearby_stops = []
    for s in stops:
        nearby_stops.extend(copy.deepcopy(ydstation[s].get_stops()[0]))
    return nearby_stops


# 获取线路集上及周边的所有站点的集合
def get_stops_by_lines(lines):
    nstops = []
    for line in lines:
        nstops.extend(list(ydline[line].get_stops().keys()))
    nstops = list({}.fromkeys(nstops).keys())
    nearby_stops = get_nearby_stops(nstops)
    nstops.extend(nearby_stops)
    nstops = list({}.fromkeys(nstops).keys())
    return nstops


# 获取驿动内部规划方案，路径可行，不考虑时间约束
# 输入出发站名称，到达站名称，输出方案（list，换乘会有多个step
# 每一个step是两站间的出行方案（出发站，出发线路，上下行，终点站））
# 输出换乘次数，具体方案；没有可行方案反馈-1，和none
def yd_yd_plan(os_name, ds_name):
    plans = []
    o_nstops = get_nearby_stops([os_name])
    o_nstops.append(os_name)
    d_nstops = get_nearby_stops([ds_name])
    d_nstops.append(ds_name)
    plan0, result0 = yyplan0(o_nstops, d_nstops)
    if plan0 == True:
        for p0 in result0:
            plans.append([p0])
        return 0, plans
    else:
        o_nlines = result0[0]
        # print('o_nstops',o_nstops,'o_nlines',o_nlines,'d_nstops',d_nstops)
        plan1, result1 = yyplan1(o_nstops, o_nlines, d_nstops)
        # print('plan1',plan1,'result1',result1)
        if plan1 == True:
            for p1 in result1:
                plans.append(p1)
            return 1, plans
        else:
            d_nlines = result0[1]
            o_nstops1 = result1[0]
            o_nlines1 = result1[1]
            plan2, result2 = yyplan2(o_nstops, o_nstops1, o_nlines1, d_nlines, d_nstops)
            if plan2 == True:
                for p2 in result2:
                    plans.append(p2)
                return 2, plans
    return -1, None


# 驿动与驿动直达的算法，输入出发站点集list，到达站点集list
# 如果有方案，输出true及方案
# 如果没有，输出false及一次换乘需要的相关输入参数（可减少重复计算）
def yyplan0(o_nstops, d_nstops, o_nlines=[], d_nlines=[]):
    planline = []
    plans = []
    if o_nlines == []:
        o_nlines = get_lines_by_stops(o_nstops)
    if d_nlines == []:
        d_nlines = get_lines_by_stops(d_nstops)
    for i in o_nlines:
        if i in d_nlines:
            planline.append(i)
    if len(planline) > 0:
        for i in planline:
            s = ydline[i].get_stops()
            o_ps = []
            d_ps = []
            for j in o_nstops:
                if j in s:
                    o_ps.append([j, s[j][0]])
            for k in d_nstops:
                if k in s:
                    d_ps.append([k, s[k][0]])
            for ops in o_ps:
                for dps in d_ps:
                    if ops[1] < dps[1]:
                        if ydline[i].get_isCircle() == True:
                            num = len(s)
                            n = dps[1] - ops[1]
                            if n <= (num - n):
                                pl = [ydline[i].get_name(), ydline[i].get_type(), ydline[i].get_id()]
                                plans.append([ops, pl, dps])
                        else:
                            pl = [ydline[i].get_name(), ydline[i].get_type(), ydline[i].get_id()]
                            plans.append([ops, pl, dps])
        if len(plans) > 0:
            return True, plans
        else:
            return False, [o_nlines, d_nlines]
    else:
        return False, [o_nlines, d_nlines]


# 驿动和驿动一次换乘的算法，输入出发站点集list，经过出发站点集的线路list（即可能的step1的线路），到达站点集list
# 如果有方案，输出true及方案
# 如果没有，输出false及二次换乘需要的相关输入参数（可减少重复计算）
def yyplan1(o_nstops, o_nlines, d_nstops):
    # print(o_nstops,o_nlines,d_nstops)
    plans = []
    o_nstops1 = get_stops_by_lines(o_nlines)
    for i in o_nstops:
        o_nstops1.remove(i)
    plan1_1, result1_1 = yyplan0(o_nstops1, d_nstops)
    # print(plan1_1,result1_1)
    if plan1_1 == True:
        for p1 in result1_1:
            # print('p1',p1)
            tstop = p1[0][0]
            # print('tstop',tstop)
            tstops = get_nearby_stops([tstop])
            # print('tstops',tstops)
            tstops.append(tstop)
            plan1_2, result1_2 = yyplan0(o_nstops, tstops)
            if plan1_2 == True:
                for p2 in result1_2:
                    plans.append([p2, p1])
        if len(plans) > 0:
            # print('plans',plans)
            return True, plans
    else:
        # print('result1_1',result1_1)
        o_nlines1 = result1_1[0]
        return False, [o_nstops1, o_nlines1]


# 驿动和驿动两次换乘的算法，输入出发站点集list，可能的第一个换乘站点集，可能的step2的线路，到达站点集list
# 如果有方案，输出true及方案
# 如果没有，输出false及None，停止计算
def yyplan2(o_nstops, o_nstops1, o_nlines1, d_nlines, d_nstops):
    plans = []
    d_nstops1 = get_stops_by_lines(d_nlines)
    for i in d_nstops:
        d_nstops1.remove(i)
    plan2_1, result2_1 = yyplan0(o_nstops1, d_nstops1, o_nlines1)
    if plan2_1 == True:
        for p1 in result2_1:
            tstop1 = p1[0][0]
            tstops1 = get_nearby_stops([tstop1])
            tstops1.append(tstop1)
            plan2_0, result2_0 = yyplan0(o_nstops, tstops1)
            tstop2 = p1[2][0]
            tstops2 = get_nearby_stops([tstop2])
            tstops2.append(tstop2)
            plan2_2, result2_2 = yyplan0(tstops2, d_nstops)
            if plan2_0 == True and plan2_2 == True:
                for p0 in result2_0:
                    for p2 in result2_2:
                        plan = []
                        plan.append(p0)
                        plan.append(p1)
                        plan.append(p2)
                        plans.append(plan)
        if len(plans) > 0:
            return True, plans
    else:
        return False, None


# 对于驿动内部方案，根据时间获取方案的可行班次


# In[672]:


# 获取每一步方案的可行班次，目前设置为出发时间后小于三十分钟以内的等待时间最小的班次
def get_step_routeCode(o_id, lineid, otime):
    codes = []
    for code in stationTime[lineid]:
        if o_id in stationTime[lineid][code]:
            ct = stationTime[lineid][code][o_id]
            td = ct - otime
            waittime = int(td.total_seconds()) / 60
            if waittime > 0 and waittime < 30:
                codes.append([code, waittime])
    if len(codes) > 0:
        codes.sort(key=operator.itemgetter(1))
        return codes[0]
    else:
        return None


# In[662]:


# 获取总方案的可行班次，返回一个列表，没有可行班次的为None
def get_routeCode(otime, plantype, plans):
    codes = []
    if plantype == 0:
        for i in range(len(plans)):
            codes.append([])
            lineid = plans[i][0][1][-1]
            o_id = plans[i][0][0][-1]
            c = get_step_routeCode(o_id, lineid, otime)
            if c != None:
                codes[i] = [c]
            else:
                codes[i] = None
    else:
        for i in range(len(plans)):
            codes.append([])
            ot = otime
            for j in range(len(plans[i])):
                lineid = plans[i][j][1][-1]
                o_id = plans[i][j][0][-1]
                step_code = get_step_routeCode(o_id, lineid, ot)
                if step_code != None:
                    d_id = plans[i][j][2][-1]
                    if d_id in stationTime[lineid][step_code[0]]:
                        transfertime = datetime.timedelta(seconds=300)  # 加上换乘步行时间，此处设为5分钟，
                        ot = stationTime[lineid][step_code[0]][d_id] + transfertime
                        codes[i].append(step_code)
                    else:
                        codes[i] = None
                        break
                else:
                    codes[i] = None
                    break
    return codes


# In[631]:


# 对于驿动内部方案，根据班次和方案获取出行时长


# In[632]:


# 获取每一步方案的出行时长
def get_step_duration(o_id, lineid, d_id, code):
    otime = stationTime[lineid][code][o_id]
    dtime = stationTime[lineid][code][d_id]
    duration = dtime - otime
    return duration


# In[633]:


# 获取总方案的出行时长
def get_plan_duration(plantype, plans, codes):
    pds = []
    if plantype == 0:
        for i in range(len(plans)):
            td = get_step_duration(plans[i][0][0][-1], plans[i][0][1][-1], plans[i][0][2][-1], codes[i][0][0])
            pd = int(td.total_seconds()) / 60 + codes[i][0][1]
            pds.append(pd)
    else:
        for i in range(len(plans)):
            pd = 0
            for j in range(len(plans[i])):
                td = get_step_duration(plans[i][j][0][-1], plans[i][j][1][-1], plans[i][j][2][-1], codes[i][j][0])
                pd += int(td.total_seconds()) / 60 + codes[i][j][1]
            pd += plantype * 5  # 中间换乘步行时间，此处设为5分钟，
            pds.append(pd)
    return pds


# In[634]:


# 对路径上可行的驿动内部方案，根据出行时间和班次，输出时间约束下可行的驿动内部的行程
def out_put_yd_trip(otime, plantype, plans, o_wt=0, d_wt=0):
    o_walktime = datetime.timedelta(seconds=o_wt * 60)  # 获取从起点到出发站点的步行时间，timedelta类型，此处大小与上一致（单位秒）
    otime1 = otime + o_walktime  # 根据出发时刻和步行的timedelta，获取到达出发站点的时刻
    ps = []
    cs = []
    codes = get_routeCode(otime1, plantype, plans)
    for i in range(len(codes)):
        if codes[i] != None:
            ps.append(plans[i])
            cs.append(codes[i])
    if len(ps) > 0:
        pc = []
        pds = get_plan_duration(plantype, ps, cs)
        for i in range(len(ps)):
            pc.append([])
            pc[i].append(ps[i])
            pc[i].append(cs[i])
            pds[i] += d_wt + o_wt
            pc[i].insert(0, int(pds[i]))
            td_duration = pds[i] * 60
            dtime = otime + datetime.timedelta(seconds=td_duration)
            d_time = dtime.strftime('%H:%M')
            pc[i].insert(1, d_time)
        pc.sort(key=operator.itemgetter(0))
        return pc
    else:
        return None


# In[635]:


# ——根据od站点获取驿动与地铁的换乘方案（驿动-地铁，地铁-驿动）


# In[636]:


# 查找驿动直达及一次换乘内站点周边的地铁站，获取与已知地铁站间的出行方案
def yd_sbw_plan(os_name,o_type,ds_name,d_type):
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
            nearby_sbws[sbws].append(ys)
    # 获取周边地铁站与给定地铁站间的出行方案ss_plan
    tsf_plans=[]
    ss_plans=[]
    nearbysbw=list(nearby_sbws.keys())
    if sbw_s in nearbysbw:
        nearbysbw.remove(sbw_s)
    for sbws in nearbysbw:
        if o_type==0 and d_type==1:
            plantype,duration,ss_plan=get_sbwplan(sbws,sbw_s)
            if plantype==False:
                continue
            tsf_ydstop=nearby_sbws[sbws]
            for ys in tsf_ydstop:
                if os_name==ys:
                    continue
                ypt,ydplans=yd_yd_plan(os_name,ys)
        elif o_type==1 and d_type==0:
            plantype,duration,ss_plan=get_sbwplan(sbw_s,sbws)
            if plantype==False:
                continue
            tsf_ydstop=nearby_sbws[sbws]
            for ys in tsf_ydstop:
                if ds_name==ys:
                    continue
                ypt,ydplans=yd_yd_plan(ys,ds_name)
        for p in ydplans:
            plan=[]
            plan.append([ypt,[p]])
            plan.append([duration,ss_plan])
            tsf_plans.append(plan)
    # 输出驿动站点与给定地铁站间的出行方案tsf_plan
    if len(tsf_plans)==0:
        return -2,None
    return 3,tsf_plans


# In[637]:


# 对路径上可行的地铁方案，根据出行时间，输出包含时刻信息的地铁方案
def out_put_sbw_trip(otime, duration, sbwplans, o_wt=0, d_wt=0):
    o_walktime = datetime.timedelta(seconds=o_wt * 60)  # 获取从起点到出发站点的步行时间，timedelta类型，此处大小与上一致（单位秒）
    otime1 = otime + o_walktime  # 根据出发时刻和步行的timedelta，获取到达出发站点的时刻
    pc = []
    total_d = int(duration) + d_wt + o_wt
    pc.append(total_d)
    pc.append(sbwplans)
    td_duration = total_d * 60
    dtime = otime + datetime.timedelta(seconds=td_duration)
    d_time = dtime.strftime('%H:%M')
    pc.insert(1, d_time)
    return pc


# In[638]:


# ——根据od经纬度和时间计算出行方案


# In[639]:


# 找出od最近的驿动站点（后面的计算中会包含该站点周边站，故此处只考虑距离最近的即可）
def get_odstops(o_lat, o_lng, d_lat, d_lng):
    # 设置驿动最远阈值1000米范围内
    o_dmin = [500, None]
    d_dmin = [500, None]
    for key in ydstation:
        o_d = get_distance(o_lat, o_lng, ydstation[key].get_location()[0], ydstation[key].get_location()[1])
        d_d = get_distance(d_lat, d_lng, ydstation[key].get_location()[0], ydstation[key].get_location()[1])
        o_dmin = ([o_d, key] if o_d < o_dmin[0] else o_dmin)
        d_dmin = ([d_d, key] if d_d < d_dmin[0] else d_dmin)
    return o_dmin, d_dmin


# 寻找公交站点可用百度地图周边poi接口


# In[640]:


# 找出最近的地铁站点（后面的计算中会包含该站点周边站，故此处只考虑距离最近的即可）
def get_sbwstops(lat, lng):
    # 设置最远阈值1000米范围内
    dmin = [500, None]
    for key in sbwstation:
        d = get_distance(lat, lng, sbwstation[key].get_location()[0], sbwstation[key].get_location()[1])
        dmin = ([d, key] if d < dmin[0] else dmin)
    return dmin


# In[641]:


# 规划驿动内部的行程
def plan_yd_yd_trip(os, ds, otime, o_location=[], d_location=[]):
    o_wt = int(os[0] / 60)  # 获取从起点到出发站点的步行时长，可以调百度api，此处设为5分钟
    d_wt = int(ds[0] / 60)  # 获取从到达站点到目的地的步行时间，可以调百度api，此处设为5分钟
    plantype, plans = yd_yd_plan(os[1], ds[1])
    if plantype != -1:
        return out_put_yd_trip(otime, plantype, plans, o_wt, d_wt)
    return None


# In[642]:


# 规划驿动-地铁的行程
def plan_yd_sbw_trip(os, sbw_ds, otime, o_location=[], d_location=[]):
    o_wt = int(os[0] / 60)  # 获取从起点到出发站点的步行时长，可以调百度api，此处设为5分钟
    d_wt = int(sbw_ds[0] / 60)  # 获取从到达站点到目的地的步行时间，可以调百度api，此处设为5分钟
    plantype, plans = yd_sbw_plan(os[1], 0, sbw_ds[1], 1)
    outputs = []
    tsf_wt = 5
    if plantype != -2:
        for plan in plans:
            [ydplantype, ydplans] = plan[0]
            [sbw_duration, sbwplans] = plan[1]
            ydstep = out_put_yd_trip(otime, ydplantype, ydplans, o_wt, tsf_wt)
            if ydstep == None:
                continue
            for yds in ydstep:
                yd_dtime = datetime.datetime.strptime(yds[1], '%H:%M')
                sbwstep = out_put_sbw_trip(yd_dtime, sbw_duration, sbwplans, tsf_wt, d_wt)
                output = []
                total_d = yds[0] + sbwstep[0]
                output.append(total_d)
                output.append(yds)
                output.append(sbwstep)
                outputs.append(output)
        outputs.sort(key=operator.itemgetter(0))
        if len(outputs) < 4:
            return outputs
        else:
            return outputs[0:4]  # 只输出行程时间最短的3个及以下
    return None


# In[679]:


# 规划地铁-驿动的行程
def plan_sbw_yd_trip(sbw_os, ds, otime, o_location=[], d_location=[]):
    o_wt = int(sbw_os[0] / 60)  # 获取从起点到出发站点的步行时长，可以调百度api，此处设为5分钟
    d_wt = int(ds[0] / 60)  # 获取从到达站点到目的地的步行时间，可以调百度api，此处设为5分钟
    plantype, plans = yd_sbw_plan(sbw_os[1], 1, ds[1], 0)
    outputs = []
    tsf_wt = 5
    if plantype != -2:
        for plan in plans:
            [ydplantype, ydplans] = plan[0]
            [sbw_duration, sbwplans] = plan[1]
            sbwstep = out_put_sbw_trip(otime, sbw_duration, sbwplans, o_wt, tsf_wt)
            sbw_dtime = datetime.datetime.strptime(sbwstep[1], '%H:%M')
            ydstep = out_put_yd_trip(sbw_dtime, ydplantype, ydplans, o_wt, tsf_wt)
            if ydstep == None:
                continue
            for yds in ydstep:
                output = []
                total_d = yds[0] + sbwstep[0]
                output.append(total_d)
                output.append(sbwstep)
                output.append(yds)
                outputs.append(output)
        outputs.sort(key=operator.itemgetter(0))
        if len(outputs) < 4:
            return outputs
        else:
            return outputs[0:4]
    return None


# 利用上述method，输入出发地目的地的经纬度，和出发时刻，获取出行方案
# 输出优先级：驿动内部，驿动-地铁，地铁-驿动
def plan_trip(o_lat, o_lng, d_lat, d_lng, o_time):
    otime = datetime.datetime.strptime(o_time, '%H:%M')
    os, ds = get_odstops(o_lat, o_lng, d_lat, d_lng)
    if os[1] != None and ds[1] != None and os[1] != ds[1]:
        trip = plan_yd_yd_trip(os, ds, otime)
        if trip != None:
            return trip
    if (os[1] != None or ds[1] != None) and os[1] != ds[1]:
        sbw_ds = get_sbwstops(d_lat, d_lng)
        if os[1] != None and sbw_ds[1] != None:
            trip = plan_yd_sbw_trip(os, sbw_ds, otime)
            if trip != None:
                return trip
        sbw_os = get_sbwstops(o_lat, o_lng)
        if ds[1] != None and sbw_os[1] != None:
            trip = plan_sbw_yd_trip(sbw_os, ds, otime)
            if trip != None:
                return trip
    return None


# if __name__ == '__main__':
#     # # o-柏林映象周边，d-安亭新镇周边
#     # # 驿动内直达换乘
#     # o_lat=31.2712
#     # o_lng=121.178615
#     # d_lat=31.277159
#     # d_lng=121.175772
#     # o_time='07:10'
#     # otime = datetime.datetime.strptime(o_time,'%H:%M')
#     # os,ds=get_odstops(o_lat,o_lng,d_lat,d_lng)
#     # plan_yd_yd_trip(os,ds,otime)
#     #
#     #
#     # # In[670]:
#     #
#     #
#     # # o-柏林映象周边，d-中山公园周边
#     # # 驿动内一次换乘
#     # o_lat=31.2712
#     # o_lng=121.178615
#     # d_lat=31.22415
#     # d_lng=121.424639
#     # o_time='07:10'
#     # plan_trip(o_lat,o_lng,d_lat,d_lng,o_time)
#
#
#     # In[684]:
#
#
#     # o-柏林映象周边，d-中山公园周边
#     # 驿动换乘地铁，该类方案的总时长合理性需要利用 百度api 获取到公交出行的时间进行判断，如果长于两地直接公交，那么方案需剔除
#     # o_lat=31.2712
#     # o_lng=121.178615
#     # d_lat=31.22415
#     # d_lng=121.424639
#     # o_time='07:30'
#     # print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time))
#
#
#     # In[687]:
#
#
#     # # o-中山公园周边，d-安亭新镇周边
#     # # 地铁换乘驿动，该类方案的总时长合理性需要利用 百度api 获取到公交出行的时间进行判断，如果长于两地直接公交，那么方案需剔除
#     o_lat=31.22415
#     o_lng=121.424639
#     d_lat=31.277159
#     d_lng=121.175772
#     o_time='16:50'
#     print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time))
#     #
#     #
#     # # In[686]:
#     #
#     #
#     # # 测试用例3-驿动内两次换乘，加上时间约束后没有找到合适的测试用例，仅调用显示路径可行解
#     # o_sname='奥托立夫,1'
#     # d_sname='柏林映象,0'
#     # yd_yd_plan(o_sname,d_sname)
#     #
#     #
#     # # In[650]:
#     #
#     #
#     # # 测试用例2--驿动内一次换乘，加上时间约束后没有找到合适的测试用例，仅调用显示路径可行解
#     # o_sname='柏林映象,0'
#     # d_sname='中山公园,0'
#     # yd_yd_plan(o_sname,d_sname)
#     #
#     #
#     # # In[651]:
#     #
#     #
#     # # 测试用例1-驿动内直达，加上时间约束后没有找到合适的测试用例，仅调用显示路径可行解
#     # o_sname='柏林映象,0'
#     # d_sname='安亭新镇,1'
#     # yd_yd_plan(o_sname,d_sname)
