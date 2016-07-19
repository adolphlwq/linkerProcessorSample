# Introduce Deploying python code to Spark cluster

## Run Spark on your local machine
### Prerequisite
1. run zookeeper
2. run kafka
3. run cassandra

I suggest you use [Docker](https://www.docker.com/) to run above softwares

### Submit code
1. git clone https://github.com/adolphlwq/linkerProcessorSample.git
2. submit code
The script is below:
```shell
path/to/spark/bin/spark-submit \
    --packages org.apache.spark:spark-streaming-kafka_2.10:SPARK_VERSION(like 1.6.0)  \
    path/to/linkerProcessorSample/spark2cassandra.py <zk> <kafka_topic>
```
Where `<zk>` is the url of zookeeper, like  `192.168.1.5:2181` or `192.168.1.6:2181,192.168.1.5:2181,192.168.1.7:2181` if have multi zookeeper.`kafka_topic` is the topic of kafka.
3. The open your browser in [localhost:4040](http://localhost:4040) to see if Spark is running

## Run Spark on Mesos Cluster
Here I will not introduce how to set up a Mesos Cluster, you can refer this [GitHub repo](https://github.com/DHOPL/docker-mesos-marathon-cluster) to set it. I assume that you have set up a Mesos Cluster with 1 Mesos master and at least 3 Mesos slaves.

![](https://camo.githubusercontent.com/c2246e442655a68832c0434120e74e1b1cd81d10/687474703a2f2f37786f3676652e636f6d312e7a302e676c622e636c6f7564646e2e636f6d2f6170702d61726368697465637572652e737667)

### Spark driver
Spark on Mesos only `client mode` for python code.So we should run a Spark driver on the Mesos Cluster using Marathon and then use it to submit code to Mesos.
1. run a spark driver docker image
 [Here](https://github.com/dockerq/docker-spark/tree/spark-driver) I maintain a Spark Docker image repo, **all python dependencies have been download in the image**. I will run and exec to it to submit my code. 
The json for Marathon to launch a Spark driver is:
```json
{
  "id": "/spark-driver",
  "cmd": null,
  "cpus": 1,
  "mem": 2048,
  "disk": 2048,
  "instances": 1,
  "constraints": [
    [
      "hostname",
      "LIKE",
      "10.140.0.17"
    ]
  ],
  "container": {
    "type": "DOCKER",
    "volumes": [
      {
        "containerPath": "/linker",
        "hostPath": "/home/zhangjie0220/linkerProcess",
        "mode": "RW"
      }
    ],
    "docker": {
      "image": "adolphlwq/docker-spark:spark-driver-1.6.0",
      "network": "HOST",
      "privileged": false,
      "parameters": [],
      "forcePullImage": true
    }
  },
  "portDefinitions": [
    {
      "port": 10003,
      "protocol": "tcp",
      "labels": {}
    }
  ]
}
```
You should change the cpus and memory but **must provide at least 2G memory for spark driver**.Otherwise the driver will shutdown because lacking memory.
2. submit code
submit script is :
```language
SPARK_HOME/bin/spark-submit \
    --master mesos://host:port \
    --packages org.apache.spark:spark-streaming-kafka_2.10:SPARK_VERSION(like 1.6.0) \
    --executor-memory 3g
    spark2cassandra.py <zk endpoint> <kafka topic>
```
More submit arguments refer [Launching Applications with spark-submit](http://spark.apache.org/docs/latest/submitting-applications.html#launching-applications-with-spark-submit)
## Using DCOS cli
It is now under trying that submit python code to Mesos Cluster.I suggest using Scala write your code if using DCOS cli.
