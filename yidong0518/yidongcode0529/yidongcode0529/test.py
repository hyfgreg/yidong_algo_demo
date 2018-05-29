from util_v_0_5.func import plan_trip


if __name__ == '__main__':
    # o-柏林映象周边，d-安亭新镇周边
    # 驿动内直达换乘
    o_lat=31.2712
    o_lng=121.178615
    d_lat=31.277159
    d_lng=121.175772
    o_time='07:10'
    membertype=0
    # print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))
    #
    #
    # # In[52]:
    #
    #
    # # o-安亭新镇周边，d-中山公园周边
    # # 驿动内直达
    o_lat=31.277159
    o_lng=121.175772
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:30'
    membertype=1
    # print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))
    #
    #
    # # In[53]:
    #
    #
    # # o-柏林映象周边，d-中山公园周边
    # # 驿动内一次换乘
    o_lat=31.2712
    o_lng=121.178615
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:10'
    membertype=2
    # print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))
    #
    #
    # # In[54]:
    #
    #
    # # o-同济大学周边，d-中山公园周边
    # # 驿动换乘地铁
    o_lat=31.29188
    o_lng=121.22063
    d_lat=31.22415
    d_lng=121.424639
    o_time='07:20'
    membertype=2
    # print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time,membertype))
    #
    #
    # # In[55]:
    #
    #
    # # o-中山公园周边，d-安亭新镇周边
    # # 地铁换乘驿动，该类方案的总时长合理性需要利用 百度api 获取到公交出行的时间进行判断，如果长于两地直接公交，那么方案需剔除
    o_lat=31.22415
    o_lng=121.424639
    d_lat=31.277159
    d_lng=121.175772
    o_time='16:40'
    print(plan_trip(o_lat,o_lng,d_lat,d_lng,o_time))