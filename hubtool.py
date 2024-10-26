#!/usr/bin/python

import brainstem
from brainstem.result import Result

import sys
import argparse
from enum import Enum


class HubToolStatus(Enum):
    SUCCESS = 0
    BAD_ARGS = 1
    NO_STEM = 2
    STEM_ERROR = 3


class Hosts(Enum):
    PC = 0
    PI = 1
    AUTO = 2
    TOGGLE = 3


class State(Enum):
    DISABLE = 0
    OFF = 0
    ENABLE = 1
    ON = 1
    TOGGLE = 2
    TGL = 2
    T = 2


class HubTool:
    def __init__(self):
        self._parser = argparse.ArgumentParser()
        self._subparser = self._parser.add_subparsers()
        self._output = sys.stderr

    def parse_arguments(self, args):
        port_setter = self._subparser.add_parser("port")
        port_setter.add_argument(
            "state",
            help="Enable/Disable/Toggle",
            type=lambda x: State[x.upper()],
            metavar="portState",
        )
        port_setter.add_argument(
            "port",
            help="Port to enable/disable",
            type=int,
            nargs="+",
            metavar="portNum",
            choices={0, 1, 2, 3, 4, 5, 6, 7},
        )
        port_setter.set_defaults(func=self.handle_port)

        upstream_conf = self._subparser.add_parser("upstream")
        upstream_conf.add_argument(
            "host",
            help="Set Upstream Host. If absent, returns the current upstream host",
            nargs="?",
            type=lambda x: Hosts[x.upper()],
            metavar="host",
        )
        upstream_conf.set_defaults(func=self.handle_upstream)

        resetter = self._subparser.add_parser("reset")
        resetter.set_defaults(func=self.handle_reset)

        return self._parser.parse_args(args[1:])

    def run(self, args):
        args = self.parse_arguments(args)
        if "func" not in args:
            self._parser.print_help()
            return HubToolStatus.BAD_ARGS
        elif args.func is not None:
            return args.func(args)
        return HubToolStatus.BAD_ARGS

    def handle_port(self, args):
        stem = self.get_brainstem()
        if stem is None:
            return HubToolStatus.NO_STEM

        result = None
        for port in args.port:
            state_setting = args.state
            if args.state.value == State.TOGGLE.value:
                cur_state = stem.usb.getPortState(port)
                if cur_state.error != 0:
                    return HubToolStatus.STEM_ERROR
                if cur_state.value == 0:
                    state_setting = State.ENABLE
                else:
                    state_setting = State.DISABLE

            print(f"{state_setting.name.lower().capitalize()}ing port {port}")

            if state_setting.value == State.ENABLE.value:
                result = stem.usb.setPortEnable(port)
            elif state_setting.value == State.DISABLE.value:
                result = stem.usb.setPortDisable(port)

        if result == 0:
            return HubToolStatus.SUCCESS
        elif result is None:
            return HubToolStatus.BAD_ARGS
        else:
            return HubToolStatus.STEM_ERROR

    def handle_upstream(self, args):
        stem = self.get_brainstem()
        if stem is None:
            return HubToolStatus.NO_STEM

        if args.host is not None:
            if args.host == Hosts.TOGGLE:
                cur_host = self.get_upstream_host(stem)
                if cur_host is None:
                    return HubToolStatus.STEM_ERROR
                args.host = Hosts.PC if cur_host == Hosts.PI else Hosts.PI

            success = self.set_upstream_host(stem, args.host.value)
            if success:
                return HubToolStatus.SUCCESS
            else:
                return HubToolStatus.STEM_ERROR
        else:
            host = self.get_upstream_host(stem)
            if host is not None:
                print(f"current host: {host.name}")
                print(f"host id: {host.value}")
                return HubToolStatus.SUCCESS
            else:
                return HubToolStatus.STEM_ERROR

    def handle_reset(self, args):
        stem = self.get_brainstem()
        if stem is None:
            return HubToolStatus.NO_STEM

        stem.system.reset()
        return HubToolStatus.SUCCESS

    def get_upstream_host(self, stem):
        result = stem.usb.getUpstreamMode()

        if result.error == 0:
            return Hosts(result.value)
        else:
            return None

    def set_upstream_host(self, stem, hostnum):
        result = stem.usb.setUpstreamMode(hostnum)
        if result == 0:
            return True
        else:
            return False

    def get_brainstem(self):
        stem = brainstem.stem.USBHub3p()
        result = stem.discoverAndConnect(1)
        if result == Result.NO_ERROR:
            return stem
        else:
            return None

    @classmethod
    def main(cls, args):
        return HubTool().run(args).value


if __name__ == "__main__":
    sys.exit(HubTool.main(sys.argv))
