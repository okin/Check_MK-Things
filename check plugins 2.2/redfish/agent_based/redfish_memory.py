#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>

# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

# Example Output:
#
#
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
    parse_redfish_multiple,
    redfish_health_state,
    find_key_recursive,
)

register.agent_section(
    name="redfish_memory",
    parse_function=parse_redfish_multiple,
)

HPE_DIMM_STATE = {
    "Null": ("A value is temporarily unavailable", 1),
    "Unknown": ("The status of the DIMM is unknown.", 3),
    "Other": ("DIMM status that does not fit any of these definitions.", 3),
    "NotPresent": ("DIMM is not present.", 1),
    "PresentUnused": ("DIMM is present but unused.", 0),
    "GoodInUse": ("DIMM is functioning properly and currently in use.", 0),
    "AddedButUnused": ("DIMM is added but currently unused.", 0),
    "UpgradedButUnused": ("DIMM is upgraded but currently unused.", 0),
    "ExpectedButMissing": ("DIMM is expected but missing.", 1),
    "DoesNotMatch": ("DIMM type does not match.", 1),
    "NotSupported": ("DIMM is not supported.", 1),
    "ConfigurationError": ("Configuration error in DIMM.", 2),
    "Degraded": ("DIMM state is degraded.", 1),
    "PresentSpare": ("DIMM is present but used as spare.", 0),
    "GoodPartiallyInUse": ("DIMM is functioning properly but partially in use.", 0),
    "MapOutConfiguration": ("DIMM mapped out due to configuration error.", 1),
    "MapOutError": ("DIMM mapped out due to training failure.", 1),
}


def discovery_redfish_memory(section) -> DiscoveryResult:
    """Discover all non absent single modules"""
    for key in section.keys():
        if "Collection" in section[key].get("@odata.type"):
            continue
        if section[key].get("Status", {}).get("State") == "Absent":
            continue
        yield Service(item=section[key]["Id"])


def check_redfish_memory(item: str, section) -> CheckResult:
    """Check module state"""
    data = section.get(item, None)
    if data is None:
        return

    capacity = data.get("CapacityMiB")
    if not capacity:
        capacity = data.get("SizeMB", 0)
    memtype = data.get("MemoryDeviceType")
    if not memtype:
        memtype = data.get("DIMMType")
    opspeed = data.get("OperatingSpeedMhz")
    if not opspeed:
        opspeed = data.get("MaximumFrequencyMHz")
    errcor = data.get("ErrorCorrection")

    mem_msg = f"Size: {capacity / 1024:0.0f}GB, Type: {memtype}-{opspeed} {errcor}"
    yield Result(state=State(0), summary=mem_msg)

    if data.get("Status"):
        status, message = redfish_health_state(data["Status"])
    elif state := find_key_recursive(data, "DIMMStatus"):
        message, status = HPE_DIMM_STATE.get(state, ("Unknown state", 3))
    else:
        status = 0
        message = "No known status value found"

    yield Result(state=State(status), notice=message)


register.check_plugin(
    name="redfish_memory",
    service_name="Memory Module %s",
    sections=["redfish_memory"],
    discovery_function=discovery_redfish_memory,
    check_function=check_redfish_memory,
)
