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
  fit                  run eartip fit test (keep earbuds in ears, takes ~2s)
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
    sub.add_parser("fit")

    anc = sub.add_parser("anc")
    anc.add_argument("mode", choices=["high", "mid", "low", "adaptive", "transparency", "off"])

    find = sub.add_parser("find")
    find.add_argument("side", choices=["left", "right", "both", "stop"])

    watch = sub.add_parser("watch")
    watch.add_argument("--timeout", type=float, default=60.0,
                       help="seconds to listen for battery push events (default: 60)")

    return p


def _fmt_case(level: int) -> str:
    if level == 0:
        return "Case:  0% (case disconnected/battery empty)"
    return f"Case:  {level}%"


def run(args, ear: Device):
    if args.cmd == "battery":
        b = ear.battery()
        print(f"Left:  {b.left}%")
        print(f"Right: {b.right}%")
        if b.case is not None:
            print(_fmt_case(b.case))

    elif args.cmd == "firmware":
        print(ear.info.firmware())

    elif args.cmd == "info":
        print(f"{ear.name}  ({ear.mac})")
        print(f"Firmware: {ear.info.firmware()}")

    elif args.cmd == "fit":
        print("Running eartip fit test — keep both earbuds in your ears...")
        try:
            result = ear.fit.run()
        except TimeoutError as e:
            print(f"Error: {e}")
        else:
            def _side(code):
                return {0: "✓ Good seal", 1: "✗ Poor seal", 2: "✗ Not in ear"}.get(code, f"✗ Unknown ({code})")
            print(f"Left:  {_side(result.left)}")
            print(f"Right: {_side(result.right)}")
            if result.left_ok and result.right_ok:
                print("\033[1mPerfect fit — you're ready!\033[0m")
            elif result.left == 2 or result.right == 2:
                print("\033[1mOne or both earbuds not detected — make sure they're in your ears.\033[0m")
            else:
                bad = [s for s, c in (("left", result.left), ("right", result.right)) if c != 0]
                print(f"\033[1mPoor seal on {' and '.join(bad)} side — try adjusting or switching eartip size.\033[0m")

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
                    case_str = "Case: 0% (case disconnected/battery empty)" if b.case == 0 else f"Case: {b.case}%"
                    parts.append(case_str)
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
