from util_v_0_6.func import plan_trip
import requests
from util_v_0_6.yidong_algo import YidongAlgo

# url = 'http://115.28.153.0/plan_trip?o_lat={}&o_lng={}&d_lat={}&d_lng={}&otime={}&membertype={}'
url = 'http://localhost:8000/plan_trip?o_lat={}&o_lng={}&d_lat={}&d_lng={}&otime={}&membertype={}'


def test_method():

    yd = YidongAlgo()
    # o-柏林映象周边，d-安亭新镇周边
    # 驿动内直达换乘
    o_lat=31.2712
    o_lng=121.178615
    d_lat=31.277159
    d_lng=121.175772
    o_time='07:10'
    membertype=0

    print(yd.plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-安亭新镇周边，d-中山公园周边
    # # 驿动内直达
    o_lat=31.277159
    o_lng=121.175772
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:30'
    membertype=1
    print(yd.plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-柏林映象周边，d-中山公园周边
    # # 驿动内一次换乘
    o_lat=31.2712
    o_lng=121.178615
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:10'
    membertype=2
    print(yd.plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-同济大学周边，d-中山公园周边
    # # 驿动换乘地铁
    o_lat=31.29188
    o_lng=121.22063
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:20'
    membertype=2

    print(yd.plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-中山公园周边，d-安亭新镇周边
    # # 地铁换乘驿动，该类方案的总时长合理性需要利用 百度api 获取到公交出行的时间进行判断，如果长于两地直接公交，那么方案需剔除
    o_lat=31.22415
    o_lng=121.424639
    d_lat=31.277159
    d_lng=121.175772
    o_time='16:50'

    print(yd.plan_trip(o_lat,o_lng,d_lat,d_lng,o_time))


def test_func():


    # o-柏林映象周边，d-安亭新镇周边
    # 驿动内直达换乘
    o_lat=31.2712
    o_lng=121.178615
    d_lat=31.277159
    d_lng=121.175772
    o_time='07:10'
    membertype=0
    print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-安亭新镇周边，d-中山公园周边
    # # 驿动内直达
    o_lat=31.277159
    o_lng=121.175772
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:30'
    membertype=1
    print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-柏林映象周边，d-中山公园周边
    # # 驿动内一次换乘
    o_lat=31.2712
    o_lng=121.178615
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:10'
    membertype=2
    print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-同济大学周边，d-中山公园周边
    # # 驿动换乘地铁
    o_lat=31.29188
    o_lng=121.22063
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:20'
    membertype=2

    print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))

    # # o-中山公园周边，d-安亭新镇周边
    # # 地铁换乘驿动，该类方案的总时长合理性需要利用 百度api 获取到公交出行的时间进行判断，如果长于两地直接公交，那么方案需剔除
    o_lat=31.22415
    o_lng=121.424639
    d_lat=31.277159
    d_lng=121.175772
    o_time='16:50'

    print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time))

def test_api():
    o_lat = 31.2712
    o_lng = 121.178615
    d_lat = 31.277159
    d_lng = 121.175772
    o_time = '07:10'
    membertype = 0
    url1 = url.format(o_lat,o_lng,d_lat,d_lng,o_time,membertype)
    print(url1)
    resp = requests.get(url1)
    print(resp.text)


    # # o-安亭新镇周边，d-中山公园周边
    # # 驿动内直达
    o_lat = 31.277159
    o_lng = 121.175772
    d_lat = 31.22415
    d_lng = 121.424639
    o_time = '07:30'
    membertype = 1
    url2 = url.format(o_lat, o_lng, d_lat, d_lng, o_time, membertype)
    print(url2)
    resp = requests.get(url2)
    print(resp.text)


    # # o-柏林映象周边，d-中山公园周边
    # # 驿动内一次换乘
    o_lat = 31.2712
    o_lng = 121.178615
    d_lat = 31.22415
    d_lng = 121.424639
    o_time = '07:10'
    membertype = 2
    url3 = url.format(o_lat, o_lng, d_lat, d_lng, o_time, membertype)
    print(url3)
    resp = requests.get(url3)
    print(resp.text)

    # # o-同济大学周边，d-中山公园周边
    # # 驿动换乘地铁
    o_lat = 31.29188
    o_lng = 121.22063
    d_lat = 31.22415
    d_lng = 121.424639
    o_time = '07:20'
    membertype = 2
    url4 = url.format(o_lat, o_lng, d_lat, d_lng, o_time, membertype)
    print(url4)
    resp = requests.get(url4)
    print(resp.text)


    # # o-中山公园周边，d-安亭新镇周边
    # # 地铁换乘驿动，该类方案的总时长合理性需要利用 百度api 获取到公交出行的时间进行判断，如果长于两地直接公交，那么方案需剔除
    o_lat = 31.22415
    o_lng = 121.424639
    d_lat = 31.277159
    d_lng = 121.175772
    o_time = '16:50'
    url5 = url.format(o_lat, o_lng, d_lat, d_lng, o_time, membertype)
    print(url5)
    resp = requests.get(url5)
    print(resp.text)

if __name__ == '__main__':
    test_api()