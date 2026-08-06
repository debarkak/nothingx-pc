#!/usr/bin/env python3
import sys
import logging
import argparse
from nothingx import Device
from nothingx.errors import NothingError


HELP = """\
usage: nothingx [--debug] [-d DEVICE] <command> [...]

commands:
  select               interactively select active Nothing device
  devices              list all paired Nothing devices
  battery              left, right, and case (when available) battery levels
  firmware             firmware version string
  info                 device name, MAC, and firmware
  fetch                fetch and display all current device settings
  anc <mode>           set noise control mode
                         high, mid, low, adaptive, transparency, off
  find <side>          ring an earbud to find it
                         left, right, both, stop
  fit                  run eartip fit test to check for optimised noise cancellation
  latency <on|off|get> control low lag mode
  bass <on|off|get> [N] control enhanced bass (level 1-5)
  watch [--timeout N]  monitor live battery updates

options:
  -d, --device NAME    target specific paired device (name or MAC)
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
    p.add_argument("-d", "--device", type=str, help="target specific paired device")
    p.add_argument("--debug", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("select")
    sub.add_parser("devices")
    sub.add_parser("battery")
    sub.add_parser("firmware")
    sub.add_parser("info")
    sub.add_parser("fetch")
    sub.add_parser("fit")

    anc = sub.add_parser("anc")
    anc.add_argument("mode", choices=["high", "mid", "low", "adaptive", "transparency", "off"])

    find = sub.add_parser("find")
    find.add_argument("side", choices=["left", "right", "both", "stop"])

    latency = sub.add_parser("latency")
    latency.add_argument("action", choices=["on", "off", "get"])

    bass = sub.add_parser("bass")
    bass.add_argument("action", choices=["on", "off", "get"])
    bass.add_argument("level", type=int, nargs="?", default=None, help="bass level (1-5)")

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

    elif args.cmd == "fetch":
        print(f"Device:   {ear.name} ({ear.mac})")
        print(f"Firmware: {ear.info.firmware()}")
        print("---------------------------------")
        b = ear.battery()
        
        l_act = "Yes" if b.left > 0 else "No"
        r_act = "Yes" if b.right > 0 else "No"
        print(f"Active:   L: {l_act}  |  R: {r_act}")
        print(f"Battery:  L {b.left}%  |  R {b.right}%" + (f"  |  Case {b.case}%" if b.case else ""))
        print(f"ANC Mode: {ear.anc.get().title()}")
        print(f"Low Lag:  {'ON' if ear.latency.get() else 'OFF'}")
        b_info = ear.bass.get()
        b_st = f"ON (Level {b_info['level']})" if b_info['enabled'] else "OFF"
        print(f"Bass:     {b_st}")

    elif args.cmd == "latency":
        if args.action == "get":
            state = ear.latency.get()
            print(f"Low Lag Mode: {'ON' if state else 'OFF'}")
        elif args.action == "on":
            ear.latency.set(True)
            print("Low Lag Mode: ON")
        elif args.action == "off":
            ear.latency.set(False)
            print("Low Lag Mode: OFF")

    elif args.cmd == "bass":
        if args.action == "get":
            b_info = ear.bass.get()
            if b_info["enabled"]:
                print(f"Enhanced Bass: ON (Level: {b_info['level']})")
            else:
                print("Enhanced Bass: OFF")
        elif args.action == "on":
            lvl = args.level if args.level is not None else 5
            if lvl == 0:
                ear.bass.off()
                print("Enhanced Bass: OFF")
            else:
                ear.bass.on(lvl)
                print(f"Enhanced Bass: ON (Level: {lvl})")
        elif args.action == "off":
            ear.bass.off()
            print("Enhanced Bass: OFF")

    elif args.cmd == "fit":
        print("Running eartip fit test — keep both earbuds in your ears...\n")
        print("\n\n\n\n\n") # Space for earbuds + text
        
        reset = "\033[0m"
        
        def build_frames(dot_color, reverse=False):
            dot = f"{dot_color}@{reset}"
            frames = [
                ["  .-.  ", f" ( {dot} ) ", "  | |  ", "  | |  ", "  '-'  "],
                ["  .-.  ", f" ({dot}  ) ", "  | |  ", "  | |  ", "  '-'  "],
                ["   .   ", "  ( )  ", "   |   ", "   |   ", "   '   "],
                ["  .-.  ", " (   ) ", "  | |  ", "  | |  ", "  '-'  "],
                ["   .   ", "  ( )  ", "   |   ", "   |   ", "   '   "],
                ["  .-.  ", f" (  {dot}) ", "  | |  ", "  | |  ", "  '-'  "]
            ]
            return [frames[0], frames[5], frames[4], frames[3], frames[2], frames[1]] if reverse else frames

        l_frames = build_frames("\033[90m") # Dark gray
        r_frames = build_frames("\033[31m", reverse=True) # Red

        anim_idx = 0
        last_step = 0
        def step():
            nonlocal anim_idx, last_step
            import time
            if time.time() - last_step < 0.15:
                return
            last_step = time.time()
            
            sys.stdout.write("\033[6A") # Move up 6 lines (5 for buds + 1 for text)
            frame_l = l_frames[anim_idx % 6]
            frame_r = r_frames[anim_idx % 6]
            for i in range(5):
                sys.stdout.write(f"      {frame_l[i]}          {frame_r[i]}\033[K\n")
            
            dots = "." * ((anim_idx % 3) + 1)
            sys.stdout.write(f"        Testing fit{dots:<3} \033[K\n")
            sys.stdout.flush()
            anim_idx += 1

        try:
            result = ear.fit.run(step_callback=step)
        except TimeoutError as e:
            sys.stdout.write("\033[6A\033[J")
            print(f"Error: {e}")
        else:
            def get_color(c):
                return "\033[97m" if c == 0 else "\033[33m" if c == 1 else "\033[31m"
                
            def colored_earbud(c):
                dot = f"{c}@{reset}"
                return [f"{c}  .-.  {reset}", f"{c} ( {dot} ){reset}", f"{c}  | |  {reset}", f"{c}  | |  {reset}", f"{c}  '-'  {reset}"]

            final_l = colored_earbud(get_color(result.left))
            final_r = colored_earbud(get_color(result.right))
            
            sys.stdout.write("\033[6A")
            for i in range(5):
                sys.stdout.write(f"      {final_l[i]}          {final_r[i]}\033[K\n")
            sys.stdout.write("      \033[1mTest Complete!\033[0m\033[K\n")
            sys.stdout.flush()

            def _side(c):
                return "\033[97m✓ Good seal\033[0m" if c == 0 else "\033[33m! Moderate/Poor seal\033[0m" if c == 1 else "\033[31m✗ Awful seal / Not in ear\033[0m"
                
            print(f"\nLeft:  {_side(result.left)}")
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


def list_devices():
    from nothingx.scanner import Scanner
    devs = Scanner.find_all_nothing()
    if not devs:
        print("error: no paired Nothing / Ear / CMF devices found.", file=sys.stderr)
        sys.exit(1)
    selected = Scanner.get_selected()
    selected_mac = selected["mac"] if selected else None

    print("Paired Nothing Devices:")
    for d in devs:
        active_mark = "  \033[32m[active]\033[0m" if d["mac"] == selected_mac else ""
        print(f"  • {d['name']} ({d['mac']}){active_mark}")


def select_device_interactive():
    from nothingx.scanner import Scanner
    devs = Scanner.find_all_nothing()
    if not devs:
        print("error: no paired Nothing / Ear / CMF devices found.", file=sys.stderr)
        sys.exit(1)

    selected = Scanner.get_selected()
    selected_mac = selected["mac"] if selected else None

    if len(devs) == 1:
        d = devs[0]
        Scanner.set_selected(d)
        print(f"✓ Default device set to: {d['name']} ({d['mac']})")
        return

    current_idx = 0
    if selected_mac:
        for idx, d in enumerate(devs):
            if d["mac"] == selected_mac:
                current_idx = idx
                break

    if not sys.stdin.isatty():
        print("Paired Nothing Devices:\n")
        for i, d in enumerate(devs, 1):
            act = " [active]" if d["mac"] == selected_mac else ""
            print(f"  {i}) {d['name']} ({d['mac']}){act}")
        try:
            choice = input(f"\nSelect device (1-{len(devs)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(devs):
                chosen = devs[idx]
                Scanner.set_selected(chosen)
                print(f"✓ Selected device: {chosen['name']} ({chosen['mac']})")
            else:
                print("Invalid selection.")
        except Exception:
            print("Selection cancelled.")
        return

    import termios
    import tty

    def render(idx):
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write("\033[1mSelect Active Nothing Device:\033[0m\n\n")
        for i, d in enumerate(devs):
            is_active = (d["mac"] == selected_mac)
            active_label = " \033[90m(active)\033[0m" if is_active else ""
            if i == idx:
                sys.stdout.write(f"  \033[36m❯ {i + 1}) {d['name']} ({d['mac']})\033[0m{active_label}\n")
            else:
                sys.stdout.write(f"    {i + 1}) {d['name']} ({d['mac']}){active_label}\n")
        sys.stdout.write("\n\033[90mUse ↑/↓ or 1-9 to navigate, Enter to select, q to cancel\033[0m\n")
        sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    chosen = None
    try:
        tty.setraw(fd)
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        
        while True:
            render(current_idx)
            ch = sys.stdin.read(1)
            if ch in ('\r', '\n'):
                chosen = devs[current_idx]
                break
            elif ch in ('q', 'Q', '\x03'):
                break
            elif ch.isdigit():
                num = int(ch)
                if 1 <= num <= len(devs):
                    current_idx = num - 1
            elif ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        current_idx = (current_idx - 1) % len(devs)
                    elif ch3 == 'B':
                        current_idx = (current_idx + 1) % len(devs)
            elif ch in ('k', 'K'):
                current_idx = (current_idx - 1) % len(devs)
            elif ch in ('j', 'J'):
                current_idx = (current_idx + 1) % len(devs)
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)

    sys.stdout.write("\033[H\033[J")
    if chosen:
        Scanner.set_selected(chosen)
        print(f"\033[32m✓ Active device set to:\033[0m \033[1m{chosen['name']}\033[0m ({chosen['mac']})")
    else:
        print("Selection cancelled.")


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.help or not args.cmd:
        print(HELP)
        sys.exit(0)

    if args.cmd == "select":
        select_device_interactive()
        sys.exit(0)

    if args.cmd == "devices":
        list_devices()
        sys.exit(0)

    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level, format="%(name)s: %(message)s")

    try:
        ear = Device.discover(target=args.device)
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
