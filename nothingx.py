#!/usr/bin/env python3
import sys
import logging
import argparse
from nothingx import Device
from nothingx.errors import NothingError


HELP = """\
usage: python3 nothingx.py [--debug] <command> [...]

commands:
  battery              left, right, and case (when available) battery levels
  firmware             firmware version string
  info                 device name, MAC, and firmware
  anc <mode>           set noise control mode
                         high, mid, low, adaptive, transparency, off
  find <side>          ring an earbud to find it
                         left, right, both, stop
  watch [--timeout N]  monitor live battery updates (includes case battery)
                         waits for push events (lid open/close) for N seconds

options:
  --debug              print raw Bluetooth packets
  -h, --help           show this message and exit\
"""


def build_parser():
    p = argparse.ArgumentParser(
        prog="nothingx",
        description=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    p.add_argument("-h", "--help", action="store_true")
    p.add_argument("--debug", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("battery")
    sub.add_parser("firmware")
    sub.add_parser("info")

    anc = sub.add_parser("anc")
    anc.add_argument("mode", choices=["high", "mid", "low", "adaptive", "transparency", "off"])

    find = sub.add_parser("find")
    find.add_argument("side", choices=["left", "right", "both", "stop"])

    watch = sub.add_parser("watch")
    watch.add_argument("--timeout", type=float, default=60.0,
                       help="seconds to listen for battery push events (default: 60)")

    return p


def run(args, ear: Device):
    if args.cmd == "battery":
        b = ear.battery()
        print(f"Left:  {b.left}%")
        print(f"Right: {b.right}%")
        if b.case is not None:
            print(f"Case:  {b.case}%")

    elif args.cmd == "firmware":
        print(ear.info.firmware())

    elif args.cmd == "info":
        print(f"{ear.name}  ({ear.mac})")
        print(f"Firmware: {ear.info.firmware()}")

    elif args.cmd == "anc":
        m = args.mode
        if m == "high":           ear.anc.high()
        elif m == "mid":          ear.anc.mid()
        elif m == "low":          ear.anc.low()
        elif m == "adaptive":     ear.anc.adaptive()
        elif m == "transparency": ear.anc.transparency()
        elif m == "off":          ear.anc.off()
        print(f"ANC → {m}")

    elif args.cmd == "find":
        s = args.side
        if s == "left":    ear.find.left()
        elif s == "right": ear.find.right()
        elif s == "both":  ear.find.both()
        elif s == "stop":  ear.find.stop()
        print(f"find → {s}")

    elif args.cmd == "watch":
        print(f"Monitoring battery (Ctrl-C to stop, timeout={args.timeout:.0f}s)...")
        print("Tip: open/close the case lid to trigger a case battery update.")
        try:
            for b in ear.battery.watch(timeout=args.timeout):
                parts = [f"Left: {b.left}%", f"Right: {b.right}%"]
                if b.case is not None:
                    parts.append(f"Case: {b.case}%")
                print("  " + "  ".join(parts))
        except KeyboardInterrupt:
            pass


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.help or not args.cmd:
        print(HELP)
        sys.exit(0)

    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level, format="%(name)s: %(message)s")

    try:
        ear = Device.discover()
    except NothingError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        run(args, ear)
    except NothingError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        ear.disconnect()


if __name__ == "__main__":
    main()
