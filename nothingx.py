#!/usr/bin/env python3
import sys
import logging
import argparse
from nothingx import Device
from nothingx.errors import NothingError


def build_parser():
    p = argparse.ArgumentParser(
        prog="nothingx",
        description="Control Nothing Ear earbuds from your PC."
    )
    p.add_argument("--debug", action="store_true", help="show raw Bluetooth traffic")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("battery",  help="battery levels")
    sub.add_parser("firmware", help="firmware version")
    sub.add_parser("info",     help="device info")

    anc = sub.add_parser("anc", help="set ANC mode")
    anc.add_argument("mode", choices=["high", "mid", "low", "adaptive", "transparency", "off"])

    find = sub.add_parser("find", help="ring earbuds")
    find.add_argument("side", choices=["left", "right", "both", "stop"])

    return p


def run(args, ear: Device):
    if args.cmd == "battery":
        b = ear.battery()
        print(f"Left:  {b.left}%")
        print(f"Right: {b.right}%")

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


def main():
    parser = build_parser()
    args = parser.parse_args()

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
