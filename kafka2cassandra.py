from kafka import KafkaConsumer
import ConfigParser
from cassandra.cluster import Cluster

class cassandraUtil(object):
    # props = get_config('config.txt')
    def __init__(self):
        self.ip = ['127.0.0.1']
        self.port = '9042'
        self.keyspace = 'iotinfo_kafka_tmp'
        self.cluster = Cluster(contact_points=self.ip, port=self.port)
        self.session = self.cluster.connect(self.keyspace)
    def close_session(self):
        self.session.shutdown()
    def save_kafka(self, msg):
        if not msg:
            return
        q = self.session.prepare('insert into kafkamsg (topic, partition, offset, key, value) \
                                    values (?, ?, ?, ?, ?)')
        self.session.execute(q, (msg.topic, msg.partition, msg.offset, msg.key, msg.value))



if __name__ == '__main__':
    consumer = KafkaConsumer('topic-spark2cassandra',
                             'group-spark2cassandra',
                             bootstrap_servers=['localhost:9092'])
    cassandraUtil = cassandraUtil()
    for msg in consumer:
        cassandraUtil.save_kafka(msg)