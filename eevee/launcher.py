"""Eevee launcher with auto-restart ability.

Command:
    ``eevee``

Options:
    -r, --no-restart   Disable auto-restart.
    --debug            Enable debug mode.

Exit codes:
    ===== ======== ===========
    Value Name     Description
    ===== ======== ===========
    0     SHUTDOWN Close down laucher.
    1     CRITICAL Inform of crash and attempt restart by default.
    26    RESTART  Restart Meowth.
    ===== ======== ===========
"""

import argparse
import subprocess
import sys
import time

def parse_cli_args():

    # create parser
    parser = argparse.ArgumentParser(
        description="Eevee - Pokemon Go Bot for Discord")

    # restart disable option
    parser.add_argument(
        "--no-restart", "-r",
        help="Disables auto-restart.", action="store_true")

    # debug enable option
    parser.add_argument(
        "--debug", "-d", help="Enabled debug mode.", action="store_true")

    # parse and return all provided args
    return parser.parse_known_args()

def main():

    # show intro banner
    print("==================================\n"
          "Eevee - Pokemon Go Bot for Discord\n"
          "==================================\n")

    # check if Python version is within requirements
    if sys.version_info < (3, 6, 1):
        print("ERROR: Minimum Python version not met.\n"
              "Eevee requires Python 3.6.1 or higher.\n")
        return

    # parse arguments provided and sort between launcher and unknown args
    launch_args, eevee_args = parse_cli_args()

    # forward the debug flag to the bot args
    if launch_args.debug:
        eevee_args.append('-d')

    # add the launcher flag to the bot args so it enabled restarting
    eevee_args.append('-l')

    # start tracking how many retries occurred launching the bot
    retries = 0

    # show the bot is launching
    print("Launching Eevee...", end=' ', flush=True)

    while True:

        # call the bot with it's args, and return the exit code
        code = subprocess.call(["eevee-bot", *eevee_args])

        # if clean shutdown
        if code == 0:
            print("Eevee, goodbye!")
            break

        # if restart request
        elif code == 26:
            print("Rebooting! I'll be back in a bit!\n")

            # tell bot that we're coming back from a restart
            if '--fromrestart' not in eevee_args:
                eevee_args.append('--fromrestart')

            continue

        # if closed due to error
        else:

            # don't retry if specified not to on launch
            if launch_args.no_restart:
                break

            # increase retry counter
            retries += 1

            # calculate wait time with retry count squared, max 10 minutes
            wait_time = min([retries**2, 600])

            # show crash occured in console
            print("I crashed!")
            print("Restarting in...", end='\r', flush=True)

            try:
                # each second, update restart counter in console
                for i in range(wait_time, 0, -1):

                    # if less than a minute, display only seconds
                    if i < 60:
                        print(f"Restarting in {i:0d} seconds.            ",
                              end='\r', flush=True)

                    # if over a minute, display both mins and secs
                    else:
                        m, s = divmod(i, 60)
                        print(f"Restarting in {m:0d} mins {s:0d} secs.",
                              end='\r', flush=True)

                    # wait a second before updating countdown again
                    time.sleep(1)

                # show restart attempt at end of countdown
                print("                                        ",
                      end='\r', flush=True)
                print("Restarting now.",
                      end=' ', flush=True)

            # allow user to interrupt countdown and continue loop immediately
            except KeyboardInterrupt:
                print("                                        ",
                      end='\r', flush=True)
                print("Restarting immediately.",
                      end=' ', flush=True)

            # remove restart flag from any previous attempts
            try:
                eevee_args.remove('--fromrestart')
            except ValueError:
                pass

    # when not restarting, show exit code and exit fully
    print("Exit code: {exit_code}".format(exit_code=code))
    sys.exit(code)

if __name__ == '__main__':
    main()
