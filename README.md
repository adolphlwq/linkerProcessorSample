# linkerProcessorSample Intro
A sample code for processing infomation from Kafka and store to Cassandra using Apache Spark

## Usage
### prerequisite
First, you should set up zookeeper, cassandra and kafka broker. Then create kafka topic and cassandra keyspace

Second:

1. download [Apache Spark](spark.apache.org)
2. run [linkerConnector](https://github.com/LinkerNetworks/linkerConnector)
    - git clone https://github.com/LinkerNetworks/linkerConnector.git
    - install [Golang](https://golang.org/)
    - cd path/to/linkerConnector
    - `go build` and `go install`
3. git clone linkerProcessSample(https://github.com/adolphlwq/linkerProcessorSample.git)
3. submit python code to spark(**local mode**):
```
path/to/spark/bin/spark-submit \
    --packages org.apache.spark:spark-streaming-kafka_2.10:1.6.1  \
    path/to/linkerProcessorSample/spark2cassandra.py kafka_broker_servers kafka_topic
```

## TODOs
- [X] collect info from kafka
- [X] save processes info to cassandra
- [X] save machine info to cassandra
- [X] save kafka message to cassandra directly