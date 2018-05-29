import copy
import datetime
import operator
import pymongo
from util_v_0_4.common_func import get_distance, get_area
from config import Config_dev


# method GET_SBWPLAN
# 地铁站 matrix 获取出行方案
# 示例：ss_plan=[['step1地铁上车站','step1地铁线路','step1地铁方向','step1地铁下车站'],['step2地铁上车站','step2地铁线路','step2地铁方向','step2地铁下车站']]

def get_sbwplan_prod(sbw_ostation, sbw_dstation):

    result = Config_dev.rds.get('{}-{}'.format(sbw_ostation,sbw_dstation))
    if result:
        # print(result)
        result = str(result, encoding="utf-8")
        result = eval(result)
        # print(result)
        return result
    find_route = Config_dev.db.mt.find_one({"origin": sbw_ostation, "destination": sbw_dstation})

    if find_route is not None:
        plantype = True
        transit = find_route['transits'][0]
        duration = int(transit['duration'])/60
        price = float(transit['cost'])
        segment_list = transit['segments']
        ss_plan = []

        for segment in segment_list:
            try:
                ss_plan.append([ segment['bus']['buslines'][0]['departure_stop']['name'],
                                 segment['bus']['buslines'][0]['name'],
                                 segment['bus']['buslines'][0]['final_station'],
                                 segment['bus']['buslines'][0]['arrival_stop']['name']])
            except KeyError:
                pass
    else:
        plantype = False
        duration = 1000000
        ss_plan = None
        price = 1000000

    # return plantype, {'起点': sbw_ostation_name}, {'终点': sbw_dstation_name}, duration, ss_plan
    Config_dev.rds.set('{}-{}'.format(sbw_ostation,sbw_dstation),(plantype,duration,price,ss_plan),3600)
    return plantype, duration, price,ss_plan

get_sbwplan=get_sbwplan_prod

from util_v_0_4.data import ydline, ydstation, stationTime, sbwstation, busSchedule


# 获取经过站点集的所有线路的集合
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
        name=ydline[lineid].get_name()
        if name.find('汽车城')!= -1:
            stepprice=discount*ydline[lineid].get_price()[o_id][d_id]/100 #元
        else:
            stepprice=ydline[lineid].get_price()[o_id][d_id]/100 #元
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
    sbw_s_name=sbwstation[sbw_s].get_name()
    for sbws in nearbysbw:
        sbws_name=sbwstation[sbws].get_name()
        nearby_ys=[nearby_sbws[sbws][0],nearby_sbws[sbws][1]]
        nearby_ys.sort(key=operator.itemgetter(1))
        ys=nearby_ys[0][0]
        slatlng=ydstation[ys].get_location()
        if o_type==0 and d_type==1:
            plantype,duration,price,ss_plan=get_sbwplan(sbws_name,sbw_s_name)
            if plantype==False:
                continue
            if os_name==ys:
                continue
            ypt,ydplans=yd_yd_plan(os_name,ys,olatlng,slatlng)
        elif o_type==1 and d_type==0:
            plantype,duration,price,ss_plan=get_sbwplan(sbw_s_name,sbws_name)
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
def get_odstops(o_lat,o_lng,d_lat,d_lng,dis):
    #设置驿动最远阈值1000米范围内
    o_dmin=[dis,None]
    d_dmin=[dis,None]
    ominlat, omaxlat, ominlng, omaxlng=get_area(o_lat,o_lng,dis/1000)
    dminlat, dmaxlat, dminlng, dmaxlng=get_area(d_lat,d_lng,dis/1000)
    for key in ydstation:
        [t_lat,t_lng]=ydstation[key].get_location()
        if t_lat>ominlat and t_lat<omaxlat and t_lng>ominlng and t_lng< omaxlng:
            o_d=get_distance(o_lat,o_lng,ydstation[key].get_location()[0],ydstation[key].get_location()[1])
            o_dmin=([o_d,key] if o_d<o_dmin[0] else o_dmin )
        if t_lat>dminlat and t_lat<dmaxlat and t_lng>dminlng and t_lng< dmaxlng:
            d_d=get_distance(d_lat,d_lng,ydstation[key].get_location()[0],ydstation[key].get_location()[1])
            d_dmin=([d_d,key] if d_d<d_dmin[0] else d_dmin )
    return o_dmin,d_dmin

# 寻找公交站点可用百度地图周边poi接口


# In[42]:


# 找出最近的地铁站点（后面的计算中会包含该站点周边站，故此处只考虑距离最近的即可）
def get_sbwstops(o_lat,o_lng,d_lat,d_lng,dis):
    #设置最远阈值1000米范围内
    o_dmin=[dis,None]
    d_dmin=[dis,None]
    ominlat, omaxlat, ominlng, omaxlng=get_area(o_lat,o_lng,dis/1000)
    dminlat, dmaxlat, dminlng, dmaxlng=get_area(d_lat,d_lng,dis/1000)
    for key in sbwstation:
        [t_lat,t_lng]=sbwstation[key].get_location()
        if t_lat>ominlat and t_lat<omaxlat and t_lng>ominlng and t_lng< omaxlng:
            o_d=get_distance(o_lat,o_lng,sbwstation[key].get_location()[0],sbwstation[key].get_location()[1])
            o_dmin=([o_d,key] if o_d<o_dmin[0] else o_dmin )
        if t_lat>dminlat and t_lat<dmaxlat and t_lng>dminlng and t_lng< dmaxlng:
            d_d=get_distance(d_lat,d_lng,sbwstation[key].get_location()[0],sbwstation[key].get_location()[1])
            d_dmin=([d_d,key] if d_d<d_dmin[0] else d_dmin )
    return o_dmin,d_dmin


# In[43]:


# 规划驿动内部的行程
def plan_yd_yd_trip(os,ds,otime,olatlng,dlatlng,membertype=0):
    o_wt=int(os[0]*1.5/60)# 获取从起点到出发站点的步行时长，可以调百度api，此处速度1m/s，距离为直线距离的1.5倍
    d_wt=int(ds[0]*1.5/60)# 获取从到达站点到目的地的步行时间，可以调百度api，此处速度1m/s
    plantype,plans=yd_yd_plan(os[1],ds[1],olatlng,dlatlng)
    if plantype!=-1:
        plans=out_put_yd_trip(otime,plantype,plans,o_wt,d_wt,membertype)
        if plans!=None:
            return True,yd_json_out_put(plans)
        else:
            return False,'time and codes limit'
    else:
        return None

# In[47]:


# 规划驿动-地铁的行程
def plan_yd_sbw_trip(os,sbw_ds,otime,olatlng,dlatlng,membertype=0):
    o_wt=int(os[0]*1.5/60)# 获取从起点到出发站点的步行时长，可以调百度api，此处速度1m/s
    d_wt=int(sbw_ds[0]*1.5/60)# 获取从到达站点到目的地的步行时间，可以调百度api，此处速度1m/s
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
            if len(outputs)<6:
                plans=outputs
            else:
                plans=outputs[0:5]
            return True,yd_sbw_json_out_put(plans,0)
        else:
            return False,'time and codes limit'
    else:
        return False,'route limit'


# In[48]:


# 规划地铁-驿动的行程
def plan_sbw_yd_trip(sbw_os,ds,otime,olatlng,dlatlng,membertype):
    o_wt=int(sbw_os[0]*1.5/60)# 获取从起点到出发站点的步行时长，可以调百度api，此处设为5分钟
    d_wt=int(ds[0]*1.5/60)# 获取从到达站点到目的地的步行时间，可以调百度api，此处设为5分钟
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
            if len(outputs)<6:
                plans=outputs
            else:
                plans= outputs[0:5]
            return True,yd_sbw_json_out_put(plans,1)
        else:
            return False,'time and codes limit'
    else:
        return False,'route limit'

def plan_sbw_trip(sbw_os,sbw_ds,otime):
    starttime=datetime.datetime.strptime('5:30','%H:%M')
    endtime=datetime.datetime.strptime('22:30','%H:%M')
    o_wt=int(sbw_os[0]*1.5/60)
    d_wt=int(sbw_ds[0]*1.5/60)
    if otime > starttime and otime < endtime:
        sbw_o_name=sbwstation[sbw_os[1]].get_name()
        sbw_d_name=sbwstation[sbw_ds[1]].get_name()
        plantype,duration,price,plans=get_sbwplan(sbw_o_name, sbw_d_name)
        if plantype!=False:
            plan=out_put_sbw_trip(otime,duration,price,plans,o_wt,d_wt)
            joutput=[sbw_json_out_put(plan)]
            return True,joutput
        else:
            return False,'route limit'
    else:
        return False,'time limit'
        
    
        
# In[44]:


def yd_json_out_put(plans):
    joutput=[]
    n=0
    for plan in plans:
        i=n
        joutput.append({})
        n+=1
        joutput[i]['totalDuration']=plan[0]
        joutput[i]['departTime']=plan[1]
        joutput[i]['arriveTime']=plan[2]
        joutput[i]['totalPrice']=plan[3]
        joutput[i]['planStep']=[]
        for j in range(len(plan[4])):
            stepnum=j
            joutput[i]['planStep'].append({})            
            stepcode=plan[5][j]
            otime=datetime.datetime.strptime(stepcode[0],'%H:%M')
            dtime=datetime.datetime.strptime(stepcode[3],'%H:%M')
            duration=dtime-otime
            joutput[i]['planStep'][stepnum]['stepNo']=j+1
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
    joutput['planStep']=[]
    for j in range(len(plan[4])):
        stepnum=j
        joutput['planStep'].append({})
        step=plan[4][j]
        joutput['planStep'][stepnum]['stepNo']=j+1
        joutput['planStep'][stepnum]['o_station']=step[0]
        joutput['planStep'][stepnum]['d_station']=step[-1]
        joutput['planStep'][stepnum]['route']={}
        joutput['planStep'][stepnum]['route']['name']= step[1]
        joutput['planStep'][stepnum]['route']['direction']=step[2]
    return joutput


# In[46]:


def yd_sbw_json_out_put(plans,type):
    joutput=[]
    n=0
    for plan in plans:
        i=n
        joutput.append({})
        n+=1
        joutput[i]['totalDuration']=plan[0]
        joutput[i]['departTime']=plan[1]
        joutput[i]['arriveTime']=plan[2]
        joutput[i]['totalPrice']=plan[3]
        joutput[i]['part']=[]
        if type==0:
            joutput[i]['part'].append({'partNo':type+1,'ydplan':yd_json_out_put([plan[type+4]])[0]})
            joutput[i]['part'].append({'partNo':2-type,'subwayplan':sbw_json_out_put(plan[5-type])})
        else:
            joutput[i]['part'].append({'partNo':2-type,'subwayplan':sbw_json_out_put(plan[5-type])})
            joutput[i]['part'].append({'partNo':type+1,'ydplan':yd_json_out_put([plan[type+4]])[0]})
    return joutput

def sort_trips_by_time(tripsdict):
    all_trips=[]
    output=[]
    no_trip_reason={'no_trip_reason':{}}
    for triptype in tripsdict:
        [type,trips]=tripsdict[triptype]
        if type==True:
            for i in range(len(trips)):
                duration=trips[i]['totalDuration']
                all_trips.append([duration,triptype,trips[i]])
        else:
            no_trip_reason['no_trip_reason'][triptype]=trips
    if len(all_trips)>0:
        all_trips.sort(key=operator.itemgetter(0))
        if tripsdict['subwayPlan'][0]!=False:
            maxtime=tripsdict['subwayPlan'][1][0]['totalDuration']+15
            for i in range(len(all_trips)):
                if all_trips[i][0]<=maxtime:
                    output.append({})
                    output[i]['tripNo']=i+1
                    output[i]['tripType']=all_trips[i][1]
                    output[i]['tripDetails']=all_trips[i][2]
                    if i<4:
                        i+=1
                    else:
                        break
                else:
                    break
        else:
            num=len(all_trips)
            if num>6:
                num=5
            for i in range(num):
                output.append({})
                output[i]['tripNo']=i+1
                output[i]['tripType']=all_trips[i][1]
                output[i]['tripDetails']=all_trips[i][2]
    else:
        output=None
    return output,no_trip_reason
        


# In[49]:


# 利用上述method，输入出发地目的地的经纬度，和出发时刻，获取出行方案
# 输出优先级：驿动内部，驿动-地铁，地铁-驿动
def plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype=0):
    otime= datetime.datetime.strptime(o_time,'%H:%M')
    os,ds=get_odstops(o_lat,o_lng,d_lat,d_lng,500)
    sbw_os,sbw_ds=get_sbwstops(o_lat,o_lng,d_lat,d_lng,500)
    olatlng=[o_lat,o_lng]
    dlatlng=[d_lat,d_lng]
    trips={}
    if os[1]!=None and ds[1]!=None and os[1]!=ds[1]:
        result1,trip1=plan_yd_yd_trip(os,ds,otime,olatlng,dlatlng,membertype)
        if result1==True:
            trips['ydPlan']=[True,trip1]
        else:
            trips['ydPlan']=[False,trip1]
    if (os[1]!=None or ds[1]!=None) and os[1]!=ds[1]:
        if os[1]!=None and sbw_ds[1]!=None:
            result2,trip2=plan_yd_sbw_trip(os,sbw_ds,otime,olatlng,dlatlng,membertype)
            if result2==True:
                trips['yd-subwayPlan']=[True,trip2]
            else:
                trips['yd-subwayPlan']=[False,trip2]
        if ds[1]!=None and sbw_os[1]!=None:
            result3,trip3=plan_sbw_yd_trip(sbw_os,ds,otime,olatlng,dlatlng,membertype)
            if result3==True:
                trips['subway-ydPlan']=[True,trip3]
            else:
                trips['subway-ydPlan']=[False,trip3]
    if sbw_os[1]!=None and sbw_ds[1]!= None and sbw_os[1]!= sbw_ds[1]:
        result4,trip4=plan_sbw_trip(sbw_os,sbw_ds,otime)
        if result4==True:
            trips['subwayPlan']=[True,trip4]
        else:
            trips['subwayPlan']=[False,trip4]
    if ('subwayPlan' not in trips) or ('subwayPlan' in trips and trips['subwayPlan'][1]=='route limit'):
        sbw_os,sbw_ds=get_sbwstops(o_lat,o_lng,d_lat,d_lng,1000)
        if sbw_os[1]!=None and sbw_ds[1]!= None and sbw_os[1]!= sbw_ds[1]:
            result4,trip4=plan_sbw_trip(sbw_os,sbw_ds,otime)
            if result4==True:
                trips['subwayPlan']=[True,trip4]
            else:
                trips['subwayPlan']=[False,trip4]
        else:
            if 'subwayPlan' not in trips:
                trip4='subway station limit'
                trips['subwayPlan']=[False,trip4]
    return sort_trips_by_time(trips)

