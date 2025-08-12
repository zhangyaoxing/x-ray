from pymongo.errors import OperationFailure
from libs.check_items.base_item import BaseItem, SEVERITY
from libs.utils import *

MEMBER_STATE = {
    0: "STARTUP",
    1: "PRIMARY",
    2: "SECONDARY",
    3: "RECOVERING",
    5: "STARTUP2",
    6: "UNKNOWN",
    7: "ARBITER",
    8: "DOWN",
    9: "ROLLBACK",
    10: "REMOVED"
}

class ReplicaSetItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Replica Set Information"
        self._description = "Collects and reviews replica set configuration and status."

    def _gather_replset_info(self, client):
        """
        Gather replica set configuration and status.
        """
        try:
            is_master = client.admin.command("isMaster")
            if not is_master.get("setName"):
                self._logger.warning(yellow("This MongoDB instance is not part of a replica set. Skipping..."))
                return None, None
            replset_status = client.admin.command("replSetGetStatus")
            replset_config = client.admin.command("replSetGetConfig")
            return replset_status, replset_config
        except OperationFailure as e:
            self._logger.warning(yellow(f"Failed to gather replica set information: {str(e)}"))
            return None, None
        
    def _check_replset_status(self, replset_status):
        """
        Check the replica set status for any issues.
        """
        # Find primary in members
        primary_member = next(iter(m for m in replset_status["members"] if m["state"] == 1), None)

        if not primary_member:
            self.append_item_result(
                SEVERITY.HIGH,
                "No Primary",
                "The replica set does not have a primary."
            )

        # Check member states
        max_delay = self._config.get("replication_lag_seconds", 60)
        for member in replset_status["members"]:
            # Check problematic states
            state = member["state"]
            host = member["name"]
            
            if state in [3, 6, 8, 9, 10]:
                self.append_item_result(
                    SEVERITY.HIGH,
                    "Unhealthy Member",
                    f"Member `{host}` is in `{MEMBER_STATE[state]}` state."
                )
            elif state in [0, 5]:
                self.append_item_result(
                    SEVERITY.LOW,
                    "Initializing Member",
                    f"Member `{host}` is being initialized in `{MEMBER_STATE[state]}` state."
                )

            # Check replication lag
            if state == 2:  # SECONDARY
                lag = member["optimeDate"] - primary_member["optimeDate"]
                if lag.seconds >= max_delay:
                    self.append_item_result(
                        SEVERITY.HIGH,
                        "High Replication Lag",
                        f"Member `{host}` has a replication lag of `{lag.seconds}` seconds, which is greater than the configured threshold of `{max_delay}` seconds."
                    )

    def _check_replset_config(self, replset_config):
        """
        Check the replica set configuration for any issues.
        """
        # Check number of voting members
        voting_members = sum(1 for member in replset_config["config"]["members"] if member.get("votes", 0) > 0)
        if voting_members < 3:
            self.append_item_result(
                SEVERITY.HIGH,
                "Insufficient Voting Members",
                f"The replica set has only {voting_members} voting members. Consider adding more to ensure fault tolerance."
            )
        if voting_members % 2 == 0:
            self.append_item_result(
                SEVERITY.HIGH,
                "Even Voting Members",
                "The replica set has an even number of voting members, which can lead to split-brain scenarios. Consider adding an additional member."
            )
        
        for member in replset_config["config"]["members"]:
            if member.get("slaveDelay", 0) > 0:
                if member.get("votes", 0) > 0:
                    self.append_item_result(
                        SEVERITY.HIGH,
                        "Delayed Voting Member",
                        f"Member `{member['host']}` is a delayed secondary but is also a voting member. This can lead to performance issues."
                    )
                elif member.get("priority", 0) > 0:
                    self.append_item_result(
                        SEVERITY.HIGH,
                        "Delayed Voting Member",
                        f"Member `{member['host']}` is a delayed secondary but is has non-zero priority. This can lead to potential issues."
                    )
                elif not member.get("hidden", False):
                    self.append_item_result(
                        SEVERITY.MEDIUM,
                        "Delayed Voting Member",
                        f"Member `{member['host']}` is a delayed secondary and should be configured as hidden."
                    )
                else:
                    self.append_item_result(
                        SEVERITY.LOW,
                        "Delayed Voting Member",
                        f"Member `{member['host']}` is a delayed secondary. Delayed secondaries are not recommended in general."
                    )
            if member.get("arbiterOnly", False):
                self.append_item_result(
                    SEVERITY.HIGH,
                    "Arbiter Member",
                    f"Member `{member['host']}` is an arbiter. Arbiters are not recommended."
                )

    def test(self, *args, **kwargs):
        self._logger.info("Gathering replica set config / status...")
        client = kwargs.get("client")
        replset_status, replset_config = self._gather_replset_info(client)
        if not replset_status or not replset_config:
            return

        self._check_replset_status(replset_status)
        self._check_replset_config(replset_config)

        self.sample_result = {
            "replset_status": replset_status,
            "replset_config": replset_config
        }