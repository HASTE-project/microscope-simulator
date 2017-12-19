import time
import cv2
import numpy as np
from PIL import Image

from kafka import KafkaConsumer
import sys
from myvariables import kafka_server

# file1 = open("consumer1_res.txt", "a")
# file2

def python_kafka_consumer_performance(consumer_number):
    file = open("consmer_res" + str(consumer_number) + ".txt", "a")
    topic = 'test5part'
    msg_count = 0
    print("in multip!")
    file.write("\n{}".format(time.perf_counter()))
    #file.write(str(time.perf_counter()))
    consumer = KafkaConsumer(group_id='my-group',
                             auto_offset_reset='earliest',
                             bootstrap_servers=[kafka_server + ":9092"],
                             consumer_timeout_ms=20000)

    msg_consumed_count = 0
    print("msg_count: {}".format(msg_count))
    consumer.subscribe([topic])
    consumer_start = time.perf_counter()

    for message in consumer:
       # print("{}, msg nb: {}".format(consumer_number, msg_consumed_count))
        msg_consumed_count += 1
        file.write("\n{}".format(time.perf_counter()))
        # img = cv2.imdecode(np.frombuffer(message.value, dtype=np.uint16), -1)
        # fin2 = Image.fromarray(img)
        # if msg_consumed_count >= msg_count:
        #     break

    consumer_timing = time.perf_counter() - consumer_start - 2 # consumer waits 2 sec before closing if there are no new
    # messages

    print("{} consumer_time: {} msg_count: {}".format(consumer_number, consumer_timing, msg_consumed_count))
    consumer.close()
    return "done!"
