from bson import json_util
from libs.log_analysis.log_items.info_item import InfoItem
LOGS = [
    json_util.loads('{"t":{"$date":"2025-06-09T12:20:53.755+01:00"},"s":"I",  "c":"CONTROL",  "id":20721,   "ctx":"conn7857","msg":"Process Details","attr":{"pid":"7360","port":27017,"architecture":"64-bit","host":"test1.yaoxing.online"}}',),
    json_util.loads('{"t":{"$date":"2025-06-09T12:20:53.755+01:00"},"s":"I",  "c":"CONTROL",  "id":20722,   "ctx":"conn7857","msg":"Node is a member of a replica set","attr":{"config":{"_id":"shard_0","version":13,"term":790,"members":[{"_id":0,"host":"test1.yaoxing.online:27017","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":5,"tags":{},"secondaryDelaySecs":0,"votes":1},{"_id":1,"host":"test.yaoxing.online:27017","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":4,"tags":{},"secondaryDelaySecs":0,"votes":1},{"_id":2,"host":"test2.yaoxing.online:27017","arbiterOnly":false,"buildIndexes":true,"hidden":true,"priority":0,"tags":{},"secondaryDelaySecs":0,"votes":0},{"_id":3,"host":"test3.yaoxing.online:27017","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":3,"tags":{},"secondaryDelaySecs":0,"votes":1},{"_id":4,"host":"test4.yaoxing.online:27017","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":2,"tags":{},"secondaryDelaySecs":0,"votes":1},{"_id":5,"host":"test5.yaoxing.online:27017","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":1,"tags":{},"secondaryDelaySecs":0,"votes":1}],"protocolVersion":1,"writeConcernMajorityJournalDefault":true,"settings":{"chainingAllowed":true,"heartbeatIntervalMillis":2000,"heartbeatTimeoutSecs":10,"electionTimeoutMillis":10000,"catchUpTimeoutMillis":-1,"catchUpTakeoverDelayMillis":30000,"getLastErrorModes":{},"getLastErrorDefaults":{"w":1,"wtimeout":0}}},"memberState":"SECONDARY"}}',),
    json_util.loads('{"t":{"$date":"2025-06-09T12:20:53.755+01:00"},"s":"I",  "c":"REPL",     "id":5853300, "ctx":"conn7857","msg":"current featureCompatibilityVersion value","attr":{"featureCompatibilityVersion":"6.0","context":"log rotation"}}'),
    json_util.loads('{"t":{"$date":"2025-07-01T10:16:17.695+01:00"},"s":"I",  "c":"CONTROL",  "id":23403,   "ctx":"initandlisten","msg":"Build Info","attr":{"buildInfo":{"version":"5.0.31","gitVersion":"973237567d45610d6976d5d489dfaaef6a52c2f9","openSSLVersion":"OpenSSL 1.1.1k  FIPS 25 Mar 2021","modules":["enterprise"],"allocator":"tcmalloc","environment":{"distmod":"rhel80","distarch":"x86_64","target_arch":"x86_64"}}}}'),
    json_util.loads('{"t":{"$date":"2025-07-01T10:16:17.695+01:00"},"s":"I",  "c":"CONTROL",  "id":51765,   "ctx":"initandlisten","msg":"Operating System","attr":{"os":{"name":"Red Hat Enterprise Linux release 8.10 (Ootpa)","version":"Kernel 4.18.0-553.53.1.el8_10.x86_64"}}}',),
    json_util.loads('{"t":{"$date":"2025-07-01T10:16:17.695+01:00"},"s":"I",  "c":"CONTROL",  "id":21951,   "ctx":"initandlisten","msg":"Options set by command line","attr":{"options":{"config":"/mongod/data/automation-mongod.conf","net":{"bindIp":"0.0.0.0","port":27017,"tls":{"CAFile":"/mongod/cert/rootca.pem","allowConnectionsWithoutCertificates":true,"certificateKeyFile":"/mongod/cert/cert.pem","disabledProtocols":"TLS1_0,TLS1_1","mode":"requireTLS"}},"processManagement":{"fork":true},"replication":{"oplogSizeMB":600000,"replSetName":"shard_0"},"security":{"authorization":"enabled","clusterAuthMode":"keyFile","keyFile":"/var/lib/mongodb-mms-automation/keyfile","redactClientLogData":true},"setParameter":{"authenticationMechanisms":"SCRAM-SHA-1,PLAIN"},"sharding":{"clusterRole":"shardsvr"},"storage":{"dbPath":"/mongod/data","engine":"wiredTiger"},"systemLog":{"destination":"file","path":"/mongod/log/mongodb.log"}}}}'),
    json_util.loads('{"t":{"$date":"2025-07-01T10:16:17.586+01:00"},"s":"I",  "c":"NETWORK",  "id":4913010, "ctx":"-","msg":"Certificate information","attr":{"subject":"CN=test1.yaoxing.online,OU=PS,C=SW","issuer":"CN=MongoDB Issuing CA01,DC=EU,DC=ADROOT,DC=MongoDB","thumbprint":"9C576C0A3C740CB984232EE4F680DAF95C8345DB","notValidBefore":{"$date":"2025-05-25T06:28:40.000Z"},"notValidAfter":{"$date":"2026-05-25T06:28:40.000Z"},"keyFile":"/mongod/cert/cert.pem","type":"Server"}}'),    json_util.loads('{"t":{"$date":"2025-06-09T12:20:53.755+01:00"},"s":"I",  "c":"REPL",     "id":5853300, "ctx":"conn7857","msg":"current featureCompatibilityVersion value","attr":{"featureCompatibilityVersion":"6.0","context":"log rotation"}}'),
    json_util.loads('{"t":{"$date":"2025-07-01T10:16:17.695+01:00"},"s":"I",  "c":"CONTROL",  "id":4615611, "ctx":"initandlisten","msg":"MongoDB starting","attr":{"pid":39309,"port":27017,"dbPath":"/mongod/data","architecture":"64-bit","host":"test1.yaoxing.online"}}'),
]

def test_info_item():
    item = InfoItem(output_folder="/tmp", config={})
    for log in LOGS:
        item.analyze(log)
    result = item._cache
    assert "process" in result
    assert result["process"]["pid"] == 39309
    assert "replica_set" in result
    assert result["replica_set"]["config"]["_id"] == "shard_0"
    assert "fcv" in result
    assert result["fcv"] == "6.0"
    assert "build_info" in result
    assert result["build_info"]["version"] == "5.0.31"
    assert "os" in result
    assert "Red Hat Enterprise Linux" in result["os"]["name"]
    assert "command_line_options" in result
    assert result["command_line_options"]["net"]["port"] == 27017
    assert "cert_info" in result
    assert result["cert_info"]["subject"] == "CN=test1.yaoxing.online,OU=PS,C=SW"