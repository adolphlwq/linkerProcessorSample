# linkerProcessorSample Intro
[![Build Status](https://travis-ci.org/adolphlwq/linkerProcessorSample.svg?branch=master)](https://travis-ci.org/adolphlwq/linkerProcessorSample)

A sample code for processing infomation from Kafka and store to Cassandra using Apache Spark

## Tag introductions
1. `tag v0.1` realizations:
	2. collect info from kafka topic
	3. calculate cpu total usage as well as each cpu usage
	4. save cpu usage to cassandra
	5. test successfully on Mesos cluster with [Spark client mode](http://spark.apache.org/docs/latest/running-on-mesos.html#client-mode)

## Usage
### Prerequisite
First, you should set up zookeeper, cassandra and kafka broker. Then create kafka topic and cassandra keyspace

Second:

1. download [Apache Spark](spark.apache.org)
2. run [linkerConnector](https://github.com/LinkerNetworks/linkerConnector)
    - git clone https://github.com/LinkerNetworks/linkerConnector.git
    - install [Golang](https://golang.org/)
    - cd path/to/linkerConnector
    - `go build` and `go install`
3. git clone linkerProcessSample(https://github.com/adolphlwq/linkerProcessorSample.git)

### submit code to Spark 
#### submit python code to Spark with local mode
```
path/to/spark/bin/spark-submit \
    --packages org.apache.spark:spark-streaming-kafka_2.10:1.6.1  \
    path/to/linkerProcessorSample/spark2cassandra.py kafka_broker_servers kafka_topic
```
#### submit code to Spark on Mesos cluster
>Note: this method using Spark [client mode](http://spark.apache.org/docs/latest/running-on-mesos.html#client-mode) in Mesos cluster.

1. launch a Spark driver container in Mesos cluster
The container should have:
	- Spark.
	- libmesos.so(download mesos) refer to [client mode](http://spark.apache.org/docs/latest/running-on-mesos.html#client-mode).
	- your code and dependencies.
2. submit code to Mesos cluster
```language
SPARK_HOME/bin/submit \
--master mesos://host:port(10.140.0.14:5050) \
--packages org.apache.spark:spark-streaming-kafka_2.10:1.6.0 \
--executor-memory 2g --driver-memory 2g \
spark2cassandra.py zk(10.140.0.14:2181) topic(wlu_spark2cassandra)
```
This method is client mode,in which Spark framework and Spark driver run on the same machine(the machine which we submit code).

## Note:
1. suggest interval of Spark streaming **>** interval of linkerConnector

## Docker image
1. This [image Dcokerfile](https://github.com/adolphlwq/linkerProcessorSample/blob/master/docker/Dockerfile) is for running Spark exector on Mesos cluster.
2. If your code is written in Python and your Spark run on Mesos, you must solve the java dependencies.
3. I scan [Advanced Dependency Management](http://spark.apache.org/docs/latest/submitting-applications.html#advanced-dependency-management) section and try build the dependencies on Mesos Spark exector docker image.
the Maven central repo is https://mvnrepository.com/artifact/org.apache.spark/spark-streaming-kafka_2.10/1.6.0

## Reference
- [calculate cpu usage in Golang](https://sourcegraph.com/github.com/statsd/system/-/def/GoPackage/github.com/statsd/system/pkg/cpu/-/totals)
- [Linux Kernel about proc](http://www.mjmwired.net/kernel/Documentation/filesystems/proc.txt#1271)
- [Cassandra tutorial](http://www.tutorialspoint.com/cassandra/cassandra_alter_table.htm)
- [Cassandra data types](https://docs.datastax.com/en/cql/3.0/cql/cql_reference/cql_data_types_c.html)
- [Cassandra user user-defined-type](https://docs.datastax.com/en/cql/3.1/cql/cql_using/cqlUseUDT.html)

## TODOs
- [X] collect info from kafka
- [X] save processes info to cassandra
- [X] save machine info to cassandra
- [X] save kafka message to cassandra directly
- [X] overall cpu usage from linkerConnector (via Kafka)
    - [X] calculate cpu usage and save to cassandra
- [X] Mesos agent usage from linkerConnector (via Kafka)
- [ ] build Mesos Spark executor docker image for testing code on Mesos cluster
	- [X] [Mesos Spark executor beta2 Dockerfile](https://github.com/dockerq/docker-spark/blob/master/Dockerfile)
- [ ] research Spark streaming's "window" and improve code