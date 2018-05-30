import copy
import math
import operator
import datetime
from config import Config_dev
from .data_new import data_init


class YidongAlgo(object):
    def __init__(self):
        self.init_set()

    @classmethod
    def init(cls,app):
        app.algo = cls()

    def init_set(self):
        self.ydline, self.ydstation, self.stationTime, self.sbwstation, self.sbwtime, self.sbwline, self.busSchedule = data_init()

    def update_data(self):
        self.init_set()

    def get_sbwplan(self,sbw_ostation, sbw_dstation):
        result = Config_dev.rds.get('{}-{}'.format(sbw_ostation, sbw_dstation))
        if result:
            # print(result)
            result = str(result, encoding="utf-8")
            result = eval(result)
            # print(result)
            return result
        find_route = Config_dev.db.mt.find_one({"origin": sbw_ostation, "destination": sbw_dstation})
        # print(find_route)
        if find_route is not None:
            plantype = True
            transit = find_route['transits'][0]
            duration = int(transit['duration']) / 60
            price = float(transit['cost'])
            segment_list = transit['segments']
            ss_plan = []

            for segment in segment_list:
                try:
                    ss_plan.append([segment['bus']['buslines'][0]['departure_stop']['name'],
                                    segment['bus']['buslines'][0]['name'],
                                    '往' + segment['bus']['buslines'][0]['final_station'].strip(),
                                    segment['bus']['buslines'][0]['arrival_stop']['name']])
                except KeyError:
                    pass
        else:
            plantype = False
            duration = 1000000
            ss_plan = None
            price = 1000000

        # return plantype, {'起点': sbw_ostation_name}, {'终点': sbw_dstation_name}, duration, ss_plan
        Config_dev.rds.set('{}-{}'.format(sbw_ostation, sbw_dstation), (plantype, duration, price, ss_plan), 3600)
        return plantype, duration, price, ss_plan

    def get_lines_by_stops(self,stops):
        nlines = []
        for i in stops:
            lines = self.ydstation[i].get_lines()
            nlines.extend(lines)
        nlines = list({}.fromkeys(nlines).keys())
        return nlines

    def get_nearby_stops(self,stops):
        nearby_stops = []
        for s in stops:
            nearby_stop = copy.deepcopy(self.ydstation[s].get_stops()[0])
            if nearby_stop != None:
                nearby_stops.extend(list(nearby_stop.keys()))
        return nearby_stops

    def get_stops_by_lines(self,lines):
        nstops = []
        for line in lines:
            nstops.extend(list(self.ydline[line].get_stops().keys()))
        nstops = list({}.fromkeys(nstops).keys())
        nearby_stops = self.get_nearby_stops(nstops)
        nstops.extend(nearby_stops)
        nstops = list({}.fromkeys(nstops).keys())
        return nstops

    # 获取驿动内部规划方案，路径可行，不考虑时间约束
    # 输入出发站名称，到达站名称，输出方案（list，换乘会有多个step
    # 每一个step是两站间的出行方案（出发站，出发线路，上下行，终点站））
    # 输出换乘次数，具体方案；没有可行方案反馈-1，和none
    def yd_yd_plan(self,os_name, ds_name, olatlng, dlatlng):
        plans = []
        o_nstops = self.get_nearby_stops([os_name])
        o_nstops.append(os_name)
        d_nstops = self.get_nearby_stops([ds_name])
        d_nstops.append(ds_name)
        plan0, result0 = self.yyplan0(o_nstops, d_nstops, oclatlng=olatlng, dclatlng=dlatlng)
        if plan0 == True:
            for p0 in result0:
                plans.append([p0])
            return 0, plans
        else:
            o_nlines = result0[0]
            plan1, result1 = self.yyplan1(o_nstops, o_nlines, d_nstops, olatlng, dlatlng)
            if plan1 == True:
                for p1 in result1:
                    plans.append(p1)
                return 1, plans
            else:
                d_nlines = result0[1]
                o_nstops1 = result1[0]
                o_nlines1 = result1[1]
                plan2, result2 = self.yyplan2(o_nstops, o_nstops1, o_nlines1, d_nlines, d_nstops, olatlng, dlatlng)
                if plan2 == True:
                    for p2 in result2:
                        plans.append(p2)
                    return 2, plans
                else:
                    return -1, None
        return -1, None

    def yyplan0(self,o_nstops, d_nstops, o_nlines=[], d_nlines=[], oclatlng=None, dclatlng=None):
        planline = []
        plans = []
        if o_nlines == []:
            o_nlines = self.get_lines_by_stops(o_nstops)
        if d_nlines == []:
            d_nlines = self.get_lines_by_stops(d_nstops)
        for i in o_nlines:
            if i in d_nlines:
                planline.append(i)
        if len(planline) > 0:
            for i in planline:
                s = self.ydline[i].get_stops()
                o_ps = []
                d_ps = []
                mind = 10000
                for j in o_nstops:
                    if j in s and j.find('仅下客') == -1:
                        if oclatlng != None:
                            jlatlng = self.ydstation[j].get_location()
                            d = self.get_distance(jlatlng[0], jlatlng[1], oclatlng[0], oclatlng[1])
                            if d < mind:
                                mind = d
                                o_ps = [[j, s[j][0]]]
                            else:
                                continue
                        else:
                            o_ps.append([j, s[j][0]])
                mind = 10000
                for k in d_nstops:
                    if k in s:
                        if dclatlng != None:
                            klatlng = self.ydstation[k].get_location()
                            d = self.get_distance(klatlng[0], klatlng[1], dclatlng[0], dclatlng[1])
                            if d < mind:
                                mind = d
                                d_ps = [[k, s[k][0]]]
                            else:
                                continue
                        else:
                            d_ps.append([k, s[k][0]])
                for ops in o_ps:
                    for dps in d_ps:
                        if ops[1] < dps[1]:
                            if self.ydline[i].get_isCircle() == True:
                                num = len(s)
                                n = dps[1] - ops[1]
                                if n <= (num - n):
                                    pl = [self.ydline[i].get_name(), self.ydline[i].get_type(), self.ydline[i].get_id()]
                                    plans.append([ops, pl, dps])
                            else:
                                pl = [self.ydline[i].get_name(), self.ydline[i].get_type(), self.ydline[i].get_id()]
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
    def yyplan1(self,o_nstops, o_nlines, d_nstops, olatlng, dlatlng):
        plans = []
        o_nstops1 = self.get_stops_by_lines(o_nlines)
        for i in o_nstops:
            o_nstops1.remove(i)
        plan1_1, result1_1 = self.yyplan0(o_nstops1, d_nstops, dclatlng=dlatlng)
        if plan1_1 == True:
            for p1 in result1_1:
                tstop = p1[0][0]
                tstops = self.get_nearby_stops([tstop])
                tstops.append(tstop)
                dclatlng = self.ydstation[tstop].get_location()
                plan1_2, result1_2 = self.yyplan0(o_nstops, tstops, oclatlng=olatlng, dclatlng=dclatlng)
                if plan1_2 == True:
                    for p2 in result1_2:
                        plans.append([p2, p1])
            if len(plans) > 0:
                return True, plans
            else:
                o_nlines1 = result1_1[0]
                return False, [o_nstops1, o_nlines1]
        else:
            o_nlines1 = result1_1[0]
            return False, [o_nstops1, o_nlines1]

    # 驿动和驿动两次换乘的算法，输入出发站点集list，可能的第一个换乘站点集，可能的step2的线路，到达站点集list
    # 如果有方案，输出true及方案
    # 如果没有，输出false及None，停止计算
    def yyplan2(self,o_nstops, o_nstops1, o_nlines1, d_nlines, d_nstops, olatlng, dlatlng):
        plans = []
        d_nstops1 = self.get_stops_by_lines(d_nlines)
        for i in d_nstops:
            d_nstops1.remove(i)
        plan2_1, result2_1 = self.yyplan0(o_nstops1, d_nstops1, o_nlines1)
        if plan2_1 == True:
            for p1 in result2_1:
                tstop1 = p1[0][0]
                tstops1 = self.get_nearby_stops([tstop1])
                tstops1.append(tstop1)
                dclatlng = self.ydstation[tstop1].get_location()
                plan2_0, result2_0 = self.yyplan0(o_nstops, tstops1, oclatlng=olatlng, dclatlng=dclatlng)
                tstop2 = p1[2][0]
                tstops2 = self.get_nearby_stops([tstop2])
                tstops2.append(tstop2)
                oclatlng = self.ydstation[tstop2].get_location()
                plan2_2, result2_2 = self.yyplan0(tstops2, d_nstops, oclatlng=oclatlng, dclatlng=dlatlng)
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
        else:
            return False, None

    def get_step_routeCode(self,o_id, lineid, d_id, otime):
        codes = []
        for code in self.stationTime[lineid]:
            if (o_id in self.stationTime[lineid][code]) and (d_id in self.stationTime[lineid][code]):
                ct = self.stationTime[lineid][code][o_id]
                td = ct - otime
                waittime = int(td.total_seconds()) / 60
                if waittime > 0 and waittime < 15:
                    if code in self.busSchedule[lineid]:
                        dtime = self.stationTime[lineid][code][d_id]
                        vehicleNo = self.busSchedule[lineid][code]
                        codes.append([otime.strftime('%H:%M'), waittime, ct.strftime('%H:%M'), dtime.strftime('%H:%M'),
                                      vehicleNo, code])
            else:
                continue
        if len(codes) > 0:
            codes.sort(key=operator.itemgetter(1))
            return codes[0]
        else:
            return None

    # 获取总方案的可行班次，返回一个列表，没有可行班次的为None
    def get_routeCode(self,otime, plantype, plans):
        codes = []
        if plantype == 0:
            for i in range(len(plans)):
                codes.append([])
                lineid = plans[i][0][1][-1]
                o_id = plans[i][0][0][-1]
                d_id = plans[i][0][2][-1]
                c = self.get_step_routeCode(o_id, lineid, d_id, otime)
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
                    d_id = plans[i][j][2][-1]
                    step_code = self.get_step_routeCode(o_id, lineid, d_id, ot)
                    if step_code != None:
                        transfertime = datetime.timedelta(seconds=300)  # 加上换乘步行时间，此处设为5分钟，
                        ot = datetime.datetime.strptime(step_code[-3], '%H:%M') + transfertime
                        codes[i].append(step_code)
                    else:
                        codes[i] = None
                        break
        return codes

    # 获取每一步方案的出行时长
    def get_step_duration(self,o_id, lineid, d_id, code):
        otime = self.stationTime[lineid][code][o_id]
        dtime = self.stationTime[lineid][code][d_id]
        duration = dtime - otime
        return duration

    # 获取总方案的出行时长
    def get_plan_duration(self,plantype, plans, codes):
        pds = []
        if plantype == 0:
            for i in range(len(plans)):
                td = self.get_step_duration(plans[i][0][0][-1], plans[i][0][1][-1], plans[i][0][2][-1], codes[i][0][-1])
                pd = int(td.total_seconds()) / 60 + codes[i][0][1]
                pds.append(pd)
        else:
            for i in range(len(plans)):
                pd = 0
                for j in range(len(plans[i])):
                    td = self.get_step_duration(plans[i][j][0][-1], plans[i][j][1][-1], plans[i][j][2][-1], codes[i][j][-1])
                    pd += int(td.total_seconds()) / 60 + codes[i][j][1]
                pd += plantype * 5  # 中间换乘步行时间，此处设为5分钟，
                pds.append(pd)
        return pds

    # 获取方案的价格
    def get_plan_price(self,membertype, ydplan):
        if membertype == 0:
            discount = 1
        elif membertype == 1:
            discount = 0.3
        elif membertype == 2:
            discount = 0.2
        price = 0
        pricelist = []
        for step in ydplan:
            o_id = step[0][-1] - 1
            d_id = step[2][-1] - 1
            lineid = step[1][-1]
            name = self.ydline[lineid].get_name()
            if name.find('汽车城') != -1:
                stepprice = discount * self.ydline[lineid].get_price()[o_id][d_id] / 100  # 元
            else:
                stepprice = self.ydline[lineid].get_price()[o_id][d_id] / 100  # 元
            pricelist.append(stepprice)
            price += stepprice
        price = round(price, 2)
        return price, pricelist

    # 对路径上可行的驿动内部方案，根据出行时间和班次，输出时间约束下可行的驿动内部的行程
    def out_put_yd_trip(self,otime, plantype, plans, o_wt=0, d_wt=0, membertype=0):
        o_walktime = datetime.timedelta(seconds=o_wt * 60)  # 获取从起点到出发站点的步行时间，timedelta类型，此处大小与上一致（单位秒）
        otime1 = otime + o_walktime  # 根据出发时刻和步行的timedelta，获取到达出发站点的时刻
        ps = []
        cs = []
        codes = self.get_routeCode(otime1, plantype, plans)
        for i in range(len(codes)):
            if codes[i] != None:
                ps.append(plans[i])
                cs.append(codes[i])
        if len(ps) > 0:
            pc = []
            pds = self.get_plan_duration(plantype, ps, cs)
            for i in range(len(ps)):
                pc.append([])
                t_price, pricelist = self.get_plan_price(membertype, ps[i])
                pc[i].append(ps[i])
                pc[i].append(cs[i])
                pc[i].append(pricelist)
                pds[i] += d_wt + o_wt
                pc[i].insert(0, int(pds[i]))
                td_duration = pds[i] * 60
                dtime = otime + datetime.timedelta(seconds=td_duration)
                o_time = otime.strftime('%H:%M')
                d_time = dtime.strftime('%H:%M')
                pc[i].insert(1, o_time)
                pc[i].insert(2, d_time)
                pc[i].insert(3, t_price)
                pc[i]
            pc.sort(key=operator.itemgetter(0))
            return pc
        else:
            return None

    # 查找驿动直达及一次换乘内站点周边的地铁站，获取与已知地铁站间的出行方案
    def yd_sbw_plan(self,os_name, o_type, ds_name, d_type, olatlng, dlatlng):
        if o_type == 0 and d_type == 1:
            o_nstops = self.get_nearby_stops([os_name])
            o_nstops.append(os_name)
            yline0 = self.get_lines_by_stops(o_nstops)
            sbw_s = ds_name
        elif o_type == 1 and d_type == 0:
            d_nstops = self.get_nearby_stops([ds_name])
            d_nstops.append(ds_name)
            yline0 = self.get_lines_by_stops(d_nstops)
            sbw_s = os_name
        # 获取给定驿动站点的直达站点集
        ystation0 = self.get_stops_by_lines(yline0)
        nearby_stops = self.get_nearby_stops(ystation0)
        ystation0.extend(nearby_stops)
        ystation0 = list({}.fromkeys(ystation0).keys())
        # 获取给定驿动站点的直达和一次换乘站点集
        yline1 = self.get_lines_by_stops(ystation0)
        ystation1 = self.get_stops_by_lines(yline1)
        nearby_stops = self.get_nearby_stops(ystation1)
        ystation1.extend(nearby_stops)
        ystation1 = list({}.fromkeys(ystation1).keys())
        # 获取上述站点周边地铁站
        nearby_sbws = {}
        for ys in ystation1:
            for sbws in self.ydstation[ys].get_stops()[1]:
                nearby_sbws[sbws] = []
        for ys in ystation1:
            for sbws in self.ydstation[ys].get_stops()[1]:
                d = self.ydstation[ys].get_stops()[1][sbws]
                nearby_sbws[sbws].append([ys, d])
        # 获取周边地铁站与给定地铁站间的出行方案ss_plan
        tsf_plans = []
        nearbysbw = list(nearby_sbws.keys())
        if sbw_s in nearbysbw:
            nearbysbw.remove(sbw_s)
        sbw_s_name = self.sbwstation[sbw_s].get_name()
        for sbws in nearbysbw:
            sbws_name = self.sbwstation[sbws].get_name()
            nearby_ys = []
            for i in range(len(nearby_sbws[sbws])):
                nearby_ys.append(nearby_sbws[sbws][i])
            nearby_ys.sort(key=operator.itemgetter(1))
            ys = nearby_ys[0][0]
            slatlng = self.ydstation[ys].get_location()
            if o_type == 0 and d_type == 1:
                plantype, duration, price, ss_plan = self.get_sbwplan(sbws_name, sbw_s_name)
                if plantype == False:
                    continue
                if os_name == ys:
                    continue
                ypt, ydplans = self.yd_yd_plan(os_name, ys, olatlng, slatlng)
            elif o_type == 1 and d_type == 0:
                plantype, duration, price, ss_plan = self.get_sbwplan(sbw_s_name, sbws_name)
                if plantype == False:
                    continue
                if ds_name == ys:
                    continue
                ypt, ydplans = self.yd_yd_plan(ys, ds_name, slatlng, dlatlng)
            if ypt != -1:
                for p in ydplans:
                    plan = []
                    plan.append([ypt, [p]])
                    plan.append([duration, price, ss_plan])
                    tsf_plans.append(plan)
            else:
                continue
        # 输出驿动站点与给定地铁站间的出行方案tsf_plan
        if len(tsf_plans) == 0:
            return -2, None
        else:
            return 3, tsf_plans

    # 对路径上可行的地铁方案，根据出行时间约束，输出包含时刻信息的地铁方案
    def out_put_sbw_trip(self,otime, duration, price, sbwplans, o_wt=0, d_wt=0):
        o_walktime = datetime.timedelta(seconds=o_wt * 60)  # 获取从起点到出发站点的步行时间，timedelta类型，此处大小与上一致（单位秒）
        otime1 = otime + o_walktime  # 根据出发时刻和步行的timedelta，获取到达出发站点的时刻
        pc = []
        total_d = int(duration) + d_wt + o_wt
        pc.append(total_d)
        pc.append(sbwplans)
        td_duration = total_d * 60
        o_time = otime.strftime('%H:%M')
        dtime = otime + datetime.timedelta(seconds=td_duration)
        d_time = dtime.strftime('%H:%M')
        pc.insert(1, o_time)
        pc.insert(2, d_time)
        pc.insert(3, price)
        o = sbwplans[0][0].strip()
        o_d = sbwplans[0][-1].strip()
        olname = sbwplans[0][1]
        oline = ""
        for key in self.sbwline:
            if key.find(olname) != -1:
                isOin = False
                isO_Din = False
                for i in range(len(self.sbwline[key][1])):
                    if o == self.sbwline[key][1][i]['station']:
                        isOin = True
                    if o_d == self.sbwline[key][1][i]['station']:
                        isO_Din = True
                if isOin == True and isO_Din == True:
                    oline = self.sbwline[key][0]
        odir = sbwplans[0][-2]
        d = sbwplans[-1][-1].strip()
        d_o = sbwplans[-1][0].strip()
        dlname = sbwplans[-1][1]
        dline = ""
        for key in self.sbwline:
            if key.find(dlname) != -1:
                isDin = False
                isD_Oin = False
                for i in range(len(self.sbwline[key][1])):
                    if d == self.sbwline[key][1][i]['station']:
                        isDin = True
                    if d_o == self.sbwline[key][1][i]['station']:
                        isD_Oin = True
                if isDin == True and isD_Oin == True:
                    dline = self.sbwline[key][0]
        ddir = sbwplans[-1][-2]
        if oline != "" and dline != "":
            if odir in self.sbwtime[o][oline]['first'] and ddir in self.sbwtime[d][dline]['last']:
                first = self.sbwtime[o][oline]['first'][odir]
                last = self.sbwtime[d][dline]['last'][ddir]
                firsttime = datetime.datetime.strptime(first, '%H:%M')
                lasttime = datetime.datetime.strptime(last, '%H:%M')
                if otime > firsttime and dtime < lasttime:
                    return pc
                else:
                    return None
            else:
                return None
        else:
            return None

    # 找出od最近的驿动站点（后面的计算中会包含该站点周边站，故此处只考虑距离最近的即可）
    def get_odstops(self,o_lat, o_lng, d_lat, d_lng, dis):
        # 设置驿动最远阈值1000米范围内
        o_dmin = [dis, None]
        d_dmin = [dis, None]
        ominlat, omaxlat, ominlng, omaxlng = self.get_area(o_lat, o_lng, dis / 1000)
        dminlat, dmaxlat, dminlng, dmaxlng = self.get_area(d_lat, d_lng, dis / 1000)
        for key in self.ydstation:
            [t_lat, t_lng] = self.ydstation[key].get_location()
            if t_lat > ominlat and t_lat < omaxlat and t_lng > ominlng and t_lng < omaxlng:
                o_d = self.get_distance(o_lat, o_lng, self.ydstation[key].get_location()[0], self.ydstation[key].get_location()[1])
                o_dmin = ([o_d, key] if o_d < o_dmin[0] else o_dmin)
            if t_lat > dminlat and t_lat < dmaxlat and t_lng > dminlng and t_lng < dmaxlng:
                d_d = self.get_distance(d_lat, d_lng, self.ydstation[key].get_location()[0], self.ydstation[key].get_location()[1])
                d_dmin = ([d_d, key] if d_d < d_dmin[0] else d_dmin)
        return o_dmin, d_dmin

    # 找出最近的地铁站点（后面的计算中会包含该站点周边站，故此处只考虑距离最近的即可）
    def get_sbwstops(self,o_lat, o_lng, d_lat, d_lng, dis):
        # 设置最远阈值1000米范围内
        o_dmin = [dis, None]
        d_dmin = [dis, None]
        ominlat, omaxlat, ominlng, omaxlng = self.get_area(o_lat, o_lng, dis / 1000)
        dminlat, dmaxlat, dminlng, dmaxlng = self.get_area(d_lat, d_lng, dis / 1000)
        for key in self.sbwstation:
            [t_lat, t_lng] = self.sbwstation[key].get_location()
            if t_lat > ominlat and t_lat < omaxlat and t_lng > ominlng and t_lng < omaxlng:
                o_d = self.get_distance(o_lat, o_lng, self.sbwstation[key].get_location()[0], self.sbwstation[key].get_location()[1])
                o_dmin = ([o_d, key] if o_d < o_dmin[0] else o_dmin)
            if t_lat > dminlat and t_lat < dmaxlat and t_lng > dminlng and t_lng < dmaxlng:
                d_d = self.get_distance(d_lat, d_lng, self.sbwstation[key].get_location()[0], self.sbwstation[key].get_location()[1])
                d_dmin = ([d_d, key] if d_d < d_dmin[0] else d_dmin)
        return o_dmin, d_dmin

    # 规划驿动内部的行程
    def plan_yd_yd_trip(self,os, ds, otime, olatlng, dlatlng, membertype=0):
        o_wt = int(os[0] * 1.5 / 60)  # 获取从起点到出发站点的步行时长，可以调百度api，此处速度1m/s，距离为直线距离的1.5倍
        d_wt = int(ds[0] * 1.5 / 60)  # 获取从到达站点到目的地的步行时间，可以调百度api，此处速度1m/s
        plantype, plans = self.yd_yd_plan(os[1], ds[1], olatlng, dlatlng)
        if plantype != -1:
            plans = self.out_put_yd_trip(otime, plantype, plans, o_wt, d_wt, membertype)
            if plans != None:
                return True, self.yd_yd_json_out_put(plans)
            else:
                return False, 'time and codes limit'
        else:
            return None

    # 规划驿动-地铁的行程
    def plan_yd_sbw_trip(self,os, sbw_ds, otime, olatlng, dlatlng, membertype=0):
        o_wt = int(os[0] * 1.5 / 60)  # 获取从起点到出发站点的步行时长，可以调百度api，此处速度1m/s
        d_wt = int(sbw_ds[0] * 1.5 / 60)  # 获取从到达站点到目的地的步行时间，可以调百度api，此处速度1m/s
        plantype, plans = self.yd_sbw_plan(os[1], 0, sbw_ds[1], 1, olatlng, dlatlng)
        outputs = []
        tsf_wt = 5  # 换乘时间
        if plantype != -2:
            for plan in plans:
                [ydplantype, ydplans] = plan[0]
                [sbw_duration, sbw_price, sbwplans] = plan[1]
                ydstep = self.out_put_yd_trip(otime, ydplantype, ydplans, o_wt, tsf_wt, membertype)
                if ydstep == None:
                    continue
                for yds in ydstep:
                    yd_dtime = datetime.datetime.strptime(yds[2], '%H:%M')
                    sbwstep = self.out_put_sbw_trip(yd_dtime, sbw_duration, sbw_price, sbwplans, tsf_wt, d_wt)
                    if sbwstep == None:
                        continue
                    output = []
                    total_d = yds[0] + sbwstep[0]
                    t_duration = total_d * 60
                    total_p = sbw_price + yds[3]
                    output.append(total_d)
                    output.append(total_p)
                    output.append(yds)
                    output.append(sbwstep)
                    o_time = otime.strftime('%H:%M')
                    dtime = otime + datetime.timedelta(seconds=t_duration)
                    d_time = dtime.strftime('%H:%M')
                    output.insert(1, o_time)
                    output.insert(2, d_time)
                    outputs.append(output)
            outputs.sort(key=operator.itemgetter(0))
            if len(outputs) > 0:
                if len(outputs) < 6:
                    plans = outputs
                else:
                    plans = outputs[0:5]
                return True, self.yd_sbw_json_out_put(plans, 0)
            else:
                return False, 'time and codes limit'
        else:
            return False, 'route limit'

    # 规划地铁-驿动的行程
    def plan_sbw_yd_trip(self,sbw_os, ds, otime, olatlng, dlatlng, membertype):
        o_wt = int(sbw_os[0] * 1.5 / 60)  # 获取从起点到出发站点的步行时长，可以调百度api，此处设为5分钟
        d_wt = int(ds[0] * 1.5 / 60)  # 获取从到达站点到目的地的步行时间，可以调百度api，此处设为5分钟
        plantype, plans = self.yd_sbw_plan(sbw_os[1], 1, ds[1], 0, olatlng, dlatlng)
        outputs = []
        tsf_wt = 5
        if plantype != -2:
            for plan in plans:
                [ydplantype, ydplans] = plan[0]
                [sbw_duration, sbw_price, sbwplans] = plan[1]
                sbwstep = self.out_put_sbw_trip(otime, sbw_duration, sbw_price, sbwplans, o_wt, tsf_wt)
                if sbwstep == None:
                    continue
                sbw_dtime = datetime.datetime.strptime(sbwstep[2], '%H:%M')
                ydstep = self.out_put_yd_trip(sbw_dtime, ydplantype, ydplans, o_wt, tsf_wt, membertype)
                if ydstep == None:
                    continue
                for yds in ydstep:
                    output = []
                    total_d = yds[0] + sbwstep[0]
                    t_duration = total_d * 60
                    total_p = sbw_price + yds[3]
                    output.append(total_d)
                    output.append(total_p)
                    output.append(sbwstep)
                    output.append(yds)
                    o_time = otime.strftime('%H:%M')
                    dtime = otime + datetime.timedelta(seconds=t_duration)
                    d_time = dtime.strftime('%H:%M')
                    output.insert(1, o_time)
                    output.insert(2, d_time)
                    outputs.append(output)
            outputs.sort(key=operator.itemgetter(0))
            if len(outputs) > 0:
                if len(outputs) < 6:
                    plans = outputs
                else:
                    plans = outputs[0:5]
                return True, self.yd_sbw_json_out_put(plans, 1)
            else:
                return False, 'time and codes limit'
        else:
            return False, 'route limit'

    def plan_sbw_trip(self,sbw_os, sbw_ds, otime):
        o_wt = int(sbw_os[0] * 1.5 / 60)
        d_wt = int(sbw_ds[0] * 1.5 / 60)
        sbw_o_name = self.sbwstation[sbw_os[1]].get_name()
        sbw_d_name = self.sbwstation[sbw_ds[1]].get_name()
        plantype, duration, price, plans = self.get_sbwplan(sbw_o_name, sbw_d_name)
        if plantype != False:
            plan = self.out_put_sbw_trip(otime, duration, price, plans, o_wt, d_wt)
            if plan == None:
                return False, 'time limit'
            joutput = self.sbw_sbw_json_out_put([plan])
            return True, joutput
        else:
            return False, 'route limit'

    def ydpart_json_out_put(self,plan):
        joutput = {}
        n = 0
        joutput['totalDuration'] = plan[0]
        joutput['departTime'] = plan[1]
        joutput['arriveTime'] = plan[2]
        joutput['totalPrice'] = plan[3]
        joutput['partStep'] = []
        for j in range(len(plan[4])):
            stepnum = j
            joutput['partStep'].append({})
            stepcode = plan[5][j]
            otime = datetime.datetime.strptime(stepcode[0], '%H:%M')
            dtime = datetime.datetime.strptime(stepcode[3], '%H:%M')
            duration = dtime - otime
            joutput['partStep'][stepnum]['stepNo'] = j + 1
            joutput['partStep'][stepnum]['duration'] = int(duration.total_seconds()) / 60
            joutput['partStep'][stepnum]['departTime'] = stepcode[0]
            joutput['partStep'][stepnum]['arriveTime'] = stepcode[3]
            joutput['partStep'][stepnum]['price'] = plan[6][j]
            step = plan[4][j]
            stepo = step[0]
            stepo_name, stepo_type = stepo[0].split(',', 1)
            stepo_id = self.ydstation[stepo[0]].get_id()
            joutput['partStep'][stepnum]['o_station'] = {}
            joutput['partStep'][stepnum]['o_station']['name'] = stepo_name
            joutput['partStep'][stepnum]['o_station']['type'] = stepo_type
            stepd = step[2]
            stepd_name, stepd_type = stepd[0].split(',', 1)
            stepd_id = self.ydstation[stepd[0]].get_id()
            joutput['partStep'][stepnum]['d_station'] = {}
            joutput['partStep'][stepnum]['d_station']['name'] = stepd_name
            joutput['partStep'][stepnum]['d_station']['type'] = stepd_type
            stepline = step[1]
            stepline_id, stepline_type = stepline[-1].split(',', 1)
            joutput['partStep'][stepnum]['route'] = {}
            joutput['partStep'][stepnum]['route']['id'] = stepline_id
            joutput['partStep'][stepnum]['route']['name'] = stepline[0]
            joutput['partStep'][stepnum]['route']['type'] = stepline_type
            joutput['partStep'][stepnum]['route']['code'] = stepcode[-1]
            joutput['partStep'][stepnum]['route']['vehicleNo'] = stepcode[-2]
            joutput['partStep'][stepnum]['route']['waitTime'] = stepcode[1]
            joutput['partStep'][stepnum]['route']['busArriveOStationTime'] = stepcode[2]
        return joutput

    def sbwpart_json_out_put(self,plan):
        joutput = {}
        joutput['totalDuration'] = plan[0]
        joutput['departTime'] = plan[1]
        joutput['arriveTime'] = plan[2]
        joutput['totalPrice'] = plan[3]
        joutput['partStep'] = []
        for j in range(len(plan[4])):
            stepnum = j
            joutput['partStep'].append({})
            step = plan[4][j]
            joutput['partStep'][stepnum]['stepNo'] = j + 1
            joutput['partStep'][stepnum]['o_station'] = {}
            joutput['partStep'][stepnum]['d_station'] = {}
            joutput['partStep'][stepnum]['o_station']['name'] = step[0]
            joutput['partStep'][stepnum]['d_station']['name'] = step[-1]
            joutput['partStep'][stepnum]['route'] = {}
            joutput['partStep'][stepnum]['route']['name'] = step[1]
            joutput['partStep'][stepnum]['route']['direction'] = step[2]
        return joutput

    def yd_yd_json_out_put(self,plans):
        joutput = []
        n = 0
        for plan in plans:
            i = n
            joutput.append({})
            n += 1
            joutput[i]['totalDuration'] = plan[0]
            joutput[i]['departTime'] = plan[1]
            joutput[i]['arriveTime'] = plan[2]
            joutput[i]['totalPrice'] = plan[3]
            joutput[i]['part'] = []
            joutput[i]['part'].append({'partNo': 1, 'partType': 'ydplan', 'partDetail': self.ydpart_json_out_put(plan)})
        return joutput

    def sbw_sbw_json_out_put(self,plans):
        joutput = []
        n = 0
        for plan in plans:
            i = n
            joutput.append({})
            n += 1
            joutput[i]['totalDuration'] = plan[0]
            joutput[i]['departTime'] = plan[1]
            joutput[i]['arriveTime'] = plan[2]
            joutput[i]['totalPrice'] = plan[3]
            joutput[i]['part'] = []
            joutput[i]['part'].append({'partNo': 1, 'partType': 'subwayplan', 'partDetail': self.sbwpart_json_out_put(plan)})
        return joutput

    def yd_sbw_json_out_put(self,plans, type):
        joutput = []
        n = 0
        for plan in plans:
            i = n
            joutput.append({})
            n += 1
            joutput[i]['totalDuration'] = plan[0]
            joutput[i]['departTime'] = plan[1]
            joutput[i]['arriveTime'] = plan[2]
            joutput[i]['totalPrice'] = plan[3]
            joutput[i]['part'] = []
            if type == 0:
                joutput[i]['part'].append(
                    {'partNo': type + 1, 'partType': 'ydplan', 'partDetail': self.ydpart_json_out_put(plan[type + 4])})
                joutput[i]['part'].append(
                    {'partNo': 2 - type, 'partType': 'subwayplan', 'partDetail': self.sbwpart_json_out_put(plan[5 - type])})
            else:
                joutput[i]['part'].append(
                    {'partNo': 2 - type, 'partType': 'subwayplan', 'partDetail': self.sbwpart_json_out_put(plan[5 - type])})
                joutput[i]['part'].append(
                    {'partNo': type + 1, 'partType': 'ydplan', 'partDetail': self.ydpart_json_out_put(plan[type + 4])})
        return joutput

    def sort_trips_by_time(self,tripsdict):
        all_trips = []
        output = []
        no_trip_reason = {}
        for triptype in tripsdict:
            [type, trips] = tripsdict[triptype]
            if type == True:
                for i in range(len(trips)):
                    duration = trips[i]['totalDuration']
                    all_trips.append([duration, triptype, trips[i]])
            else:
                no_trip_reason[triptype] = trips
        outputtype = set('')
        if len(all_trips) > 0:
            all_trips.sort(key=operator.itemgetter(0))
            if tripsdict['subwayPlan'][0] != False:
                maxtime = tripsdict['subwayPlan'][1][0]['totalDuration'] + 15
                for i in range(len(all_trips)):
                    if all_trips[i][0] <= maxtime:
                        output.append({})
                        output[i]['tripNo'] = i + 1
                        output[i]['tripType'] = all_trips[i][1]
                        outputtype.add(all_trips[i][1])
                        output[i]['tripDetails'] = all_trips[i][2]
                        if i < 3:
                            i += 1
                        else:
                            break
                    else:
                        break
            else:
                num = len(all_trips)
                if num > 3:
                    num = 3
                for i in range(num):
                    output.append({})
                    output[i]['tripNo'] = i + 1
                    output[i]['tripType'] = all_trips[i][1]
                    outputtype.add(all_trips[i][1])
                    output[i]['tripDetails'] = all_trips[i][2]
        else:
            output = None
        for triptype in tripsdict:
            [type, trips] = tripsdict[triptype]
            if type == True:
                if triptype not in outputtype:
                    no_trip_reason[triptype] = 'duration limit'
        result = {}
        result['no trip reason'] = no_trip_reason
        result['trip'] = output
        return result



    # 利用上述method，输入出发地目的地的经纬度，和出发时刻，获取出行方案
    # 输出优先级：驿动内部，驿动-地铁，地铁-驿动
    def plan_trip(self, o_lat, o_lng, d_lat, d_lng, o_time, membertype=0):
        otime = datetime.datetime.strptime(o_time, '%H:%M')
        os, ds = self.get_odstops(o_lat, o_lng, d_lat, d_lng, 800)
        sbw_os, sbw_ds = self.get_sbwstops(o_lat, o_lng, d_lat, d_lng, 1000)
        olatlng = [o_lat, o_lng]
        dlatlng = [d_lat, d_lng]
        trips = {}
        if os[1] != None and ds[1] != None and os[1] != ds[1]:
            result1, trip1 = self.plan_yd_yd_trip(os, ds, otime, olatlng, dlatlng, membertype)
            if result1 == True:
                trips['ydPlan'] = [True, trip1]
            else:
                trips['ydPlan'] = [False, trip1]
        elif os[1] == None and ds[1] != None:
            trip1 = 'o ydstation limit'
            trips['ydPlan'] = [False, trip1]
        elif os[1] != None and ds[1] == None:
            trip1 = 'd ydstation limit'
            trips['ydPlan'] = [False, trip1]
        elif os[1] == ds[1]:
            trip1 = 'od same nearest ydstation'
            trips['ydPlan'] = [False, trip1]
        else:
            trip1 = 'od ydstaiton limit'
            trips['ydPlan'] = [False, trip1]
        if (os[1] != None or ds[1] != None) and os[1] != ds[1]:
            if os[1] != None and sbw_ds[1] != None:
                result2, trip2 = self.plan_yd_sbw_trip(os, sbw_ds, otime, olatlng, dlatlng, membertype)
                if result2 == True:
                    trips['yd-subwayPlan'] = [True, trip2]
                else:
                    trips['yd-subwayPlan'] = [False, trip2]
            elif os[1] == None and sbw_ds[1] != None:
                trip2 = 'o ydstation limit'
                trips['yd-subwayPlan'] = [False, trip2]
            elif os[1] != None and sbw_ds[1] == None:
                trip2 = 'd subway station limit'
                trips['yd-subwayPlan'] = [False, trip2]
            else:
                trip2 = 'o ydstation and d subway station limit'
                trips['yd-subwayPlan'] = [False, trip2]
            if ds[1] != None and sbw_os[1] != None:
                result3, trip3 = self.plan_sbw_yd_trip(sbw_os, ds, otime, olatlng, dlatlng, membertype)
                if result3 == True:
                    trips['subway-ydPlan'] = [True, trip3]
                else:
                    trips['subway-ydPlan'] = [False, trip3]
            elif ds[1] == None and sbw_os[1] != None:
                trip3 = 'd ydstation limit'
                trips['subway-ydPlan'] = [False, trip3]
            elif ds[1] != None and sbw_os[1] == None:
                trip3 = 'o subway station limit'
                trips['subway-ydPlan'] = [False, trip3]
            else:
                trip3 = 'd ydstation and o subway station limit'
                trips['subway-ydPlan'] = [False, trip3]
        elif os[1] == ds[1]:
            trip2 = 'od same nearest ydstation'
            trips['yd-subwayPlan'] = [False, trip2]
            trip3 = 'od same nearest ydstation'
            trips['subway-ydPlan'] = [False, trip3]
        else:
            trip2 = 'o ydstaiton limit'
            trips['yd-subwayPlan'] = [False, trip2]
            trip3 = 'd ydstation limit'
            trips['subway-ydPlan'] = [False, trip3]
        if sbw_os[1] != None and sbw_ds[1] != None and sbw_os[1] != sbw_ds[1]:
            result4, trip4 = self.plan_sbw_trip(sbw_os, sbw_ds, otime)
            if result4 == True:
                trips['subwayPlan'] = [True, trip4]
            else:
                trips['subwayPlan'] = [False, trip4]
        if ('subwayPlan' not in trips) or ('subwayPlan' in trips and trips['subwayPlan'][1] == 'route limit'):
            sbw_os, sbw_ds = self.get_sbwstops(o_lat, o_lng, d_lat, d_lng, 2000)
            if sbw_os[1] != None and sbw_ds[1] != None and sbw_os[1] != sbw_ds[1]:
                result4, trip4 = self.plan_sbw_trip(sbw_os, sbw_ds, otime)
                if result4 == True:
                    trips['subwayPlan'] = [True, trip4]
                else:
                    trips['subwayPlan'] = [False, trip4]
            else:
                if 'subwayPlan' not in trips:
                    if sbw_os[1] == None and sbw_ds[1] != None:
                        trip4 = 'o subway station limit'
                        trips['subwayPlan'] = [False, trip4]
                    elif sbw_os[1] != None and sbw_ds[1] == None:
                        trip4 = 'd subway station limit'
                        trips['subwayPlan'] = [False, trip4]
                    elif sbw_os[1] == sbw_ds[1]:
                        trip4 = 'od same nearest subway station'
                        trips['subwayPlan'] = [False, trip4]
                    else:
                        trip4 = 'od subway staiton limit'
                        trips['subwayPlan'] = [False, trip4]
        return self.sort_trips_by_time(trips)

    def get_area(self,latitude, longitude, dis):
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
    def get_distance(self,lat1, lng1, lat2, lng2):
        lng1, lat1, lng2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])
        dlng = lng2 - lng1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371
        return c * r * 1000