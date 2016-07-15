# Debug info
## problem 1
1. Why spark application fail with “executor.CoarseGrainedExecutorBackend: Driver Disassociated”?
[executor.CoarseGrainedExecutorBackend: Driver Disassociated](http://stackoverflow.com/questions/28967500/why-spark-application-fail-with-executor-coarsegrainedexecutorbackend-driver-d)
[jianshu](http://www.jianshu.com/p/80dc6209acc0)

2. `16/07/14 21:34:32 INFO RemoteActorRefProvider$RemotingTerminator: Shutting down remote daemon` `I0714 13:36:28.319780   464 exec.cpp:390] Executor asked to shutdown`

problem 1 has solved. **We `must` provide enough cpu and memory for spark driver**