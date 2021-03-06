from utils import *
from train_blocking import data_to_featureb
import signal
import time
import numpy as np
from keras.models import Sequential, load_model
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import SGD, Adam, RMSprop
from keras.utils import np_utils

def quit(signum, frame):
    print()
    print('%s|Stopping the thinking part...'%get_time())
    #tcpCliSock.close()
    sys.exit()


signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGTERM, quit)

print("%s|initialization..."%get_time())
conn = psycopg2.connect(host="localhost", dbname="ve450", user='root', password='1234') #database configuration
cursor = conn.cursor()
try:
    cursor.execute("CREATE TABLE CNCLinear_result (time varchar, mot_temp real, room_temp real, current real, displacement real, wave varchar, temp_high int, current_high int, is_cutblocking int, item_count int);")
except:
    print("Table CNCLinear_result exists, skipped\n")
conn.commit()
cursor.close()

last_wave="not working"
item_count = 0
last_timestamp = None
pool = []
tmp_data = []

flag = False
lst_wave = "not working"
print("%s|loading model..."%get_time())
model = load_model('brain.h5')
model1 = Sequential()
model1.add(Dense(64, input_dim=block_sample_num))
model1.add(Activation('tanh'))
model1.add(Dropout(0.2))
model1.add(Dense(64))
model1.add(Activation('tanh'))
model1.add(Dropout(0.2))
model1.add(Dense(nb_classes))
model1.add(Activation('sigmoid'))
#model1.compile(loss='binary_crossentropy', optimizer='rmsprop',metrics=['accuracy'])
model1.load_weights('block_weights.h5')
while True:
    if (last_timestamp == None):
        pool = read_from_db("ve450","root","1234","cnclinear","*","WHERE time >'%s'"%get_1minago())
        if (len(pool) == 0):
            #print(pool)
            print("%s|Database is empty... Wait for %.2f sec"%(get_time(),window_size))
            time.sleep(window_size)
            continue
        last_timestamp = pool[-1][key_to_idx("time")]
    else:
        tmp_data = read_from_db("ve450","root","1234","cnclinear","*","WHERE time>'%s'"%last_timestamp)
        if (len(tmp_data) == 0):
            #print("%s|No new data... Wait for %.2f sec"%(get_time(),wait_interval))
            time.sleep(wait_interval)
            continue
        data_point = tmp_data[-1]

        curr_time = data_point[0]
        mot_temp = data_point[1]
        room_temp = data_point[2]
        current = data_point[3]
        displacement = data_point[4]
        is_processing = data_point[5]


        #print(last_timestamp, data_point)
        last_timestamp = data_point[key_to_idx("time")]
        winner = -1;
        ifb = -1;
        if data_point[key_to_idx("processing")]:
            if pool_add(pool, data_point, window_size):
#enough length to predict
                flag = True
                #print("pool length is %d"%len(pool))
                X=[]
                X.append(data_to_feature(raw_data=pool, idx=key_to_idx("displacement"), sw=0))
                X=np.array(X)
                res = model.predict(X)
                winner = vec_to_idx(res, 0.99)
                X=[]
                X.append(data_to_feature(raw_data=pool, idx=key_to_idx("displacement"), sw=1))
                X=np.array(X)
                #res = model1.predict(X)
                #ifb = vec_to_idx(res, 0)
                ifb = 1 if (X[0,0]>=3 and X[0,1]>=0.3 and X[0,1]<=13) or (X[0,0]>3 and X[0,1]>1) else 0
                print(X)
                if ifb == 1:
                    print("%s|Blocking..."%get_time())
                else:
                    if winner != -1:
                        print("%s|It Should be %s"%(get_time(),idx_to_type(winner)))
                        lst_wave = idx_to_type(winner)
            else:
                X=[]
                X.append(data_to_feature(raw_data=pool, idx=key_to_idx("displacement"), sw=1))
                X=np.array(X)
                #res = model1.predict(X)
                #ifb = vec_to_idx(res, 0)
                ifb = 1 if (X[0,0]>=3 and X[0,1]>=0.3 and X[0,1]<=13) or (X[0,0]>3 and X[0,1]>1) else 0
                print(X)
                if ifb == 1:
                    print("%s|Blocking..."%get_time())
                else:
                    if (not flag):
                        #print("%s|Too less information!!"%get_time())
                        a = 1
                    else:
                        continue
#too less info
        else:
            #if (len(pool)!=0):
                #print("%s|Not working..."%get_time())
            pool=[]
            tmp_data=[]
            if flag:
                item_count += 1
                #print("%s|Current item is finished"%get_time())
            flag = False
            lst_wave = "unknown"
        if(is_processing == 0):
            wave = "not working"
            lst_wave = wave
        else:
            wave = idx_to_type(winner)
            if (wave != "unknown"):
                last_wave = wave
        if(wave == "unknown"):
            wave = last_wave


        if(temp_alarm(room_temp,mot_temp)==True):
            temp_high = 1
        else:
            temp_high = 0
        if(current_alarm(current)==True):
            current_high = 1
        else:
            current_high = 0
        is_cutblocking=ifb
        if(wave == "unknown"):
            wave = lst_wave
        write_data=(curr_time, mot_temp,room_temp,current,displacement,wave,temp_high,current_high,is_cutblocking,item_count)
        write_db(write_data)

