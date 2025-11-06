from libs.log_analysis.log_items.base_item import BaseItem


class StateTraceItem(BaseItem):
    LOG_IDS = [
        4615611,  # starting (for rs members)
        20721,  # starting (for shard members)
        21392,  # new configuration applied
        21215,  # new state
        21216,  # new state
        21358,  # state transition
        4615660,  # priority takeover
    ]

    def __init__(self, output_folder, config):
        super().__init__(output_folder, config)
        self.name = "Member State Trace"
        self.description = "Visualize member state trace logs to understand system state changes over time."
        self._cache = None
        self._myself = "self"
        self._show_reset = True
        self._last_log = None

    def analyze(self, log_line):
        super().analyze(log_line)
        log_id = log_line.get("id", "")
        if log_id not in self.LOG_IDS:
            return
        if self._cache is None:
            self._cache = {}
        msg = log_line.get("msg", "")
        if log_id == 4615611:
            # Identify myself
            host = log_line.get("attr", {}).get("host", "unknown")
            port = log_line.get("attr", {}).get("port", "unknown")
            self._myself = f"{host}:{port}"
        if log_id == 21392:
            # New configuration applied
            host = self._myself
            config = log_line.get("attr", {}).get("config", {})
            if host not in self._cache:
                self._cache[host] = []
            self._cache[host].append(
                {
                    "id": log_id,
                    "host": host,
                    "timestamp": log_line.get("t", ""),
                    "event": "NewConfig",
                    "details": {"msg": msg, "config": config},
                }
            )
        if log_id == 21215:
            # New state for others
            host = log_line.get("attr", {}).get("hostAndPort", {})
            new_state = log_line.get("attr", {}).get("newState", "unknown")
            if host not in self._cache:
                self._cache[host] = []
            self._cache[host].append(
                {
                    "id": log_id,
                    "host": host,
                    "timestamp": log_line.get("t", ""),
                    "event": "NewMemberState",
                    "details": {"new_state": new_state, "msg": msg},
                }
            )
        if log_id == 21216:
            # New state
            host = log_line.get("attr", {}).get("hostAndPort", {})
            # match new state from msg
            new_state = msg.split(" ")[-1] if msg else "UNKNOWN"
            # normalize RS_DOWN to DOWN because according to the document DOWN is the correct state name.
            if new_state == "RS_DOWN":
                new_state = "DOWN"
            if host not in self._cache:
                self._cache[host] = []
            self._cache[host].append(
                {
                    "id": log_id,
                    "host": host,
                    "timestamp": log_line.get("t", ""),
                    "event": "NewMemberState",
                    "details": {"new_state": new_state, "msg": msg},
                }
            )
        if log_id == 21358:
            # State transition
            host = self._myself
            old_state = log_line.get("attr", {}).get("oldState", "unknown")
            new_state = log_line.get("attr", {}).get("newState", "unknown")
            if host not in self._cache:
                self._cache[host] = []
            self._cache[host].append(
                {
                    "id": log_id,
                    "host": host,
                    "timestamp": log_line.get("t", ""),
                    "event": "StateTransition",
                    "details": {"msg": msg, "old_state": old_state, "new_state": new_state},
                }
            )
        if log_id == 4615660:
            # Priority takeover
            host = self._myself
            msg = log_line.get("msg", "")
            if host not in self._cache:
                self._cache[host] = []
            self._cache[host].append(
                {
                    "id": log_id,
                    "host": host,
                    "timestamp": log_line.get("t", ""),
                    "event": "Priority Takeover",
                    "details": {"msg": msg},
                }
            )
        self._last_log = log_line

    def finalize_analysis(self):
        if self._last_log:
            # Because we are using line chart to describe the state changes,
            # we need to add a final point to indicate the last known state.
            # Otherwise, the chart will end abruptly at the last event.
            for host, events in self._cache.items():
                events.append(
                    {
                        "id": -1,
                        "host": host,
                        "timestamp": self._last_log.get("t", "") if self._last_log else "",
                        "event": "LogEnd",
                        "details": {"msg": "End of log"},
                    }
                )
        super().finalize_analysis()

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f'<canvas id="canvas_{self.__class__.__name__}" height="300" width="400"></canvas>\n')
