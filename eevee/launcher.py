import sys
import argparse
import subprocess

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Eevee - Pokemon Go Bot for Discord")
    parser.add_argument(
        "--no-restart", "-r",
        help="Disables auto-restart.", action="store_true")
    parser.add_argument(
        "--debug", "-d", help="Enabled debug mode.", action="store_true")
    return parser.parse_known_args()

def main():
    """Launch Eevee via subprocess, passing args onto it and wait for exit.

    CLI Launch Arguments
            ``--no-restart | -r``

            Disable auto-restart. 

            ``--debug``

            Enable debug mode. 

    Exit codes::

        0 (SHUTDOWN): Close down laucher.
        1 (CRITICAL): Inform of crash and attempt restart by default.
        26 (RESTART): Restart Meowth.
    """

    print("==================================\n"
          "Eevee - Pokemon Go Bot for Discord\n"
          "==================================\n")

    if sys.version_info < (3, 6, 1):
        print("ERROR: Minimum Python version not met.\n"
              "Eevee requires Python 3.6.1 or higher.\n")
        return

    print("Launching Eevee...", end=' ', flush=True)

    launch_args, meowth_args = parse_cli_args()

    if launch_args.debug:
        meowth_args.append('-d')

    meowth_args.append('-l')

    while True:
        code = subprocess.call(["eevee-bot", *meowth_args])
        if code == 0:
            print("Eevee, goodbye!")
            break
        elif code == 26:
            print("Rebooting! I'll be back in a bit!\n")
            continue
        else:
            if launch_args.no_restart:
                break
            print("I crashed! Trying to restart...\n")
    print("Exit code: {exit_code}".format(exit_code=code))
    sys.exit(code)
