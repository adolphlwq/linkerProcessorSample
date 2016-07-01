# -*- coding: utf-8 -*-
"""
    ## spark2cassandra:
    1. recieve info from kafka
    2. convert the info to needed format
    3. store info to cassandra
    4. use Spark Streaming1.6.0 Python API and kafka-python1.2.2 library
    ## usage
    ### srtart linkerConnector
    linkerConnector -i 5000 -d kafka -t topic-spark2cassandra -s localhost:9092
    ### submit py files
    ./bin/spark-submit --packages org.apache.spark:spark-streaming-kafka_2.10:1.6.1  \
    /publicdata/workspace/PycharmProjects/spark2cassandra/spark2cassandra.py \
    localhost:2181 topic-spark2cassandra
"""

from __future__ import print_function
import sys
import ConfigParser

from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils

# load config
def get_config(filename):
    with open(filename,'r') as f:
        cfg = ConfigParser.ConfigParser()
        cfg.readfp(f)
        secs = cfg.sections()
        props = cfg.items(secs[0])
    return dict(props)

# props = get_config('config.txt')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: spark2cassandra.py <zk> <topic>", file=sys.stderr)
        exit(-1)

    sc = SparkContext('local[2]', 'spark2cassandra')
    ssc = StreamingContext(sc, 5)

    zkQuorum, topic = sys.argv[1:]
    kafkaStream = KafkaUtils.createStream(ssc, zkQuorum, 'group-spark2cassandra', {topic: 1})
    machineInfo = kafkaStream.filter()
    kafkaStream.pprint()
    ssc.start()
    ssc.awaitTermination()

from cassandra.cluster import Cluster

class cassandraUtil(object):
    props = get_config('config.txt')
    def __init__(self, props):
        self.ip = props['cassandea_ip']
        self.port = props['cassandea_port']
        self.keyspace = props['cassandra_keyspace']
        self.cluster = Cluster(contact_points=self.ip, port=self.port)
        self.session = self.cluster.connect(self.keyspace)
    def set_new_keyspace(self, new_keyspace):
        self.session.set_keyspace(new_keyspace)
    def close_session(self):
        self.session.shutdown()