#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
# ported by (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>
import ast
from typing import Any, Dict, Mapping

from .agent_based_api.v1 import register, render, Result, Service, State
from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult, StringTable

Section = Dict[str, Mapping[str, Any]]


def parse_pure_fa_pod(string_table: StringTable) -> Section:
    parsed: Section = {}
    data = ast.literal_eval(string_table[0][0])
    for element in data:
        parsed.setdefault(element.get("name", "unknown"), element)
    return parsed


register.agent_section(
    name="pure_fa_pod",
    parse_function=parse_pure_fa_pod,
)


def discovery_pure_fa_pod(section: Section) -> DiscoveryResult:
    for item in section:
        yield Service(item=item)


def check_pure_fa_pod(item: str, section: Section) -> CheckResult:
    data = section.get(item)
    if not data:
        return
    status = 0
    if data.get("promotion_status") != data.get("requested_promotion_state"):
        status = 1
        message = "Actual promotion state is different than the expected one - %s vs. %s" % (data.get("promotion_status"), data.get("requested_promotion_state"))
    else:
        message = "Promotion state: %s" % data.get("promotion_status")

    yield Result(state=State(status), summary=message)

    _ARRAY_STATE = {
        "online" : 0,
        "offline": 1,
    }

    for element in data.get("arrays", []):
        status = _ARRAY_STATE.get(element.get("status","unknown"), 3)
        yield Result(state=State(status), notice="Array %s has state %s" % (element.get("name"), element.get("state")))


register.check_plugin(
    name="pure_fa_pod",
    service_name="Pure Pod %s",
    sections=["pure_fa_pod"],
    discovery_function=discovery_pure_fa_pod,
    check_function=check_pure_fa_pod,
)
