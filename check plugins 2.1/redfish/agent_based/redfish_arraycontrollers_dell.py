#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>

# License: GNU General Public License v2

from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import (
    CheckResult,
    DiscoveryResult,
)
from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    register,
    Result,
    State,
    Service,
)
from .utils.redfish import (
    RedfishAPIData,
    redfish_health_state,
)


def discovery_redfish_arraycontrollers_dell(section: RedfishAPIData) -> DiscoveryResult:
    for key in section.keys():
        if section[key].get("Oem"):
            if section[key]["Oem"].get("Dell"):
                yield Service(item=section[key]["Id"])


def check_redfish_arraycontrollers_dell(item: str, section: RedfishAPIData) -> CheckResult:
    data = section.get(item, None)
    if data is None:
        return

    if data.get("StorageControllers@odata.count") == 1:
        ctrl_data = data.get("StorageControllers")[0]

        storage_msg = (
            f"Type: {ctrl_data.get('Model')}, "
            f"RaidLevels: {','.join(ctrl_data.get('SupportedRAIDTypes', []))}, "
            f"DeviceProtocols: {','.join(ctrl_data.get('SupportedDeviceProtocols', []))}"
        )
        yield Result(state=State(0), summary=storage_msg)

    dev_state, dev_msg = redfish_health_state(data["Status"])
    status = dev_state
    message = dev_msg

    yield Result(state=State(status), notice=message)


register.check_plugin(
    name="redfish_arraycontrollers_dell",
    service_name="Storage Controller %s",
    sections=["redfish_arraycontrollers"],
    discovery_function=discovery_redfish_arraycontrollers_dell,
    check_function=check_redfish_arraycontrollers_dell,
)
