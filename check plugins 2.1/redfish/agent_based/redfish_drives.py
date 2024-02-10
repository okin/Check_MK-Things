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
    parse_redfish_multiple,
    redfish_health_state,
)

register.agent_section(
    name="redfish_drives",
    parse_function=parse_redfish_multiple,
)


def discovery_redfish_drives(section: RedfishAPIData) -> DiscoveryResult:
    for key in section.keys():
        if section[key].get("Status", {}).get("State") == "Absent":
            continue
        item = section[key].get("Id", "0") + "-" + section[key]["Name"]
        yield Service(item=item)


def check_redfish_drives(item: str, section: RedfishAPIData) -> CheckResult:
    data = None
    for key in section.keys():
        if item == section[key].get("Id", "0") + "-" + section[key]["Name"]:
            data = section.get(key, None)
            break
    if data is None:
        return

    disc_msg = (
        f"Size: {data.get('CapacityBytes', 0) / 1024 / 1024 / 1024:0.0f}GB, "
        f"Speed {data.get('CapableSpeedGbs', 0)} Gbs"
    )

    if data.get("MediaType") == "SSD":
        if data.get("PredictedMediaLifeLeftPercent"):
            disc_msg = (
                f"{disc_msg}, Media Life Left: "
                f"{int(data.get('PredictedMediaLifeLeftPercent', 0))}%"
            )
        else:
            disc_msg = f"{disc_msg}, no SSD Media information available"

    yield Result(state=State(0), summary=disc_msg)

    dev_state, dev_msg = redfish_health_state(data["Status"])
    yield Result(state=State(dev_state), notice=dev_msg)


register.check_plugin(
    name="redfish_drives",
    service_name="Drive %s",
    sections=["redfish_drives"],
    discovery_function=discovery_redfish_drives,
    check_function=check_redfish_drives,
)
