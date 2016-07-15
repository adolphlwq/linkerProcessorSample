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
    ./bin/spark-submit \
    --packages org.apache.spark:spark-streaming-kafka_2.10:SPARK_VERSION(like 1.6.0) \
    --executor-memory 2g \
    --driver-memory 2g \
    path/to/spark2cassandra.py \
    <zk endpoint> <kafka topic>

    ### submit to mesos cluster using spark submit script
    SPARK_HOME/bin/spark-submit \
    --master mesos://host:port \
    --packages org.apache.spark:spark-streaming-kafka_2.10:SPARK_VERSION(like 1.6.0) \
    --executor-memory 3g
    spark2cassandra.py <zk endpoint> <kafka topic>

    ### submit on docs by dcos-spark cli
    dcos spark run --submit-args='--packages org.apache.spark:spark-streaming-kafka_2.10:SPARK_VERSION(like 1.6.0) \
        spark2cassandra.py 10.140.0.14:2181 wlu_spark2cassandra' \
        --docker-image=adolphlwq/mesos-for-spark-exector-image:1.6.0.beta

    ### error
    "blockmanager block input replicated to only 0 peer(s) instead of 1 peers"
    or "16/07/04 13:51:05 WARN BlockManager: Block input-0-1467611464800 \
        replicated to only 0 peer(s) instead of 1 peers"
    http://stackoverflow.com/questions/32583273/spark-streaming-get-warn-replicated-to-only-0-peers-instead-of-1-peers
"""

from __future__ import print_function
import sys
import logging
import ConfigParser
import json
import time

from pyspark import SparkContext
from pyspark import SparkConf
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
        self.ip = ['10.140.0.16','10.140.0.17','10.140.0.18']
        self.port = '9042'
        self.keyspace = 'iotinfo_tmp'
        self.cluster = Cluster(contact_points=self.ip, port=self.port)
        self.session = self.cluster.connect(self.keyspace)
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
    def save_cpu_usage(self, data):
        '''
        :param data:list of cpu usage:[{},{},...,{}]
        :return:
        '''
        if len(data) == 0:
            print('no data from spark streaming')
            return
        ret_data = cal_cpu_usage(data)
        if ret_data is None or len(ret_data) == 0:
            return
        q = self.session.prepare("INSERT INTO etldata(timestamp, cpu_all, cpus) values (?, ?, ?)")
        for ret in ret_data:
            self.session.execute(q, (ret['timestamp'], ret['cpu_all'], json.dumps(ret['cpus'])))
            print('insert info {0}'.format(ret))

def cal_cpu_usage(l):
    '''
    :param l: [{'timestamp':timestamp, 'cpus':[{idle, total, id},...]},{},...,{}], 'cpu_all':{idle, total}},...,{}]
    :return:
    '''
    if len(l) < 2:
        return
    usage = []
    core_nums = len(l[0]['cpus'])
    for i in range(len(l)-1):
        each_ret = []
        c0 = l[i]['cpus']
        c1 = l[i+1]['cpus']
        cpu_all_usage = (l[i+1]['cpu_all']['idle']-l[i]['cpu_all']['idle'])/float(l[i+1]['cpu_all']['total']-l[i]['cpu_all']['total'])*100
        for j in range(core_nums):
            ret = (c1[j]['idle']-c0[j]['idle'])/float(c1[j]['total']-c0[j]['total'])*100
            each_ret.append({'id':c0[j]['id'], 'usage':ret})
        usage.append({'timestamp':l[i]['timestamp'], 'cpu_all':cpu_all_usage, 'cpus':each_ret})
    return usage

def format_cpu_stat(p):
    if p is None or p == '':
        return
    #calc tot cpu usage
    cpu_all = p['stat']['cpu_all']
    tot_idle = cpu_all['idle'] + cpu_all['iowait']
    del cpu_all['id']
    tot_tot = sum(cpu_all.values())
    ret = []
    cpus = p['stat']['cpus']
    core_nums = len(cpus)
    # calc each cpu's idle and total
    for cpu in cpus:
        id = cpu['id']
        del cpu['id']
        tmp = {'id': id, 'idle': cpu['idle'] + cpu['iowait'], 'total': sum(cpu.values())}
        ret.append(tmp)
    return {'timestamp':p['timestamp'], 'cpu_all':{'idle':tot_idle, 'total': tot_tot}, 'cpus':ret}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: spark2cassandra.py <zk> <topic>", file=sys.stderr)
        exit(-1)

    cassandraUtil = cassandraUtil()
    conf = SparkConf()\
            .setAppName('spark2cassandra')\
            .set('spark.mesos.executor.docker.image','adolphlwq/mesos-for-spark-exector-image:1.6.0.beta2')\
            .set('spark.mesos.executor.home','/usr/local/spark-1.6.0-bin-hadoop2.6')\
	        .set('spark.mesos.coarse','true')
    sc = SparkContext(conf = conf)
    ssc = StreamingContext(sc, 5)

    zkQuorum, topic = sys.argv[1:]
    kafkaStream = KafkaUtils.createStream(ssc, zkQuorum, 'group-spark2cassandra', {topic: 1})
    machineStream = kafkaStream.filter(lambda line: 'MachineInfo' in line).map(lambda line: line[1])
    # compute cpu overall usage
    processStream = kafkaStream.filter(lambda line: 'ProcessInfo' in line).map(lambda line: line[1])
    formatUsageStream = processStream\
                    .map(lambda info: format_cpu_stat(json.loads(info.decode('utf-8'))))
    # formatUsageStream.pprint()
    formatUsageStream.foreachRDD(lambda t, rdd: cassandraUtil.save_cpu_usage(rdd.collect()))
    ssc.start()
    ssc.awaitTermination()
    cassandraUtil.close_session()
