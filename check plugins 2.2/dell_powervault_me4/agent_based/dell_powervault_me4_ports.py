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

from .utils.dell_powervault_me4 import parse_dell_powervault_me4

register.agent_section(
    name="dell_powervault_me4_ports",
    parse_function=parse_dell_powervault_me4,
)


def discovery_dell_powervault_me4_ports(section) -> DiscoveryResult:
    for item in section:
        yield Service(item=item, parameters={"state": section[item]["health-numeric"]})


def check_dell_powervault_me4_ports(item: str, params, section) -> CheckResult:
    data = section.get(item, {})
    if not data:
        return
    port_states = {
        0: ("OK", 0),
        1: ("Degraded", 1),
        2: ("Fault", 2),
        3: ("Unknown", 3),
        4: ("Disconnected", 0),
    }

    if params:
        inv_state_text, inv_state_num = port_states.get(params["state"], ("Unknown", 3))
    else:
        inv_state_num = False
        inv_state_text = ""

    state_text, status_num = port_states.get(
        data.get("health-numeric", 3), ("Unknown", 3)
    )

    if data.get("status") == "Disconnected":
        message = "is not connected(!)"
    else:
        message = f"with {data.get('actual-speed')} has state {data.get('status')} \
                   - health state is {state_text}"

    if (int(status_num) != int(inv_state_num)) and params:
        message += (
            f" - state changed since inventory from {inv_state_text} to {state_text}(!)"
        )
        status_num = max(status_num, 1)

    yield Result(state=State(status_num), summary=message)


register.check_plugin(
    name="dell_powervault_me4_ports",
    service_name="Port %s",
    sections=["dell_powervault_me4_ports"],
    check_default_parameters={
        "port_state": 0,
    },
    discovery_function=discovery_dell_powervault_me4_ports,
    check_function=check_dell_powervault_me4_ports,
    check_ruleset_name="dell_powervault_me4_ports",
)
