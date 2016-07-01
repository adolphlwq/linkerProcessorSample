# linkerProcessorSample Intro
A sample code for processing info from kafka and store to cassandra using Apache Spark

## Usage
First, you should set up zookeeper, cassandra and kafka broker
Second:
1. download [Apache Spark](spark.apache.org)
2. git clone https://github.com/adolphlwq/linkerProcessorSample.git
3. submit python code to spark(local mode):
```
path/to/spark//bin/spark-submit \
    --packages org.apache.spark:spark-streaming-kafka_2.10:1.6.1  \
    spark2cassandra.py kafka_broker_servers kafka_topic
```
## TODOs
[x] collect info from kafka
[] processing info
[] store info
