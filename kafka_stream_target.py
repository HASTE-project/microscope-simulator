"""Module to connect to Kafka server and send messages to Kafka producer."""

import time
from stream_target import StreamTarget
from kafka import KafkaProducer, KafkaClient, SimpleProducer
from kafka.common import LeaderNotAvailableError

from myvariables import kafka_server, topic, max_msg_size


class KafkaStreamTarget(StreamTarget):

    def __init__(self):
        # kafka = KafkaClient("129.16.125.231:9092")
        # Review: this address should be passed in the ctor
        self.producer = KafkaProducer(bootstrap_servers=[kafka_server + ":9092"], max_request_size=max_msg_size)
        self.topic = topic
        print(type(self.producer))
        # return [topic, producer]

    def old_connect(self, message):
        kafka = KafkaClient(kafka_server + ":9092")
        self.producer = SimpleProducer(kafka)
        self.topic = topic

        try:
            self.producer.send_messages(self.topic, message)
        except LeaderNotAvailableError:
            # https://github.com/mumrah/kafka-python/issues/249
            time.sleep(1)
            KafkaStreamTarget.print_response(self.producer.send_messages(self.topic, message))

        kafka.close()

    def send_message(self, image_bytes, file_name, metadata):
        """
        :param image_bytes: bytearray for image.
        :param file_name: original file name of image.
        :param metadata: extra information (timestamp, spatial information, unique stream ID, etc.)
        :return:
        """
        # kafka = KafkaClient("130.239.81.54:9092")
        # self.producer = SimpleProducer(kafka)
        # self.topic = 'test'
        # self.producer = KafkaProducer(bootstrap_servers=["130.239.81.54:9092"])
        # self.producer = KafkaProducer(bootstrap_servers=["130.239.81.54:9092"])
        print("in send_msg!")
        print("prod: {} topic: {}".format(self.producer, self.topic))

        try:
            self.producer.send(self.topic, key=str.encode(file_name), value=image_bytes)
            #  self.producer.send(self.topic, key=file_name, value=message)
            print("msg sent!")
        except LeaderNotAvailableError:
            print("in except :(")
            # https://github.com/mumrah/kafka-python/issues/249
            time.sleep(1)
            # ReviewL don't copy paste here - use a loop instead for max retries
            KafkaStreamTarget.print_response(self.producer.send(self.topic, key=file_name, value=image_bytes))

        #  kafka.close()

    @staticmethod
    def print_response(response=None):
        if response:
            print('Error: {0}'.format(response[0].error))
            print('Offset: {0}'.format(response[0].offset))
