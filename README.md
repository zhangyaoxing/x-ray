# x-ray
This project aims to build a tool to run health check against MongoDB clusters.

## 1 Compatibility Matrix
|  Replica Set  | Sharded Cluster | Standalone |
| :-----------: | :-------------: | :--------: |
| >=4.2 &check; |  >=4.2 &check;  |  &cross;   |

Older versions are not tested.

## 2 Dependencies
The tool is tested with `Python 3.11.12`. Dependencies can be installed by:
```bash
pip install -r requirements.txt
```
## 3 Configurations
### 3.1 Tool Configuration
The configuartion can be any `json` file. You can pass the configuration to the tool by specifying `-c` or `--config`.

This is a example of config file `/config.json`.
```json
{
    "checksets":{
        "default": {
            "items": ["ClusterItem", "ServerStatusItem", "ShardKeyItem","HostInfoItem", "BuildInfoItem", "SecurityItem", "CollInfoItem", "IndexInfoItem"]
        }
    },
    "item_config": {
        "BuildInfoItem": {
            "eol_version": [4, 4, 0]
        },
        "CollInfoItem": {
            "obj_size_kb": 32,
            "collection_size_gb": 2048,
            "fragmentation_ratio": 0.5,
            "index_size_ratio": 0.2,
            "ops_latency_ms": 100
        },
        "IndexInfoItem": {
            "unused_index_days": 7,
            "num_indexes": 10
        },
        "ClusterItem": {
            "replication_lag_seconds": 0,
            "oplog_window_hours": 48
        },
        "ServerStatusItem": {
            "used_connection_ratio": 0.8,
            "query_targeting": 1000,
            "query_targeting_obj": 1000,
            "cache_read_into_mb": 100
        },
        "ShardKeyItem": {
            "sharding_imbalance_percentage": 0.1
        }
    },
    "template": "standard.html"
}
```
There's also the `/config_test.json` which sets the thresholds to a very low level which will fail most tests. It's mainly used for testing purpose.

#### Checksets
*The `checksets` section in the above example.*  
Check sets allows you to define a group of check items that you want to run against the database. By default there's `default` checkset which enables all check items. You can define new checksets that include different items. And you can choose which checkset to run by passing the `-s` or `--checkset` with the set name.

To define a checkset, add a new key in the `checksets` section:
- `checksets.<your set name>.items`: Array of strings. The names of check items.

#### Item Config
*The `item_config` section in the above example.*  
Each check item uses some thresholds to help determine whether a value is in the reasonable range. Some items don't need any thresholds like the `SecurityItem`. Exceeding any threshold will record a test fail item in the final report.

|    Item Name     |          Value          |                             Meaning                             |  Default  |
| :--------------: | :---------------------: | :-------------------------------------------------------------- | :-------: |
|  BuildInfoItem   |       eol_version       | Version older than this setting will be considered end of life. | [4, 4, 0] |
|   CollInfoItem   |       obj_size_kb       | Largest object size in KB.                                      |    32     |
|   CollInfoItem   |   collection_size_GB    | Largest collection size in GB.                                  |   2048    |
|   CollInfoItem   |   fragmentation_ratio   | Highest storage fragmentation ratio.                            |    0.5    |
|   CollInfoItem   |    index_size_ratio     | Largest index:storage ratio.                                    |    0.2    |
|   CollInfoItem   |     ops_latency_ms      | Highest operation latency in ms.                                |    100    |
|  IndexInfoItem   |    unused_index_days    | Longest unused days.                                            |     7     |
|  IndexInfoItem   |       num_indexes       | Number of indexes on one collection.                            |    10     |
|   ClusterItem    | replication_lag_seconds | Replication lag in seconds.                                     |     0     |
|   ClusterItem    |   oplog_window_hours    | Oplog window in hours.                                          |    48     |
| ServerStatusItem |  used_connection_ratio  | Highest used:total connection ratio                             |    0.8    |
| ServerStatusItem |     query_targeting     | Scanned:Returned                                                |   1000    |
| ServerStatusItem |   query_targeting_obj   | Scanned Object:Returned                                         |   1000    |
| ServerStatusItem |   cache_read_into_mb    | Data read into cache / s                                        |    100    |

### 3.2 Database Permissions
**Important:** The tool will connect to each node in the cluster to gather information. For replica sets, you only need to create the user on the primary, and it will be replicated to all members. To sharded cluster, however, the user you created will only be stored in the CSRS, which let mongos and CSRS nodes pass the authentication. The shards will not accept the credential unless you also create the same user on the shards. If the cluster is created by Ops Manager, this has been done by the automation agents. If the clusters is manually created, this needs to be done by yourself.

Each optional check item requires different permissions. Please properly grant the permissions to the user that you use to access MongoDB.
|      Module      |                                           Command                                            |
| :--------------: | -------------------------------------------------------------------------------------------- |
|      Shared      | `replSetGetStatus`, `getShardMap`                                                            |
|   ClusterItem    | `collStats` against `local.oplog.rs`, `serverStatus`, `replSetGetStatus`, `replSetGetConfig` |
|   HostInfoItem   | `hostInfo`                                                                                   |
|   SecurityItem   | `getCmdLineOpts`                                                                             |
|  IndexInfoItem   | `listDatabases`, `listCollections`, `indexStats`                                             |
|   ShardKeyItem   | `find` against `config.collections` and `config.shards`                                      |
|   CollInfoItem   | `listDatabases`, `collStats` against all collections,                                        |
| ServerStatusItem | `serverStatus`                                                                               |
|  BuildInfoItem   | `buildInfo`                                                                                  |

To define a role that has all the permissions:
```javascript
db.createRole({
  role: "xray",
  privileges: [{
    resource: {
      cluster: true
    }, actions: ["replSetGetStatus", "replSetGetConfig", "getShardMap", "serverStatus", "hostInfo", "getCmdLineOpts", "listDatabases"]
  }, {
    resource: {
      db: "", collection: ""
    }, actions: ["collStats", "listCollections", "indexStats"]
  }, {
    resource: {
      db: "config",
      collection: "collections"
    }, actions: ["find"]
  }, {
    resource: {
      db: "config",
      collection: "shards"
    }, actions: ["find"]
  }]
})
```

### 3.3 Template
Different template allows you to customize the report in your own way. Currently there are the following templates:
- `standard.html`: Standard output.
- `no-netork.html`: Removed the link to the resources on the internet. Embeds the content directly into the template instead.
- `full.html`: Enable all features. Need internet access.

When you create your own template, put the `{{ content }}` in a proper position. The placeholder will later be replaced by the report content.

## 4 Output
The output will be in the `output/` or folder specified by you. For each run, there will be a new folder created. Folder name: `<checkset name>-<timestamp>`. If you set `ENV=development` the output will be directly in the root output folder.

The output consists of:
- `results.md` and `results.html`: The final report. In the report you'll see the failed items, and some some raw data collected by each check item.
- `<check item>_raw.json`: Complete raw data collected by each item. You can use them to integrate with other systems.

### 4.1 Raw Data Structure
The raw data collected by each item is organized in a structure that reflects the structure of your target cluster. This is mainly because some check items are better run against the cluster. E.g.: Get replica set config and status. While others may be better against the node. E.g.: Get storage fragmentation ratio.

The raw result collected will be mounted at the node or cluster level depending on which it runs against.

#### 4.1.1 Shared Structures
The following structures can show up at many different places in the result.

##### Test Result Structure.
- `testResult`: `array`. The failed items.
  - `host`: `string`. Hostname of the member. Or `cluster` if it's running against the cluster level (E.g. sharded cluster, or shard, or config).
  - `severity`: `string`. One of `HIGH`, `MEDIUM` and `LOW`.
  - `title`: `string`. Item title.
  - `description`: `string`. Description of the failed item.

##### Member Structure
- `members`: `array`. Replica set members.
  - `host`: `string`. Hostname of the member.
  - `rawResult`: `object`. Raw data collected by the item, against the current host.
  - `testResult`: `array`. The failed items. Refer to the [Test Result Structure](#test-result-structure).

#### 4.1.2 Replica Set
- `type`: `string`. `RS`
- `setName`: `string`. The replica set name.
- `members`: `array`. Replica set members. Refer to the [Member Structure](#member-structure).
- `rawResult`: `object`. Raw data collected by the item, against the replica set.

#### 4.1.3 Sharded Cluster
- `type`: `SH`
- `map`: `object`. Subdocument for all the sharded cluster components.
  - `config`: `object`. Subdocument for all the config server members.
    - `setName`: `string`. CSRS Replica set name.
    - `members`: `array`. CSRS members. Refer to the [Member Structure](#member-structure).
    - `rawResult`: `object`. Raw data collected by the item, against the CSRS.
    - `testResult`: `array`. The failed items against the CSRS. Refer to the [Test Result Structure](#test-result-structure).
  - `mongos`: `object`. Subdocument for all the mongos members.
    - `setName`: `string`. For mongos the `setName` will always be set to `mongos`.
    - `members`: `array`. All mongos members. Refer to the [Member Structure](#member-structure).
    - `rawResult`: `object`. Raw data collected by the item, against the all mongos.
    - `testResult`: `array`. The failed items against all mongos. Refer to the [Test Result Structure](#test-result-structure).
  - `<shard name>`: `object`. Each shard will be mapped to an item. The key `<shard name>` is the shard replica set name.
    - `setName`: `string`. Shard Replica set name.
    - `members`: `array`. Shard members. Refer to the [Member Structure](#member-structure).
    - `rawResult`: `object`. Raw data collected by the item, against the shard.
    - `testResult`: `array`. The failed items against the shard. Refer to the [Test Result Structure](#test-result-structure).
- `rawResult`: `object`. Raw data collected by the item, against the sharded cluster.
- `testResult`: `array`. The failed items. Refer to the [shared structures](#shared-structures).

**Note**: if the test was run against `map.mongos` level, it's essentially the same as running against the cluster. The possible difference is,
- The cluster level `MongoClient` is using the connection string provided by the user, which may not include all mongos instances.
- The `map.mongos` level `MongoClient` is using the connection string that include all known mongos instances, selected from `config.mongos` collections.

The check items usually use the `map.mongos` level so all mongos are included.

## 5 Using the Tool
```bash
./x-ray [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html}] [--uri URI] [-c CONFIG]
```
- `-q`, `--quiet`: Quiet mode. Defaults to `false`.
- `-h`, `--help`: Show the help message and exit.
- `-s`, `--checkset`: Checkset to run. Defaults to `default`.
- `-o`, `--output`: Output folder path. Defaults to `output/`.
- `-f`, `--format`: Output format. Can be `markdown` or `html`. Defaults to `markdown`.
- `--uri`: MongoDB database URI. Defaults to `mongodb://localhost:27017/`.
- `-c`, `--config`: Path to configuration file. Defaults to `config.json`.

Besides, you can use environment variables to control some behaviors:
- `ENV`: `development` will change the following behaviors:
  - Formatted the output JSON for for easier reading.
  - The output will not create a new folder for each run but overwrite the same files.
- `LOG_LEVEL`: Can be `DEBUG`, `ERROR` or `INFO` (default).