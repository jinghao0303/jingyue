# Hadoop基础

## Haoop

格式化命令是：hadoop namenode -format，格式化操作会清空NameNode的元数据

核心配置文件是：hdfs-site.xml和yarn-site.xml，分别用于配置HDFS和YARN

启动脚本位于：$HADOOP_HOME/sbin目录下，其中start-dfs.sh命令用于启动HDFS，start-yarn.sh命令用于启动YARN

伪分布模式下：NameNode默认监听端口号是8020，DataNode默认监听端口号是50010

核心组件包括：HDFS和MapReduce，分别负责分布式存储和分布式计算

HDFS数据块副本数量的配置文件是：hdfs-site.xml，其对应的配置项名称为：dfs.replication

HDFS采用了主从(Master/Slave)结构模型，一个HDFS集群是由一个NameNode和若干个DataNode组成的

NameNode作为主服务器，管理文件系统的命名空间和客户端文件的访问操作

DataNode主要负责管理存储的数据

默认复本布局策略是在运行客户端节点上放第一个复本

第二个复本放在与第一个不同且随机另外选择的机架中的节点上

第三个复本与第二个复本放在同一个机架上，且随机选择另一个节点

完全分布模式通常被用于生产环境，主节点和从节点会分开

secondaryNameNode更像是NameNode的一个冷备份，当NameNode宕机后，可以从secondaryNameNode上面恢复部分数据

YARN是Hadoop的资源管理系统，负责集群资源的分配和任务调度



Hadoop的核心组件包括HDFS和MapReduce。HDFS(Hadoop Distributed File System)负责分布式存储，提供高可靠性、高吞吐的数据存储服务;MapReduce负责分布式计算，将大规模数据处理任务分解为多个小任务并行处理，提高计算效率



安装配置Hadoop：使用root账号登录，修改ip、host主机名，配置SSH免密码登录，关闭防火墙，安装JDK，解压hadoop安装包，配置hadoop的核心文件hadoop-env.sh、core-site.xml、mapred-site.xml、hdfs-site.xml，配置hadoop环境变量，格式化hadoop namenode -format，启动节点start-all.sh



namenode：管理集群，存储数据的元信息，并管理记录datanode中的文件信息，secondarynamenode：是namenode的一个快照，会根据configuration中设置的值来决定多少时间周期性的去复制namenode中的metadata及其它数据，Datanode存储数据，ResourceManager负责集群中所有资源的统一管理和分配，接收来自各个节点(NodeManager)的资源汇报信息，并把这些信息按照一定策略分配给各个应用程序，NodeManager是YARN中每个节点上的代理，管理Hadoop集群中单个计算节点



## Linux系统

ls命令：可以查看当前目录下的文件列表

cd命令：可以切换工作目录

vi命令：可以编辑文件内容，:wq命令可以保存退出编辑器

cat命令：可以查看文件内容

scp命令：可以将本地文件复制到远程主机的指定路径下

ssh-keygen命令：用于生成SSH公钥以实现无密码登录

su命令：可以切换用户身份

为保证windows用户和Linux主机间用户能够正常地进行映射，用户必须保证在这两个系统上拥有相同的账号









## JAVA（JDK）

jps命令：查看当前系统运行的Java进程

java -version命令：查看Java版本信息



## Hive

是一个基于Hadoop的一个数据仓库工具，可以将结构化的数据文件映射为一张数据库表

提供简单的SQL查询功能

从Hive shell 中运行shell命令可以使用!操作符

Hive在加载数据过程中不会对数据进行任何的修改，只是将数据转移到HDFS中Hive设定的目录下，外部表实质是将已经存在的HDFS上的文件路径跟表关联起来，删除普通表时，元数据和数据同时被删除，删除外部表时，只删除元数据而不删除数据，创建外部表时需指定external关键字



## Sqoop

Sqoop基于MapReduce分布式处理，支持对HBase写入数据



## ZooKeeper

ZooKeeper具有高性能，同时保证了顺序处理，作用是分布式协调



## HBase

HBase是分布式列式存储系统，依靠HDFS存储底层数据，Region的物理存储单元是ColumnFamily，客户端首次查询HBase数据库时，首先需要从-ROOT-表开始查找，记录按列族集中存放