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
    <cassandra_host> <cassandra_port> <cassandra_keyspace> <zk endpoint> <kafka topic>

    ### submit to mesos cluster using spark submit script
    SPARK_HOME/bin/spark-submit \
    --master mesos://host:port \
    --packages org.apache.spark:spark-streaming-kafka_2.10:SPARK_VERSION(like 1.6.0) \
    --executor-memory 3g
    spark2cassandra.py \
    <cassandra_host> <cassandra_port> <cassandra_keyspace> <zk endpoint> <kafka topic>

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
import json
import time
import uuid
import getopt

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from cassandra.cluster import Cluster

class cassandraUtil(object):
    def __init__(self, host=['localhost'], port='9042', ks='dap'):
        self.ip = host
        self.port = port
        self.keyspace = ks
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
        :param data:list of cpu usage:[(K1,[Vi...]),(K2,[Vi...]),...,(Kn,[Vi...])]
        :return:
        '''
        if len(data) < 1:
            return
        q = self.session.prepare("INSERT INTO cpu_usage(uuid, cpu_usage, machine_id, ts) values (?, ?, ?, ?)")
        for ele in data:
            v = ele[1]
            if v is None or v == '':
                return
            for ret in v:
                self.session.execute(q, (uuid.uuid1(), ret['cpu_usage'], ret['machine_id'], ret['ts']))
        '''
        print(data)
        if data is None or data == '':
            print('no data from spark streaming')
            return
        ret_data = cal_cpu_usage(data)
        print (ret_data)
        if ret_data is None or ret_data == '':
            return
        q = self.session.prepare("INSERT INTO cpu_usage(uuid, cpu_usage, machine_id, ts) values (?, ?, ?, ?)")
        for ret in ret_data:
            self.session.execute(q, (uuid.uuid1(), ret['cpu_usage'], ret['machine_id'], ret['ts']))
        '''

def cal_cpu_usage(tmp):
    """
        :param: [data1,data2,...,datan]
                datan = {'machine_id':machine_id, 'cpus':{'idle':cpus['idle'],'tot':tot},'ts':ts}
        :return:[ret1,ret2,...,retn]
                ret = {machine_id, cpus,ts}
        """
    data_ = list(tmp)
    if len(data_) < 2:
        return
    data = sorted(data_, key=lambda x:x['ts'])
    l = len(data)
    ret = []
    for i in range(l - 1):
        cpu0, cpu1 = data[i], data[i + 1]
        if (cpu1['cpus']['tot'] - cpu0['cpus']['tot']) == 0:
            continue
        else:
            percent = (cpu1['cpus']['idle'] - cpu0['cpus']['idle']) / float(cpu1['cpus']['tot'] - cpu0['cpus']['tot']) * 100
        tmp = {'machine_id': cpu0['machine_id'], 'cpu_usage': percent, 'ts': cpu0['ts']}
        ret.append(tmp)
    return ret

def tmp_cal(data):
    """
    :param: data:list of cpu usage:[(K1,[Vi...]),(K2,[Vi...]),...,(Kn,[Vi...])]
            Vi = {'machine_id':machine_id, 'cpus':{'idle':cpus['idle'],'tot':tot},'ts':ts}
    :return:
    """
    if len(data) == 0:
        return
    ret = []
    for v in data:
        l = len(data[1])
        if l < 2:
            return
        for i in range(l-1):
            cpu0,cpu1 = v[i],v[i+1]
            print(cpu0)
            percent = (cpu1['cpus']['idle'] - cpu0['cpus']['idle']) / float(
                cpu1['cpus']['tot'] - cpu0['cpus']['tot']) * 100
            tmp = {'machine_id': cpu0['machine_id'], 'cpu_usage': percent, 'ts': cpu0['ts']}
            ret.append(tmp)
    # return ret

def format_cpu_stat(info):
    """
    :param info:original data source
    :return:new:python tuple (machine_id, dict)
            old:python dict
            dict={'machine_id':v,'cpus':v,'tot':v,'ts':v}
    """
    if info is None or info == '':
        return
    cpus = info['stat']['cpu_all']
    machine_id = info['machine_id']
    ts = info['timestamp']
    cpus_ = cpus
    del cpus_['id']
    tot = sum(cpus.values())
    ret = {'machine_id':machine_id, 'cpus':\
            {'idle':cpus['idle'],'tot':tot},\
            'ts':ts}
    return (machine_id,ret)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("""Usage: spark2cassandra.py <cassandra_host>
                                           <cassandra_port>
                                           <cassandra_keyspace>
                                           <zk>
                                           <topic>.
                 Example: path/to/spark2cassandra.py
                                            192.168.10.11,192.168.10.12
                                            9042
                                            dap
                                            localhost:2181
                                            topic""", file=sys.stderr)
        exit(-1)
    host,port,ks,zkQuorum,topic = sys.argv[1:]
    # cassandraUtil = cassandraUtil(host=host.split(','), port=port, ks=ks)
    cassandraUtil = cassandraUtil(host=['localhost'], port=port, ks=ks)

    conf = SparkConf()
    # conf for Spark standalone mode
    conf.setAppName('spark2cassandra').setMaster("local[2]")
    # conf for Mesos cluster
    # conf.setAppName('spark2cassandra')\
    #     .set('spark.mesos.executor.docker.image','adolphlwq/mesos-for-spark-exector-image:1.6.0.beta2')\
    #     .set('spark.mesos.executor.home','/usr/local/spark-1.6.0-bin-hadoop2.6')\
	 #    .set('spark.mesos.coarse','true')
    sc = SparkContext(conf = conf)
    ssc = StreamingContext(sc, 5)
    kafkaStream = KafkaUtils.createStream(ssc, zkQuorum, 'group-spark2cassandra', {topic: 1})
    # machineStream = kafkaStream.filter(lambda line: 'MachineInfo' in line).map(lambda line: line[1])
    # compute cpu overall usage
    processStream = kafkaStream.filter(lambda line: 'ProcessInfo' in line).map(lambda line: line[1])
    formatUsageStream = processStream\
                    .map(lambda info: format_cpu_stat(json.loads(info.decode('utf-8'))))
    keyValueCpuStream = formatUsageStream.groupByKey().mapValues(cal_cpu_usage)
    keyValueCpuStream.foreachRDD(lambda t, rdd: cassandraUtil.save_cpu_usage(rdd.collect()))
    ssc.start()
    ssc.awaitTermination()
    cassandraUtil.close_session()
