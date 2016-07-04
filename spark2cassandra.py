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

    ### error
    "blockmanager block input replicated to only 0 peer(s) instead of 1 peers"
    or "16/07/04 13:51:05 WARN BlockManager: Block input-0-1467611464800 \
        replicated to only 0 peer(s) instead of 1 peers"
    http://stackoverflow.com/questions/32583273/spark-streaming-get-warn-replicated-to-only-0-peers-instead-of-1-peers
"""

from __future__ import print_function
import sys
import ConfigParser
import json
import time

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

from cassandra.cluster import Cluster

class cassandraUtil(object):
    # props = get_config('config.txt')
    def __init__(self):
        self.ip = ['127.0.0.1']
        self.port = '9042'
        self.keyspace = 'iotinfo_tmp'
        self.cluster = Cluster(contact_points=self.ip, port=self.port)
        self.session = self.cluster.connect(self.keyspace)
    def set_new_keyspace(self, new_keyspace):
        self.session.set_keyspace(new_keyspace)
    def close_session(self):
        self.session.shutdown()
    def save_machineinfo_json(self, t, machineinfo):
        if len(machineinfo) == 0:
            return
        for info in machineinfo:
            now = time.time()
            q = self.session.prepare('INSERT INTO machineinfo(timestamp, content) values (?, ?)')
            self.session.execute(q, (int(now), info))
    def save_processinfo_json(self, t, processinfo):
        if len(processinfo) == 0:
            return
        for info in processinfo:
            now = time.time()
            q = self.session.prepare('INSERT INTO processinfo(timestamp, content) values (?, ?)')
            self.session.execute(q, (int(now), info))

def testRdd(rdd):
    for i in rdd.collect():
        print(i)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: spark2cassandra.py <zk> <topic>", file=sys.stderr)
        exit(-1)

    cassandraUtil = cassandraUtil()
    sc = SparkContext('local[*]', 'spark2cassandra')
    ssc = StreamingContext(sc, 5)

    zkQuorum, topic = sys.argv[1:]
    kafkaStream = KafkaUtils.createStream(ssc, zkQuorum, 'group-spark2cassandra', {topic: 1})
    machineStream = kafkaStream.filter(lambda line: 'MachineInfo' in line).map(lambda line: line[1])
    processStream = kafkaStream.filter(lambda line: 'ProcessInfo' in line).map(lambda line: line[1])
    machineStream.foreachRDD(lambda t, rdd: cassandraUtil.save_machineinfo_json(t, rdd.collect()))
    processStream.foreachRDD(lambda t, rdd: cassandraUtil.save_processinfo_json(t, rdd.collect()))
    # machineStream.pprint()
    ssc.start()
    ssc.awaitTermination()
    cassandraUtil.close_session()
