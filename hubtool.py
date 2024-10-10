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
        port_setter.add_argument("state", help="Enable/Disable/Toggle", type=lambda x: State[x.upper()], metavar='portState')
        port_setter.add_argument("port", help="Port to enable/disable", type=int, nargs="+", metavar='portNum', choices={0, 1, 2, 3, 4, 5, 6, 7})
        port_setter.set_defaults(func=self.handle_port)

        upstream_conf = self._subparser.add_parser("upstream")
        upstream_conf.add_argument("host", help="Set Upstream Host. If absent, returns the current upstream host", nargs="?", type=lambda x: Hosts[x.upper()], metavar='host')
        upstream_conf.set_defaults(func=self.handle_upstream)

        resetter = self._subparser.add_parser("reset")
        resetter.set_defaults(func=self.handle_reset)

        return self._parser.parse_args(args[1:])

    def run(self, args):
        args = self.parse_arguments(args)
        if 'func' not in args:
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
            if args.state.value == State.TOGGLE.value:
                cur_state = stem.usb.getPortState(port)
                if cur_state.error != 0:
                    return HubToolStatus.STEM_ERROR
                if cur_state.value == 0:
                    args.state = State.ENABLE
                else:
                    args.state = State.DISABLE

            print(f"{args.state.name[:-1].lower().capitalize()}ing port {port}")

            if args.state.value == State.ENABLE.value:
                result = stem.usb.setPortEnable(port)
            elif args.state.value == State.DISABLE.value:
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

        result = stem.system.reset()
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


# def main(argv):
#     try:
#         print(argv)
#         arg_parser = ArgumentParser()
#         if arg_parser.parse_arguments(argv):
#             return 1

#         return 0

#         print("Port: %d" % (arg_parser.port))
#         print("Enable: %d" % (arg_parser.enable))

#         # Change the brainstem object if you want to connect to a differet module.
#         # i.e. As is, this example will NOT connect to anything except a USBHub3c.
#         stem = brainstem.stem.USBHub3p()
#         # stem = brainstem.stem.USBHub2x4() 

#         result = stem.discoverAndConnect(1)
#         if result == Result.NO_ERROR:
#             if arg_parser.enable:
#                 e = stem.usb.setPortEnable(arg_parser.port)
#             else:
#                 e = stem.usb.setPortDisable(arg_parser.port)
#         else:
#             print("Error Connecting to USBHub3p(). Make sure you are using the correct module object")

#         stem.disconnect()

#     except IOError as e:
#         print("Exception - IOError: ", e)
#         return 2
#     except SystemExit as e:
#         return 3

#     return 0


if __name__ == '__main__':
    sys.exit(HubTool.main(sys.argv))
    # stem = brainstem.stem.USBHub3p()
    # result = stem.discoverAndConnect(1)
    # if result == Result.NO_ERROR:
    #     result = stem.usb.getUpstreamMode()
    #     print(f"Upstream mode: {result}")
    #     print("Change upstream to port 0")
    #     result = stem.usb.setUpstreamMode(0)
    #     print(f"Result: {result}")
    #     result = stem.usb.getUpstreamMode()
    #     print(f"new upstream mode: {result}")
    # else:
    #     print(f"Error connecting: {result}")
