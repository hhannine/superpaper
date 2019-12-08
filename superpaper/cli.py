"""CLI for Superpaper. --help switch prints usage."""
import argparse
import logging
import os
import sys

import superpaper.sp_logging as sp_logging
from superpaper.data import CLIProfileData
import superpaper.wallpaper_processing as wpproc
from superpaper.wallpaper_processing import get_display_data, change_wallpaper_job
from superpaper.tray import tray_loop


def cli_logic():
    """
    CLI command parsing and acting.

    Allows setting a wallpaper using Superpaper features without running the full application.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--setimages", nargs='*',
                        help="List of images to set as wallpaper, \
starting from the left most monitor. \
If a single image is given, it is spanned \
across all monitors.")
    parser.add_argument("-p", "--ppi", nargs='*', type=float,
                        help="List of monitor PPIs. \
Only relevant for a spanned wallpaper.")
    parser.add_argument("-i", "--inches", nargs='*', type=float,
                        help="List of monitor diagonals in inches for PPIs. \
Only relevant for a spanned wallpaper.")
    parser.add_argument("-b", "--bezels", nargs='*', type=float,
                        help="List of monitor bezels in millimeters for \
bezel correction to spanned wallpapers. \
N.B. Needs either --ppi or --inches!")
    parser.add_argument("-o", "--offsets", nargs='*',
                        help="List of wallpaper offsets. \
Should only be necessary with single spanned image.")
    parser.add_argument("-c", "--command", nargs='*',
                        help="Custom command to set the wallpaper. \
Substitute /path/to/image.jpg by '{image}'. \
Must be in quotes.")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Run the full application with debugging.")
    args = parser.parse_args()

    if args.debug:
        sp_logging.DEBUG = True
        sp_logging.G_LOGGER.setLevel(logging.INFO)
        # Install exception handler
        # sys.excepthook = custom_exception_handler
        sp_logging.CONSOLE_HANDLER = logging.StreamHandler()
        sp_logging.G_LOGGER.addHandler(sp_logging.CONSOLE_HANDLER)
        sp_logging.G_LOGGER.info(args.setimages)
        sp_logging.G_LOGGER.info(args.ppi)
        sp_logging.G_LOGGER.info(args.inches)
        sp_logging.G_LOGGER.info(args.bezels)
        sp_logging.G_LOGGER.info(args.offsets)
        sp_logging.G_LOGGER.info(args.command)
        sp_logging.G_LOGGER.info(args.debug)
    if args.debug and len(sys.argv) == 2:
        tray_loop()
    else:
        if not args.setimages:
            sp_logging.G_LOGGER.info("Exception: You must pass image(s) to set as \
wallpaper with '-s' or '--setimages'. Exiting.")
            exit()
        else:
            for filename in args.setimages:
                if not os.path.isfile(filename):
                    sp_logging.G_LOGGER.error("Exception: One of the passed images was not \
a file: (%s). Exiting.", filename)
                    exit()
        if args.bezels and not (args.ppi or args.inches):
            sp_logging.G_LOGGER.info("The bezel correction feature needs display PPIs, \
provide these with --inches or --ppi.")
        if args.offsets and len(args.offsets) % 2 != 0:
            sp_logging.G_LOGGER.error("Exception: Number of offset pixels not even. \
If passing manual offsets, give width and height offset for each display, even if \
not actually offsetting every display. Exiting.")
            exit()
        if args.command:
            if len(args.command) > 1:
                sp_logging.G_LOGGER.error("Exception: Remember to put the \
custom command in quotes. Exiting.")
                exit()
            wpproc.G_SET_COMMAND_STRING = args.command[0]

        get_display_data()
        profile = CLIProfileData(args.setimages,
                                 args.ppi,
                                 args.inches,
                                 args.bezels,
                                 args.offsets,
                                )
        job_thread = change_wallpaper_job(profile)
        job_thread.join()
