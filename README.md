# x-ray

## Permissions
|    Module     |                               Command                               |
| :-----------: | ------------------------------------------------------------------- |
|    Shared     | `replSetGetStatus`, `getShardMap`                                   |
|  ClusterItem  | `collStats`, `serverStatus`, `replSetGetStatus`, `replSetGetConfig` |
| HostInfoItem  | `hostInfo`                                                          |
| SecurityItem  | `getCmdLineOpts`                                                    |
| IndexInfoItem | `listDatabases`, `listCollections`, `indexStats`                    |
| ShardKeyItem  | `find` against `config.collections`                                 |