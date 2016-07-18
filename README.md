# linkerProcessorSample Intro
[![Build Status](https://travis-ci.org/adolphlwq/linkerProcessorSample.svg?branch=master)](https://travis-ci.org/adolphlwq/linkerProcessorSample)

A sample code for processing infomation from Kafka and store to Cassandra using Apache Spark

## Tag introductions
###tag v0.1
realizations:
2. collect info from kafka topic
3. calculate cpu total usage as well as each cpu usage
4. save cpu usage to cassandra
5. test successfully on Mesos cluster with [Spark client mode](http://spark.apache.org/docs/latest/running-on-mesos.html#client-mode)

###tag v0.2
1. the same as v0.1
2. calculate cpu_all usage

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
    - linkerConnector -i 1000 -d kafka -t <kafka topic> -s <kafka server>
3. git clone linkerProcessSample(https://github.com/adolphlwq/linkerProcessorSample.git)

### submit code to Spark 
Please refer [Here for detail](https://github.com/adolphlwq/linkerProcessorSample/blob/master/DEPLOY.md)

## Reference
- [Apache Spark Advanced Dependency Management](http://spark.apache.org/docs/latest/submitting-applications.html#advanced-dependency-management)
- [Maven central repo](https://mvnrepository.com/artifact/org.apache.spark/spark-streaming-kafka_2.10/1.6.0)
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
    - [X] calculate cpu usage from multi machine
- [X] Mesos agent usage from linkerConnector (via Kafka)
- [X] build Mesos Spark executor docker image for testing code on Mesos cluster
	- [X] [Mesos Spark executor beta2 Dockerfile](https://github.com/dockerq/docker-spark/blob/master/Dockerfile)
- [ ] research Spark streaming's "window" and improve code