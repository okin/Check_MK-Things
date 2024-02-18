#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>

# License: GNU General Public License v2

from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    Result,
    Service,
    State,
    check_levels,
    register,
)
from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import (
    CheckResult,
    DiscoveryResult,
)

from .utils.redfish import process_redfish_perfdata, redfish_health_state


def _fan_item_name(data):
    fan_name = data.get("Name", data.get("FanName", None))
    if fan_name:
        if fan_name.startswith("Fan"):
            fan_name = fan_name.lstrip("Fan").strip()
        return fan_name
    return None


def discovery_redfish_fans(section) -> DiscoveryResult:
    """Discover single fans"""
    for key in section.keys():
        fans = section[key].get("Fans", None)
        for fan in fans:
            if fan.get("Status", {}).get("State") == "Absent":
                continue
            fan_name = _fan_item_name(fan)
            if fan_name:
                yield Service(item=fan_name)


def check_redfish_fans(item: str, section) -> CheckResult:
    """Check single fan state"""
    fan = None
    for key in section.keys():
        fans = section[key].get("Fans", None)
        if fans is None:
            return

        for fan_data in fans:
            fan_name = _fan_item_name(fan_data)
            if fan_name == item:
                fan = fan_data
                break
        if fan:
            break

    if not fan:
        return

    perfdata = process_redfish_perfdata(fan)
    units = fan.get("ReadingUnits", None)

    if not perfdata:
        yield Result(state=State(0), summary="No performance data found")
    elif units == "Percent":
        yield from check_levels(
            perfdata.value,
            levels_upper=perfdata.levels_upper,
            levels_lower=perfdata.levels_lower,
            metric_name="perc",
            label="Speed",
            render_func=lambda v: "%.1f%%" % v,
            boundaries=(0, 100),
        )
    elif units == "RPM":
        yield from check_levels(
            perfdata.value,
            levels_upper=perfdata.levels_upper,
            levels_lower=perfdata.levels_lower,
            metric_name="fan",
            label="Speed",
            render_func=lambda v: "%.1f rpm" % v,
            boundaries=perfdata.boundaries,
        )
    else:
        yield from check_levels(
            perfdata.value,
            levels_upper=perfdata.levels_upper,
            levels_lower=perfdata.levels_lower,
            metric_name="fan",
            label="Speed",
            render_func=lambda v: "%.1f rpm" % v,
            boundaries=perfdata.boundaries,
        )
        yield Result(state=State(0), summary="No unit found assume RPM!")

    dev_state, dev_msg = redfish_health_state(fan["Status"])

    yield Result(state=State(dev_state), notice=dev_msg)


register.check_plugin(
    name="redfish_fans",
    service_name="Fan %s",
    sections=["redfish_thermal"],
    discovery_function=discovery_redfish_fans,
    check_function=check_redfish_fans,
)
