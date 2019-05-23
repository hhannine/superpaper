#!/usr/bin/env python3

import os
import platform
import subprocess
import math
import random
import sys
import argparse
import logging
from time import sleep
from pathlib import Path
from operator import itemgetter
from threading import Timer, Lock, Thread

from PIL import Image
from screeninfo import get_monitors
try:
    import wx
    import wx.adv
except BaseException:
    pass
if platform.system() == "Windows":
    import ctypes
elif platform.system() == "Linux":
    # KDE has special needs
    if os.environ.get("DESKTOP_SESSION") == "/usr/share/xsessions/plasma":
        import dbus


# Global variables

# list of display resolutions (width,height), use tuples.
RESOLUTION_ARRAY = []
# list of display offsets (width,height), use tuples.
DISPLAY_OFFSET_ARRAY = []

DEBUG = False
VERBOSE = False
LOGGING = False
g_logger = logging.getLogger()
nDisplays = 0
canvasSize = [0, 0]
# Set path to binary / script
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    # PATH = sys._MEIPASS
    PATH = os.path.dirname(os.path.realpath(sys.executable))
else:
    PATH = os.path.dirname(os.path.realpath(__file__))
# Derivative paths
TEMP_PATH = PATH + "/temp/"
if not os.path.isdir(TEMP_PATH):
    os.mkdir(TEMP_PATH)
PROFILES_PATH = PATH + "/profiles/"
TRAY_TOOLTIP = "Superpaper"
TRAY_ICON = PATH + "/resources/default.png"
VERSION_STRING = "1.1.2"
G_SET_COMMAND_STRING = ""
G_WALLPAPER_CHANGE_LOCK = Lock()
G_SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp")

if DEBUG and not LOGGING:
    g_logger.setLevel(logging.INFO)
    consoleHandler = logging.StreamHandler()
    g_logger.addHandler(consoleHandler)

if LOGGING:
    DEBUG = True
    # sys.stdout = open(PATH + "/log.txt", "w")
    g_logger.setLevel(logging.INFO)
    fileHandler = logging.FileHandler("{0}/{1}.log".format(PATH, "log"),
                                      mode="w")
    g_logger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler()
    g_logger.addHandler(consoleHandler)

def custom_exception_handler(exceptiontype, value, tb_var):
    """Log uncaught exceptions."""
    g_logger.exception("Uncaught exceptionn type: %s", str(exceptiontype))
    g_logger.exception("Exception: %s",str(value))
    g_logger.exception(str(tb_var))
    # g_logger.exception("Uncaught exception.")

def show_message_dialog(message, msg_type="Info"):
    """General purpose info dialog in GUI mode."""
    # Type can be 'Info', 'Error', 'Question', 'Exclamation'
    if "wx" in sys.modules:
        dial = wx.MessageDialog(None, message, msg_type, wx.OK)
        dial.ShowModal()
    else:
        pass

class GeneralSettingsData(object):
    def __init__(self):
        self.logging = False
        self.use_hotkeys = True
        self.hkBinding_next = None
        self.hkBinding_pause = None
        self.set_command = ""
        self.show_help = True
        self.parse_settings()

    def parse_settings(self):
        global DEBUG, LOGGING, G_SET_COMMAND_STRING
        global g_logger, fileHandler, consoleHandler
        fname = os.path.join(PATH, "general_settings")
        if os.path.isfile(fname):
            f = open(fname, "r")
            try:
                for line in f:
                    line.strip()
                    words = line.split("=")
                    if words[0] == "logging":
                        wrds1 = words[1].strip().lower()
                        if wrds1 == "true":
                            self.logging = True
                            LOGGING = True
                            DEBUG = True
                            g_logger = logging.getLogger()
                            g_logger.setLevel(logging.INFO)
                            # Install exception handler
                            sys.excepthook = custom_exception_handler
                            fileHandler = logging.FileHandler(
                                "{0}/{1}.log"
                                .format(PATH, "log"),
                                mode="w")
                            g_logger.addHandler(fileHandler)
                            consoleHandler = logging.StreamHandler()
                            g_logger.addHandler(consoleHandler)
                            g_logger.info("Enabled logging to file.")
                    elif words[0] == "use hotkeys":
                        wrds1 = words[1].strip().lower()
                        if wrds1 == "true":
                            self.use_hotkeys = True
                        else:
                            self.use_hotkeys = False
                        if DEBUG:
                            g_logger.info("use_hotkeys: {}"
                                          .format(self.use_hotkeys))
                    elif words[0] == "next wallpaper hotkey":
                        try:
                            binding_strings = words[1].strip().split("+")
                        except:
                            pass
                        if binding_strings:
                            self.hkBinding_next = tuple(binding_strings)
                        if DEBUG:
                            g_logger.info("hkBinding_next: {}"
                                          .format(self.hkBinding_next))
                    elif words[0] == "pause wallpaper hotkey":
                        try:
                            binding_strings = words[1].strip().split("+")
                        except:
                            pass
                        if binding_strings:
                            self.hkBinding_pause = tuple(binding_strings)
                        if DEBUG:
                            g_logger.info("hkBinding_pause: {}"
                                          .format(self.hkBinding_pause))
                    elif words[0] == "set_command":
                        G_SET_COMMAND_STRING = words[1].strip()
                        self.set_command = G_SET_COMMAND_STRING
                    elif words[0].strip() == "show_help_at_start":
                        show_state = words[1].strip().lower()
                        if show_state == "false":
                            self.show_help = False
                        else:
                            pass
                    else:
                        g_logger.info("Exception: Unkown general setting: {}"
                                      .format(words[0]))
            finally:
                f.close()
        else:
            # if file does not exist, create it and write default values.
            f = open(fname, "x")
            f.write("logging=false\n")
            f.write("use hotkeys=true\n")
            f.write("next wallpaper hotkey=control+super+w\n")
            self.hkBinding_next = ("control", "super", "w")
            f.write("pause wallpaper hotkey=control+super+shift+p\n")
            self.hkBinding_pause = ("control", "super", "shift", "p")
            f.write("set_command=")
            f.close()

    def Save(self):
        fname = os.path.join(PATH, "general_settings")
        f = open(fname, "w")

        if self.logging:
            f.write("logging=true\n")
        else:
            f.write("logging=false\n")

        if self.use_hotkeys:
            f.write("use hotkeys=true\n")
        else:
            f.write("use hotkeys=false\n")

        if self.hkBinding_next:
            hk_string = "+".join(self.hkBinding_next)
            f.write("next wallpaper hotkey={}\n".format(hk_string))

        if self.hkBinding_pause:
            hk_string_p = "+".join(self.hkBinding_pause)
            f.write("pause wallpaper hotkey={}\n".format(hk_string_p))

        if self.show_help:
            f.write("show_help_at_start=true\n")
        else:
            f.write("show_help_at_start=false\n")

        f.write("set_command={}".format(self.set_command))

        f.close()





class ProfileData(object):
    def __init__(self, file):
        self.name = "default_profile"
        self.spanmode = "single"  # single / multi
        self.slideshow = True
        self.delayArray = [600]
        self.sortmode = "shuffle"  # shuffle ( random , sorted? )
        self.ppimode = False
        self.ppiArray = nDisplays * [100]
        self.ppiArrayRelDensity = []
        self.inches = []
        self.manual_offsets = nDisplays * [(0, 0)]
        self.manual_offsets_useronly = []
        self.bezels = []
        self.bezel_px_offsets = []
        self.hkBinding = None
        self.pathsArray = []

        self.parseProfile(file)
        if self.ppimode is True:
            self.computeRelativeDensities()
            if self.bezels:
                self.computeBezelPixelOffsets()
        self.file_handler = self.Filehandler(self.pathsArray, self.sortmode)

    def parseProfile(self, file):
        f = open(file, "r")
        try:
            for line in f:
                line.strip()
                words = line.split("=")
                if words[0] == "name":
                    self.name = words[1].strip()
                elif words[0] == "spanmode":
                    wrd1 = words[1].strip().lower()
                    if wrd1 == "single":
                        self.spanmode = wrd1
                    elif wrd1 == "multi":
                        self.spanmode = wrd1
                    else:
                        g_logger.info("Exception: unknown spanmode: {} \
                                in profile: {}".format(words[1], self.name))
                elif words[0] == "slideshow":
                    wrd1 = words[1].strip().lower()
                    if wrd1 == "true":
                        self.slideshow = True
                    else:
                        self.slideshow = False
                elif words[0] == "delay":
                    self.delayArray = []
                    delayStrings = words[1].strip().split(";")
                    for str in delayStrings:
                        self.delayArray.append(int(str))
                elif words[0] == "sortmode":
                    wrd1 = words[1].strip().lower()
                    if wrd1 == "shuffle":
                        self.sortmode = wrd1
                    elif wrd1 == "sort":
                        self.sortmode = wrd1
                    else:
                        g_logger.info("Exception: unknown sortmode: {} \
                                in profile: {}".format(words[1], self.name))
                elif words[0] == "offsets":
                    # Use PPI mode algorithm to do cuts.
                    # Defaults assume uniform pixel density
                    # if no custom values are given.
                    self.ppimode = True
                    self.manual_offsets = []
                    self.manual_offsets_useronly = []
                    # w1,h1;w2,h2;...
                    offsetStrings = words[1].strip().split(";")
                    for str in offsetStrings:
                        res_str = str.split(",")
                        self.manual_offsets.append((int(res_str[0]),
                                                    int(res_str[1])))
                        self.manual_offsets_useronly.append((int(res_str[0]),
                                                             int(res_str[1])))
                elif words[0] == "bezels":
                    bezelMillimeter_Strings = words[1].strip().split(";")
                    for str in bezelMillimeter_Strings:
                        self.bezels.append(float(str))
                elif words[0] == "ppi":
                    self.ppimode = True
                    # overwrite initialized arrays.
                    self.ppiArray = []
                    self.ppiArrayRelDensity = []
                    ppiStrings = words[1].strip().split(";")
                    for str in ppiStrings:
                        self.ppiArray.append(int(str))
                elif words[0] == "diagonal_inches":
                    self.ppimode = True
                    # overwrite initialized arrays.
                    self.ppiArray = []
                    self.ppiArrayRelDensity = []
                    inchStrings = words[1].strip().split(";")
                    self.inches = []
                    for str in inchStrings:
                        self.inches.append(float(str))
                    self.ppiArray = self.computePPIs(self.inches)
                elif words[0] == "hotkey":
                    binding_strings = words[1].strip().split("+")
                    self.hkBinding = tuple(binding_strings)
                    if DEBUG:
                        g_logger.info("hkBinding:{}".format(self.hkBinding))
                elif words[0].startswith("display"):
                    paths = words[1].strip().split(";")
                    paths = list(filter(None, paths))  # drop empty strings
                    self.pathsArray.append(paths)
                else:
                    g_logger.info("Unknown setting line in config: {}".format(line))
        finally:
            f.close()

    def computePPIs(self, inches):
        if len(inches) < nDisplays:
            g_logger.info("Exception: Number of read display diagonals was: "
                          + str(len(inches))
                          + ", but the number of displays was found to be: "
                          + str(nDisplays))
            g_logger.info("Falling back to no PPI correction.")
            self.ppimode = False
            return nDisplays * [100]
        else:
            ppiArray = []
            for inch, res in zip(inches, RESOLUTION_ARRAY):
                diagonal_px = math.sqrt(res[0]**2 + res[1]**2)
                px_per_inch = diagonal_px / inch
                ppiArray.append(px_per_inch)
            if DEBUG:
                g_logger.info("Computed PPIs: {}".format(ppiArray))
            return ppiArray

    def computeRelativeDensities(self):
        max_density = max(self.ppiArray)
        for ppi in self.ppiArray:
            self.ppiArrayRelDensity.append((1 / max_density) * float(ppi))
        if DEBUG:
            g_logger.info("relative pixel densities: {}".format(self.ppiArrayRelDensity))

    def computeBezelPixelOffsets(self):
        inch_per_mm = 1.0 / 25.4
        for bez_mm, ppi in zip(self.bezels, self.ppiArray):
            self.bezel_px_offsets.append(
                round(float(ppi) * inch_per_mm * bez_mm))
        if DEBUG:
            g_logger.info(
                "Bezel px calculation: initial manual offset: {}, \
                and bezel pixels: {}".format(self.manual_offsets,
                                             self.bezel_px_offsets))
        # Add these horizontal offsets to manual_offsets:
        # Avoid offsetting the leftmost anchored display i==0
        # -1 since last display doesn't have a next display.
        for i in range(len(self.bezel_px_offsets) - 1):
            self.manual_offsets[i + 1] = (self.manual_offsets[i + 1][0] +
                                          self.bezel_px_offsets[i + 1] +
                                          self.bezel_px_offsets[i],
                                          self.manual_offsets[i + 1][1])
        if DEBUG:
            g_logger.info(
                "Bezel px calculation: resulting combined manual offset: {}"
                .format(self.manual_offsets))

    def NextWallpaperFiles(self):
        return self.file_handler.Next_Wallpaper_Files()

    class Filehandler(object):
        def __init__(self, pathsArray, sortmode):
            # A list of lists if there is more than one monitor with distinct
            # input paths.
            self.all_files_in_paths = []
            self.pathsArray = pathsArray
            self.sortmode = sortmode
            for paths_list in pathsArray:
                list_of_images = []
                for path in paths_list:
                    # Add list items to the end of the list instead of
                    # appending the list to the list.
                    if not os.path.exists(path):
                        message = "A path was not found: '{}'.\n\
Use absolute paths for best reliabilty.".format(path)
                        g_logger.info(message)
                        show_message_dialog(message, "Error")
                        continue
                    else:
                        # List only images that are of supported type.
                        list_of_images += [os.path.join(path, f)
                                           for f in os.listdir(path)
                                           if f.endswith(G_SUPPORTED_IMAGE_EXTENSIONS)
                                          ]
                # Append the list of monitor_i specific files to the list of
                # lists of images.
                self.all_files_in_paths.append(list_of_images)
            self.iterators = []
            for diplay_image_list in self.all_files_in_paths:
                self.iterators.append(
                    self.ImageList(
                        diplay_image_list,
                        self.sortmode))

        def Next_Wallpaper_Files(self):
            files = []
            for iter in self.iterators:
                next_image = iter.__next__()
                if os.path.isfile(next_image):
                    files.append(next_image)
                else:
                    # reload all files by initializing
                    if DEBUG:
                        g_logger.info("Ran into an invalid file, reinitializing..")
                    self.__init__(self.pathsArray, self.sortmode)
                    files = self.Next_Wallpaper_Files()
                    break
            return files

        class ImageList:
            def __init__(self, filelist, sortmode):
                self.counter = 0
                self.files = filelist
                self.sortmode = sortmode
                self.ArrangeList()

            def __iter__(self):
                return self

            def __next__(self):
                if self.counter < len(self.files):
                    image = self.files[self.counter]
                    self.counter += 1
                    return image
                else:
                    self.counter = 0
                    self.ArrangeList()
                    image = self.files[self.counter]
                    self.counter += 1
                    return image

            def ArrangeList(self):
                if self.sortmode == "shuffle":
                    if DEBUG and VERBOSE:
                        g_logger.info("Shuffling files: {}".format(self.files))
                    random.shuffle(self.files)
                    if DEBUG and VERBOSE:
                        g_logger.info("Shuffled files: {}".format(self.files))
                elif self.sortmode == "alphabetical":
                    self.files.sort()
                    if DEBUG and VERBOSE:
                        g_logger.info("Sorted files: {}".format(self.files))
                else:
                    g_logger.info(
                        "ImageList.ArrangeList: unknown sortmode: {}"
                        .format(self.sortmode))


class CLIProfileData(ProfileData):

    def __init__(self, files, ppiarr, inches, bezels, offsets):
        self.name = "cli"
        self.spanmode = ""  # single / multi
        if len(files) == 1:
            self.spanmode = "single"
        else:
            self.spanmode = "multi"

        self.ppimode = None
        if ppiarr is None and inches is None:
            self.ppimode = False
            self.ppiArray = nDisplays * [100]
        else:
            self.ppimode = True
            if inches:
                self.ppiArray = self.computePPIs(inches)
            else:
                self.ppiArray = ppiarr

        if offsets is None:
            self.manual_offsets = nDisplays * [(0, 0)]
        else:
            self.manual_offsets = nDisplays * [(0, 0)]
            off_pairs_zip = zip(*[iter(offsets)]*2)
            off_pairs = [tuple(p) for p in off_pairs_zip]
            for off, i in zip(off_pairs, range(len(self.manual_offsets))):
                self.manual_offsets[i] = off
            # print(self.manual_offsets)
            for pair in self.manual_offsets:
                self.manual_offsets[self.manual_offsets.index(pair)] = (int(pair[0]), int(pair[1]))
            # print(self.manual_offsets)

        self.ppiArrayRelDensity = []
        self.bezels = bezels
        self.bezel_px_offsets = []
        #self.files = files
        self.files = []
        for item in files:
            self.files.append(os.path.realpath(item))
        #
        if self.ppimode is True:
            self.computeRelativeDensities()
            if self.bezels:
                self.computeBezelPixelOffsets()

    def NextWallpaperFiles(self):
        return self.files

class TempProfileData(object):
    def __init__(self):
        self.name = None
        self.spanmode = None
        self.slideshow = None
        self.delay = None
        self.sortmode = None
        # self.ppiArray = None
        self.inches = None
        self.manual_offsets = None
        self.bezels = None
        self.hkBinding = None
        self.pathsArray = []

    def Save(self):
        if self.name is not None:
            fname = PROFILES_PATH + self.name + ".profile"
            try:
                f = open(fname, "w")
            except:
                msg = "Cannot write to file {}".format(fname)
                show_message_dialog(msg, "Error")
                return None
            f.write("name=" + str(self.name) + "\n")
            if self.spanmode:
                f.write("spanmode=" + str(self.spanmode) + "\n")
            if self.slideshow is not None:
                f.write("slideshow=" + str(self.slideshow) + "\n")
            if self.delay:
                f.write("delay=" + str(self.delay) + "\n")
            if self.sortmode:
                f.write("sortmode=" + str(self.sortmode) + "\n")
            # f.write("ppi=" + str(self.ppiArray) + "\n")
            if self.inches:
                f.write("diagonal_inches=" + str(self.inches) + "\n")
            if self.manual_offsets:
                f.write("offsets=" + str(self.manual_offsets) + "\n")
            if self.bezels:
                f.write("bezels=" + str(self.bezels) + "\n")
            if self.hkBinding:
                f.write("hotkey=" + str(self.hkBinding) + "\n")
            if self.pathsArray:
                for paths in self.pathsArray:
                    # paths_formatted = ";".join(paths)
                    f.write("display" + str(self.pathsArray.index(paths)) + "paths=" + paths + "\n")

            f.close()
            return fname
        else:
            print("tmp.Save(): name is not set.")
            return None

    def TestSave(self):
        valid_profile = False
        if self.name is not None and self.name.strip() is not "":
            fname = PROFILES_PATH + self.name + ".deleteme"
            try:
                f = open(fname, "w")
                f.close()
                os.remove(fname)
            except:
                msg = "Cannot write to file {}".format(fname)
                show_message_dialog(msg, "Error")
                return False
            if self.spanmode == "single":
                if len(self.pathsArray) > 1:
                    msg = "When spanning a single image across all monitors, only one paths field is needed."
                    show_message_dialog(msg, "Error")
                    return False
            if self.spanmode == "multi":
                if len(self.pathsArray) < 2:
                    msg = "When setting a different image on every display, each display needs its own paths field."
                    show_message_dialog(msg, "Error")
                    return False
            if self.slideshow is True and not self.delay:
                msg = "When using slideshow you need to enter a delay."
                show_message_dialog(msg, "Info")
                return False
            if self.delay:
                try:
                    val = int(self.delay)
                    if val < 20:
                        msg = "It is advisable to set the slideshow delay to be at least 20 seconds due to the time the image processing takes."
                        show_message_dialog(msg, "Info")
                        return False
                except ValueError:
                    msg = "Slideshow delay must be an integer of seconds."
                    show_message_dialog(msg, "Error")
                    return False
            # if self.sortmode:
                # No test needed
            if self.inches:
                if self.is_list_float(self.inches):
                    pass
                else:
                    msg = "Display diagonals must be given in numeric values using decimal point and separated by semicolon ';'."
                    show_message_dialog(msg, "Error")
                    return False
            if self.manual_offsets:
                if self.is_list_offsets(self.manual_offsets):
                    pass
                else:
                    msg = "Display offsets must be given in width,height pixel pairs and separated by semicolon ';'."
                    show_message_dialog(msg, "Error")
                    return False
            if self.bezels:
                if self.is_list_float(self.bezels):
                    if self.manual_offsets:
                        if len(self.manual_offsets.split(";")) < len(self.bezels.split(";")):
                            msg = "When using both offset and bezel corrections, take care to enter an offset for each display that you enter a bezel thickness."
                            show_message_dialog(msg, "Error")
                            return False
                        else:
                            pass
                    else:
                        pass
                else:
                    msg = "Display bezels must be given in millimeters using decimal point and separated by semicolon ';'."
                    show_message_dialog(msg, "Error")
                    return False
            if self.hkBinding:
                if self.is_valid_hotkey(self.hkBinding):
                    pass
                else:
                    msg = "Hotkey must be given as 'mod1+mod2+mod3+key'. Valid modifiers are 'control', 'super', 'alt', 'shift'."
                    show_message_dialog(msg, "Error")
                    return False
            if self.pathsArray:
                if self.is_list_valid_paths(self.pathsArray):
                    pass
                else:
                    # msg = "Paths must be separated by a semicolon ';'."
                    # show_message_dialog(msg, "Error")
                    return False
            else:
                msg = "You must enter at least one path for images."
                show_message_dialog(msg, "Error")
                return False
            # Passed all tests.
            valid_profile = True
            return valid_profile
        else:
            print("tmp.Save(): name is not set.")
            msg = "You must enter a name for the profile."
            show_message_dialog(msg, "Error")
            return False

    def is_list_float(self, input):
        is_floats = True
        list_input = input.split(";")
        for item in list_input:
            try:
                val = float(item)
            except ValueError:
                return False
        return is_floats

    def is_list_offsets(self, input):
        list_input = input.split(";")
        # if len(list_input) < nDisplays:
        #     msg = "Enter an offset for every display, even if it is (0,0)."
        #     show_message_dialog(msg, "Error")
        #     return False
        try:
            for off_pair in list_input:
                offset = off_pair.split(",")
                if len(offset) > 2:
                    return False
                try:
                    val_w = int(offset[0])
                    val_h = int(offset[1])
                except ValueError:
                    return False
        except:
            return False
        # Passed tests.
        return True

    def is_valid_hotkey(self, input):
        # Validity is hard to properly verify here.
        # Instead do it when registering hotkeys at startup.
        is_hk = True
        return is_hk

    def is_list_valid_paths(self, input):
        if input == [""]:
            msg = "At least one path for wallpapers must be given."
            show_message_dialog(msg, "Error")
            return False
        if "" in input:
            msg = "Take care not to save a profile with an empty display paths field."
            show_message_dialog(msg, "Error")
            return False
        for path_list_str in input:
            path_list = path_list_str.split(";")
            for path in path_list:
                if os.path.isdir(path) is True:
                    supported_files = [f for f in os.listdir(path)
                                       if f.endswith(G_SUPPORTED_IMAGE_EXTENSIONS)]
                    if supported_files:
                        continue
                    else:
                        msg = "Path '{}' does not contain supported image files.".format(path)
                        show_message_dialog(msg, "Error")
                        return False
                else:
                    msg = "Path '{}' was not recognized as a directory.".format(path)
                    show_message_dialog(msg, "Error")
                    return False
        valid_pathsarray = True
        return valid_pathsarray



class RepeatedTimer(object):
    # Credit:
    # https://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds/13151299#13151299
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def getDisplayData():
    # https://github.com/rr-/screeninfo
    global nDisplays, RESOLUTION_ARRAY, DISPLAY_OFFSET_ARRAY
    RESOLUTION_ARRAY = []
    DISPLAY_OFFSET_ARRAY = []
    monitors = get_monitors()
    nDisplays = len(monitors)
    for m_index in range(len(monitors)):
        res = []
        offset = []
        res.append(monitors[m_index].width)
        res.append(monitors[m_index].height)
        offset.append(monitors[m_index].x)
        offset.append(monitors[m_index].y)
        RESOLUTION_ARRAY.append(tuple(res))
        DISPLAY_OFFSET_ARRAY.append(tuple(offset))
    # Check that the display offsets are sane, i.e. translate the values if
    # there are any negative values (Windows).
    # Top-most edge of the crop tuples.
    leftmost_offset = min(DISPLAY_OFFSET_ARRAY, key=itemgetter(0))[0]
    topmost_offset = min(DISPLAY_OFFSET_ARRAY, key=itemgetter(1))[1]
    if leftmost_offset < 0 or topmost_offset < 0:
        if DEBUG:
            g_logger.info("Negative display offset: {}".format(DISPLAY_OFFSET_ARRAY))
        translate_offsets = []
        for offset in DISPLAY_OFFSET_ARRAY:
            translate_offsets.append((offset[0] - leftmost_offset, offset[1] - topmost_offset))
        DISPLAY_OFFSET_ARRAY = translate_offsets
        if DEBUG:
            g_logger.info("Sanitised display offset: {}".format(DISPLAY_OFFSET_ARRAY))
    if DEBUG:
        g_logger.info(
            "getDisplayData output: nDisplays = {}, {}, {}"
            .format(
                nDisplays,
                RESOLUTION_ARRAY,
                DISPLAY_OFFSET_ARRAY))
    # Sort displays left to right according to offset data
    display_indices = list(range(len(DISPLAY_OFFSET_ARRAY)))
    display_indices.sort(key=DISPLAY_OFFSET_ARRAY.__getitem__)
    DISPLAY_OFFSET_ARRAY = list(map(DISPLAY_OFFSET_ARRAY.__getitem__, display_indices))
    RESOLUTION_ARRAY = list(map(RESOLUTION_ARRAY.__getitem__, display_indices))
    if DEBUG:
        g_logger.info(
            "SORTED getDisplayData output: nDisplays = {}, {}, {}"
            .format(
                nDisplays,
                RESOLUTION_ARRAY,
                DISPLAY_OFFSET_ARRAY))


def computeCanvas(res_array, offset_array):
    # Take the subtractions of right-most right - left-most left
    # and bottom-most bottom - top-most top (=0).
    leftmost = 0
    topmost = 0
    right_edges = []
    bottom_edges = []
    for res, off in zip(res_array, offset_array):
        right_edges.append(off[0]+res[0])
        bottom_edges.append(off[1]+res[1])
    # Right-most edge.
    rightmost = max(right_edges)
    # Bottom-most edge.
    bottommost = max(bottom_edges)
    canvasSize = [rightmost - leftmost, bottommost - topmost]
    if DEBUG:
        g_logger.info("Canvas size: {}".format(canvasSize))
    return canvasSize


def computeRESOLUTION_ARRAYPPIcorrection(res_array, ppiArrayRelDensity):
    eff_RESOLUTION_ARRAY = []
    for i in range(len(res_array)):
        effw = round(res_array[i][0] / ppiArrayRelDensity[i])
        effh = round(res_array[i][1] / ppiArrayRelDensity[i])
        eff_RESOLUTION_ARRAY.append((effw, effh))
    return eff_RESOLUTION_ARRAY


# resize image to fill given rectangle and do a centered crop to size.
# Return output image.
def resizeToFill(img, res):
    imgSize = img.size  # returns image (width,height)
    if imgSize == res:
        # input image is already of the correct size, no action needed.
        return img
    imgRatio = imgSize[0] / imgSize[1]
    trgtRatio = res[0] / res[1]
    # resize along the shorter edge to get an image that is at least of the
    # target size on the shorter edge.
    if imgRatio < trgtRatio:      # img not wide enough / is too tall
        resizeFactor = res[0] / imgSize[0]
        newSize = (
            round(
                resizeFactor *
                imgSize[0]),
            round(
                resizeFactor *
                imgSize[1]))
        img = img.resize(newSize, resample=Image.LANCZOS)
        # crop vertically to target height
        extraH = newSize[1] - res[1]
        if extraH < 0:
            g_logger.info(
                "Error with cropping vertically, resized image \
                wasn't taller than target size.")
            return -1
        if extraH == 0:
            # image is already at right height, no cropping needed.
            return img
        # (left edge, half of extra height from top,
        # right edge, bottom = top + res[1]) : force correct height
        cropTuple = (
            0,
            round(extraH/2),
            newSize[0],
            round(extraH/2) + res[1])
        cropped_res = img.crop(cropTuple)
        if cropped_res.size == res:
            return cropped_res
        else:
            g_logger.info(
                "Error: result image not of correct size. crp:{}, res:{}"
                .format(cropped_res.size, res))
            return -1
    elif imgRatio >= trgtRatio:      # img not tall enough / is too wide
        resizeFactor = res[1] / imgSize[1]
        newSize = (
            round(resizeFactor * imgSize[0]),
            round(resizeFactor * imgSize[1]))
        img = img.resize(newSize, resample=Image.LANCZOS)
        # crop horizontally to target width
        extraW = newSize[0] - res[0]
        if extraW < 0:
            g_logger.info(
                "Error with cropping horizontally, resized image \
                wasn't wider than target size.")
            return -1
        if extraW == 0:
            # image is already at right width, no cropping needed.
            return img
        # (half of extra from left edge, top edge,
        # right = left + desired width, bottom) : force correct width
        cropTuple = (
            round(extraW/2),
            0,
            round(extraW/2) + res[0],
            newSize[1])
        cropped_res = img.crop(cropTuple)
        if cropped_res.size == res:
            return cropped_res
        else:
            g_logger.info(
                "Error: result image not of correct size. crp:{}, res:{}"
                .format(cropped_res.size, res))
            return -1


def get_center(res):
    return (round(res[0] / 2), round(res[1] / 2))


def get_all_centers(resarr_eff, manual_offsets):
    centers = []
    sum_widths = 0
    # get the vertical pixel distance of the center of the left most display
    # from the top.
    center_standard_height = get_center(resarr_eff[0])[1]
    if len(manual_offsets) < len(resarr_eff):
        g_logger.info("get_all_centers: Not enough manual offsets: \
            {} for displays: {}".format(
                len(manual_offsets),
                len(resarr_eff)))
    else:
        for i in range(len(resarr_eff)):
            horiz_radius = get_horizontal_radius(resarr_eff[i])
            # here take the center height to be the same for all the displays
            # unless modified with the manual offset
            center_with_respect_to_AnchorLeftTop = (
                sum_widths + manual_offsets[i][0] + horiz_radius,
                center_standard_height + manual_offsets[i][1])
            centers.append(center_with_respect_to_AnchorLeftTop)
            sum_widths += resarr_eff[i][0]
    if DEBUG:
        g_logger.info("centers: {}".format(centers))
    return centers


def get_lefttop_from_center(center, res):
    return (center[0] - round(res[0] / 2), center[1] - round(res[1] / 2))


def get_rightbottom_from_lefttop(lefttop, res):
    return (lefttop[0] + res[0], lefttop[1] + res[1])


def get_horizontal_radius(res):
    return round(res[0] / 2)


def computeCropTuples(RESOLUTION_ARRAY_eff, manual_offsets):
    # Assume the centers of the physical displays are aligned on common
    # horizontal line. If this is not the case one must use the manual
    # offsets defined in the profile for adjustment (and bezel corrections).
    # Anchor positions to the top left corner of the left most display. If
    # its size is scaled up, one will need to adjust the horizontal positions
    # of all the displays. (This is automatically handled by using the
    # effective resolution array).
    # Additionally one must make sure that the highest point of the display
    # arrangement is at y=0.
    crop_tuples = []
    centers = get_all_centers(RESOLUTION_ARRAY_eff, manual_offsets)
    for center, res in zip(centers, RESOLUTION_ARRAY_eff):
        lefttop = get_lefttop_from_center(center, res)
        rightbottom = get_rightbottom_from_lefttop(lefttop, res)
        crop_tuples.append(lefttop + rightbottom)
    # Translate crops so that the highest point is at y=0 -- remember to add
    # translation to both top and bottom coordinates!
    # Top-most edge of the crop tuples.
    leftmost = min(crop_tuples, key=itemgetter(0))[0]
    # Top-most edge of the crop tuples.
    topmost = min(crop_tuples, key=itemgetter(1))[1]
    if leftmost is 0 and topmost is 0:
        if DEBUG:
            g_logger.info("crop_tuples: {}".format(crop_tuples))
        return crop_tuples  # [(left, up, right, bottom),...]
    else:
        crop_tuples_translated = translate_crops(
            crop_tuples, (leftmost, topmost))
        if DEBUG:
            g_logger.info("crop_tuples_translated: {}".format(crop_tuples_translated))
        return crop_tuples_translated  # [(left, up, right, bottom),...]


def translate_crops(crop_tuples, translateTuple):
    crop_tuples_translated = []
    for crop_tuple in crop_tuples:
        crop_tuples_translated.append(
            (crop_tuple[0] - translateTuple[0],
             crop_tuple[1] - translateTuple[1],
             crop_tuple[2] - translateTuple[0],
             crop_tuple[3] - translateTuple[1]))
    return crop_tuples_translated


def computeWorkingCanvas(crop_tuples):
    # Take the subtractions of right-most right - left-most left
    # and bottom-most bottom - top-most top (=0).
    leftmost = 0
    topmost = 0
    # Right-most edge of the crop tuples.
    rightmost = max(crop_tuples, key=itemgetter(2))[2]
    # Bottom-most edge of the crop tuples.
    bottommost = max(crop_tuples, key=itemgetter(3))[3]
    canvasSize = [rightmost - leftmost, bottommost - topmost]
    return canvasSize


def spanSingleImage(profile):
    file = profile.NextWallpaperFiles()[0]
    if DEBUG:
        g_logger.info(file)
    img = Image.open(file)
    canvasTuple = tuple(computeCanvas(RESOLUTION_ARRAY, DISPLAY_OFFSET_ARRAY))
    img_resize = resizeToFill(img, canvasTuple)
    outputfile = TEMP_PATH + profile.name + "-a.png"
    if os.path.isfile(outputfile):
        outputfile_old = outputfile
        outputfile = TEMP_PATH + profile.name + "-b.png"
    else:
        outputfile_old = TEMP_PATH + profile.name + "-b.png"
    img_resize.save(outputfile, "PNG")
    setWallpaper(outputfile)
    if os.path.exists(outputfile_old):
        os.remove(outputfile_old)
    return 0


# Take pixel densities of displays into account to have the image match
# physically between displays.
def spanSingleImagePPIcorrection(profile):
    file = profile.NextWallpaperFiles()[0]
    if DEBUG:
        g_logger.info(file)
    img = Image.open(file)
    RESOLUTION_ARRAY_eff = computeRESOLUTION_ARRAYPPIcorrection(
        RESOLUTION_ARRAY, profile.ppiArrayRelDensity)

    # Cropping now sections of the image to be shown, USE EFFECTIVE WORKING
    # SIZES. Also EFFECTIVE SIZE Offsets are now required.
    manual_offsets = profile.manual_offsets
    cropped_images = []
    crop_tuples = computeCropTuples(RESOLUTION_ARRAY_eff, manual_offsets)
    # larger working size needed to fill all the normalized lower density
    # displays. Takes account manual offsets that might require extra space.
    canvasTuple_eff = tuple(computeWorkingCanvas(crop_tuples))
    # Image is now the height of the eff tallest display + possible manual
    # offsets and the width of the combined eff widths + possible manual
    # offsets.
    img_workingsize = resizeToFill(img, canvasTuple_eff)
    # Simultaneously make crops at working size and then resize down to actual
    # resolution from RESOLUTION_ARRAY as needed.
    for crop, res in zip(crop_tuples, RESOLUTION_ARRAY):
        crop_img = img_workingsize.crop(crop)
        if crop_img.size == res:
            cropped_images.append(crop_img)
        else:
            crop_img = crop_img.resize(res, resample=Image.LANCZOS)
            cropped_images.append(crop_img)
    # Combine crops to a single canvas of the size of the actual desktop
    # actual combined size of the display resolutions
    canvasTuple_fin = tuple(computeCanvas(RESOLUTION_ARRAY, DISPLAY_OFFSET_ARRAY))
    combinedImage = Image.new("RGB", canvasTuple_fin, color=0)
    combinedImage.load()
    for i in range(len(cropped_images)):
        combinedImage.paste(cropped_images[i], DISPLAY_OFFSET_ARRAY[i])
    # Saving combined image
    outputfile = TEMP_PATH + profile.name + "-a.png"
    if os.path.isfile(outputfile):
        outputfile_old = outputfile
        outputfile = TEMP_PATH + profile.name + "-b.png"
    else:
        outputfile_old = TEMP_PATH + profile.name + "-b.png"
    combinedImage.save(outputfile, "PNG")
    setWallpaper(outputfile)
    if os.path.exists(outputfile_old):
        os.remove(outputfile_old)
    return 0


def setMultipleImages(profile):
    files = profile.NextWallpaperFiles()
    if DEBUG:
        g_logger.info(str(files))
    img_resized = []
    for file, res in zip(files, RESOLUTION_ARRAY):
        image = Image.open(file)
        img_resized.append(resizeToFill(image, res))
    canvasTuple = tuple(computeCanvas(RESOLUTION_ARRAY, DISPLAY_OFFSET_ARRAY))
    combinedImage = Image.new("RGB", canvasTuple, color=0)
    combinedImage.load()
    for i in range(len(files)):
        combinedImage.paste(img_resized[i], DISPLAY_OFFSET_ARRAY[i])
    outputfile = TEMP_PATH + profile.name + "-a.png"
    if os.path.isfile(outputfile):
        outputfile_old = outputfile
        outputfile = TEMP_PATH + profile.name + "-b.png"
    else:
        outputfile_old = TEMP_PATH + profile.name + "-b.png"
    combinedImage.save(outputfile, "PNG")
    setWallpaper(outputfile)
    if os.path.exists(outputfile_old):
        os.remove(outputfile_old)
    return 0


def errcheck(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())


def setWallpaper(outputfile):
    pltform = platform.system()
    if pltform == "Windows":
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 1
        SPIF_SENDCHANGE = 2
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        SystemParametersInfo = user32.SystemParametersInfoW
        SystemParametersInfo.argtypes = [
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint]
        SystemParametersInfo.restype = ctypes.c_int
        SystemParametersInfo.errcheck = errcheck
        SystemParametersInfo(
            SPI_SETDESKWALLPAPER,
            0,
            outputfile,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
    elif pltform == "Linux":
        setWallpaper_linux(outputfile)
    elif pltform == "Darwin":
        SCRIPT = """/usr/bin/osascript<<END
                    tell application "Finder"
                    set desktop picture to POSIX file "%s"
                    end tell
                    END"""
        subprocess.Popen(SCRIPT % outputfile, shell=True)
    else:
        g_logger.info("Unknown platform.system(): {}".format(pltform))


def setWallpaper_linux(outputfile):
    file = "file://" + outputfile
    set_command = G_SET_COMMAND_STRING
    if DEBUG:
        g_logger.info(file)
    # subprocess.run(["gsettings", "set", "org.cinnamon.desktop.background",
    # "picture-uri", file])  # Old working command for backup

    desk_env = os.environ.get("DESKTOP_SESSION")
    if DEBUG:
        g_logger.info("DESKTOP_SESSION is: '{env}'".format(env=desk_env))

    if desk_env:
        if set_command != "":
            if set_command == "feh":
                subprocess.run(["feh", "--bg-scale", "--no-xinerama", outputfile])
            else:
                os.system(set_command.format(image=outputfile))
        elif desk_env in ["gnome", "gnome-wayland",
                        "unity", "ubuntu",
                        "pantheon", "budgie-desktop"]:
            subprocess.run(["gsettings", "set",
                            "org.gnome.desktop.background", "picture-uri",
                            file])
        elif desk_env in ["cinnamon"]:
            subprocess.run(["gsettings", "set",
                            "org.cinnamon.desktop.background", "picture-uri",
                            file])
        elif desk_env in ["mate"]:
            subprocess.run(["gsettings",
                            "set",
                            "org.mate.background",
                            "picture-filename",
                            outputfile])
        elif desk_env in ["xfce", "xubuntu"]:
            xfce_actions(outputfile)
        elif desk_env in ["lubuntu", "Lubuntu"]:
            try:
                subprocess.run("pcmanfm", "-w", outputfile)
            except:
                try:
                    subprocess.run("pcmanfm-qt", "-w", outputfile)
                except:
                    g_logger.info("Exception: failure to find either command \
'pcmanfm' or 'pcmanfm-qt'. Exiting.")
                    sys.exit(1)
        elif desk_env in ["/usr/share/xsessions/plasma"]:
            kdeplasma_actions(outputfile)
        elif "i3" in desk_env or desk_env in ["/usr/share/xsessions/bspwm"]:
            subprocess.run(["feh", "--bg-scale", "--no-xinerama", outputfile])
        else:
            if set_command == "":
                message = "Your DE could not be detected to set the wallpaper. \
You need to set the 'set_command' option in your \
settings file superpaper/general_settings. Exiting."
                g_logger.info(message)
                show_message_dialog(message, "Error")
                sys.exit(1)
            else:
                os.system(set_command.format(image=outputfile))
    else:
        g_logger.info("DESKTOP_SESSION variable is empty, \
attempting to use feh to set the wallpaper.")
        subprocess.run(["feh", "--bg-scale", "--no-xinerama", outputfile])


def special_image_cropper(outputfile):
    # file needs to be split into monitor pieces since KDE/XFCE are special
    img = Image.open(outputfile)
    outputname = os.path.splitext(outputfile)[0]
    img_names = []
    id = 0
    for res, offset in zip(RESOLUTION_ARRAY, DISPLAY_OFFSET_ARRAY):
        left = offset[0]
        top = offset[1]
        right = left + res[0]
        bottom = top + res[1]
        crop_tuple = (left, top, right, bottom)
        cropped_img = img.crop(crop_tuple)
        fname = outputname + "-crop-" + str(id) + ".png"
        img_names.append(fname)
        cropped_img.save(fname, "PNG")
        id += 1
    return img_names

def remove_old_temp_files(outputfile):
    opbase = os.path.basename(outputfile)
    opname = os.path.splitext(opbase)[0]
    print(opname)
    oldfileid = ""
    if "-a" in opname:
        oldfileid = "-b"
        print(oldfileid)
    elif "-b" in opname:
        oldfileid = "-a"
        print(oldfileid)
    else:
        pass
    if oldfileid:
        # Must take care than only temps of current profile are deleted.
        match_string = oldfileid + "-crop"
        for f in os.listdir(TEMP_PATH):
            if match_string in f:
                print(f)
                os.remove(os.path.join(TEMP_PATH, f))

def kdeplasma_actions(outputfile):
    script = """
var listDesktops = desktops();
print(listDesktops);
d = listDesktops[{index}];
d.wallpaperPlugin = "org.kde.image";
d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
d.writeConfig("Image", "file://{filename}")
"""
    img_names = special_image_cropper(outputfile)

    sessionb = dbus.SessionBus()
    plasmaInterface = dbus.Interface(
        sessionb.get_object(
            "org.kde.plasmashell",
            "/PlasmaShell"),
        dbus_interface="org.kde.PlasmaShell")
    for fname, idx in zip(img_names, range(len(img_names))):
        plasmaInterface.evaluateScript(
            script.format(index=idx, filename=fname))

    # Delete old images after new ones are set
    remove_old_temp_files(outputfile)


def xfce_actions(outputfile):
    monitors = []
    for m in range(nDisplays):
        monitors.append("monitor" + str(m))
    img_names = special_image_cropper(outputfile)

    read_prop = subprocess.Popen(["xfconf-query",
                                  "-c",
                                  "xfce4-desktop",
                                  "-p",
                                  "/backdrop",
                                  "-l"],
                                 stdout=subprocess.PIPE)
    props = read_prop.stdout.read().decode("utf-8").split("\n")
    for prop in props:
        for monitor, imgname in zip(monitors, img_names):
            if monitor in prop:
                if "last-image" in prop or "image-path" in prop:
                    os.system(
                        "xfconf-query -c xfce4-desktop -p "
                        + prop
                        + " -s ''")
                    os.system(
                        "xfconf-query -c xfce4-desktop -p "
                        + prop
                        + " -s '%s'" % imgname)
                if "image-show" in prop:
                    os.system(
                        "xfconf-query -c xfce4-desktop -p "
                        + prop
                        + " -s 'true'")
    # Delete old images after new ones are set
    remove_old_temp_files(outputfile)


def changeWallpaperJob(profile):
    with G_WALLPAPER_CHANGE_LOCK:
        if profile.spanmode.startswith("single") and profile.ppimode is False:
            # spanSingleImage(profile)
            thrd = Thread(target=spanSingleImage, args=(profile,), daemon=True)
            thrd.start()
        elif profile.spanmode.startswith("single") and profile.ppimode is True:
            # spanSingleImagePPIcorrection(profile)
            thrd = Thread(target=spanSingleImagePPIcorrection, args=(profile,), daemon=True)
            thrd.start()
        elif profile.spanmode.startswith("multi"):
            # setMultipleImages(profile)
            thrd = Thread(target=setMultipleImages, args=(profile,), daemon=True)
            thrd.start()
        else:
            g_logger.info("Unkown profile spanmode: {}".format(profile.spanmode))
        return thrd


def runProfileJob(profile):
    repeating_timer = None
    getDisplayData()  # Check here so new profile has fresh data.
    if DEBUG:
        g_logger.info("running profile job with profile: {}".format(profile.name))

    if not profile.slideshow:
        if DEBUG:
            g_logger.info("Running a one-off wallpaper change.")
        changeWallpaperJob(profile)
    elif profile.slideshow:
        if DEBUG:
            g_logger.info("Running wallpaper slideshow.")
        changeWallpaperJob(profile)
        repeating_timer = RepeatedTimer(
            profile.delayArray[0], changeWallpaperJob, profile)
    return repeating_timer


def quickProfileJob(profile):
    with G_WALLPAPER_CHANGE_LOCK:
        # Look for old temp image:
        files = [i for i in os.listdir(TEMP_PATH)
                 if os.path.isfile(os.path.join(TEMP_PATH, i))
                 and i.startswith(profile.name + "-")]
        if DEBUG:
            g_logger.info("quickswitch file lookup: {}".format(files))
        if files:
            # setWallpaper(os.path.join(TEMP_PATH, files[0]))
            thrd = Thread(target=setWallpaper, args=(os.path.join(TEMP_PATH, files[0]),), daemon=True)
            thrd.start()
        else:
            pass
            if DEBUG:
                g_logger.info("Old file for quickswitch was not found. {}".format(files))


# Profile and data handling
def listProfiles():
    files = sorted(os.listdir(PROFILES_PATH))
    profile_list = []
    for i in range(len(files)):
        try:
            profile_list.append(ProfileData(PROFILES_PATH + files[i]))
        except Exception as e:
            msg = "There was an error when loading profile '{}'. Exiting.".format(files[i])
            g_logger.info(msg)
            g_logger.info(e)
            show_message_dialog(msg, "Error")
            exit()
        if DEBUG:
            g_logger.info("Listed profile: {}".format(profile_list[i].name))
    return profile_list


def readActiveProfile():
    fname = TEMP_PATH + "running_profile"
    profname = ""
    profile = None
    if os.path.isfile(fname):
        f = open(fname, "r")
        try:
            for line in f:     # loop through line by line
                line.rstrip("\r\n")
                profname = line
                if DEBUG:
                    g_logger.info("read profile name from 'running_profile':{}"
                                  .format(profname))
                prof_file = PROFILES_PATH + profname + ".profile"
                if os.path.isfile(prof_file):
                    profile = ProfileData(prof_file)
                else:
                    profile = None
                    g_logger.info("Exception: Previously run profile configuration \
                        file not found. Is the filename same as the \
                        profile name: {pname}?".format(pname=profname))
        finally:
            f.close()
    else:
        f = open(fname, "x")
        f.close()
        profile = None
    return profile


def writeActiveProfile(profname):
    fname = TEMP_PATH + "running_profile"
    f = open(fname, "w")
    f.write(profname)
    f.close()



# TRAY ICON APPLET definitions
    # Credit:
    # https://stackoverflow.com/questions/6389580/quick-and-easy-trayicon-with-python/48401917#48401917

try:

    def create_menu_item(menu, label, func, *args, **kwargs):
        item = wx.MenuItem(menu, -1, label, **kwargs)
        menu.Bind(wx.EVT_MENU, lambda event: func(event, *args), id=item.GetId())
        menu.Append(item)
        return item

    class ConfigFrame(wx.Frame):
        def __init__(self, parent_tray_obj):
            wx.Frame.__init__(self, parent=None, title="Superpaper Profile Configuration")
            self.fSizer = wx.BoxSizer(wx.VERTICAL)
            config_panel = ConfigPanel(self, parent_tray_obj)
            self.fSizer.Add(config_panel, 1, wx.EXPAND)
            self.SetAutoLayout(True)
            self.SetSizer(self.fSizer)
            self.Fit()
            self.Layout()
            self.Center()
            self.Show()


    class ConfigPanel(wx.Panel):
        def __init__(self, parent, parent_tray_obj):
            wx.Panel.__init__(self, parent)
            self.frame = parent
            self.parent_tray_obj = parent_tray_obj
            self.sizer_main = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer_left = wx.BoxSizer(wx.VERTICAL) # buttons and prof sel
            self.sizer_right = wx.BoxSizer(wx.VERTICAL) # option fields
            self.sizer_paths = wx.BoxSizer(wx.VERTICAL)
            self.sizer_paths_buttons = wx.BoxSizer(wx.HORIZONTAL)

            self.paths_controls = []

            self.list_of_profiles = listProfiles()
            self.profnames = []
            for p in self.list_of_profiles:
                self.profnames.append(p.name)
            self.profnames.append("Create a new profile")
            # self.choiceProfile = wx.Choice(self, -1, name="ProfileChoice", size=(200, -1), choices=self.profnames)
            self.choiceProfile = wx.Choice(self, -1, name="ProfileChoice", choices=self.profnames)
            self.choiceProfile.Bind(wx.EVT_CHOICE, self.onSelect)
            self.sizer_grid_options = wx.GridSizer(5, 4, 5, 5)
            pnl = self
            st_name = wx.StaticText(pnl, -1, "Name")
            st_span = wx.StaticText(pnl, -1, "Spanmode")
            st_slide = wx.StaticText(pnl, -1, "Slideshow")
            st_sort = wx.StaticText(pnl, -1, "Sort")
            st_del = wx.StaticText(pnl, -1, "Delay (600) [sec]")
            st_off = wx.StaticText(pnl, -1, "Offsets (w1,h1;w2,h2) [px]")
            st_in = wx.StaticText(pnl, -1, "Diagonal inches (24.0;13.3) [in]")
            # st_ppi = wx.StaticText(pnl, -1, "PPIs")
            st_bez = wx.StaticText(pnl, -1, "Bezels (10.1;9.5) [mm]")
            st_hk = wx.StaticText(pnl, -1, "Hotkey (control+alt+w)")

            tc_width = 160
            self.tc_name = wx.TextCtrl(pnl, -1, size=(tc_width, -1))
            self.ch_span = wx.Choice(pnl, -1, name="SpanChoice", size=(tc_width, -1), choices=["Single", "Multi"])
            self.ch_sort = wx.Choice(pnl, -1, name="SortChoice", size=(tc_width, -1), choices=["Shuffle", "Alphabetical"])
            self.tc_delay = wx.TextCtrl(pnl, -1, size=(tc_width, -1))
            self.tc_offsets = wx.TextCtrl(pnl, -1, size=(tc_width, -1))
            self.tc_inches = wx.TextCtrl(pnl, -1, size=(tc_width, -1))
            # self.tc_ppis = wx.TextCtrl(pnl, -1, size=(tc_width, -1))
            self.tc_bez = wx.TextCtrl(pnl, -1, size=(tc_width, -1))
            self.tc_hotkey = wx.TextCtrl(pnl, -1, size=(tc_width, -1))
            self.cb_slideshow = wx.CheckBox(pnl, -1, "")  # Put the title in the left column
            self.sizer_grid_options.AddMany(
                [
                    (st_name, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.tc_name, 0, wx.ALIGN_LEFT|wx.ALL),
                    (st_span, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.ch_span, 0, wx.ALIGN_LEFT),
                    (st_slide, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.cb_slideshow, 0, wx.ALIGN_LEFT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (st_sort, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.ch_sort, 0, wx.ALIGN_LEFT),
                    (st_del, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.tc_delay, 0, wx.ALIGN_LEFT),
                    (st_off, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.tc_offsets, 0, wx.ALIGN_LEFT),
                    (st_in, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.tc_inches, 0, wx.ALIGN_LEFT),
                    # (st_ppi, 0, wx.ALIGN_RIGHT),
                    # (self.tc_ppis, 0, wx.ALIGN_LEFT),
                    (st_bez, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.tc_bez, 0, wx.ALIGN_LEFT),
                    (st_hk, 0, wx.ALIGN_RIGHT|wx.ALL|wx.ALIGN_CENTER_VERTICAL),
                    (self.tc_hotkey, 0, wx.ALIGN_LEFT),
                ]
            )

            # Paths display
            self.pathsWidget_default = self.createPathsWidget()
            self.sizer_paths.Add(self.pathsWidget_default, 0, wx.CENTER|wx.ALL, 5)


            # Left column buttons
            self.button_apply = wx.Button(self, label="Apply")
            self.button_new = wx.Button(self, label="New")
            self.button_delete = wx.Button(self, label="Delete")
            self.button_save = wx.Button(self, label="Save")
            # self.button_settings = wx.Button(self, label="Settings")
            self.button_testimage = wx.Button(self, label="Align Test")  # internally called 'testimage'
            self.button_help = wx.Button(self, label="Help")
            self.button_close = wx.Button(self, label="Close")

            self.button_apply.Bind(wx.EVT_BUTTON, self.onApply)
            self.button_new.Bind(wx.EVT_BUTTON, self.onCreateNewProfile)
            self.button_delete.Bind(wx.EVT_BUTTON, self.onDeleteProfile)
            self.button_save.Bind(wx.EVT_BUTTON, self.onSave)
            # self.button_settings.Bind(wx.EVT_BUTTON, self.onSettings)
            self.button_testimage.Bind(wx.EVT_BUTTON, self.onTestImage)
            self.button_help.Bind(wx.EVT_BUTTON, self.onHelp)
            self.button_close.Bind(wx.EVT_BUTTON, self.onClose)

            # Right column buttons
            self.button_add_paths = wx.Button(self, label="Add path")
            self.button_remove_paths = wx.Button(self, label="Remove path")

            self.button_add_paths.Bind(wx.EVT_BUTTON, self.onAddDisplay)
            self.button_remove_paths.Bind(wx.EVT_BUTTON, self.onRemoveDisplay)

            self.sizer_paths_buttons.Add(self.button_add_paths, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_paths_buttons.Add(self.button_remove_paths, 0, wx.CENTER|wx.ALL, 5)


            # Left add items
            self.sizer_left.Add(self.choiceProfile, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_left.Add(self.button_apply, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_left.Add(self.button_new, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_left.Add(self.button_delete, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_left.Add(self.button_save, 0, wx.CENTER|wx.ALL, 5)
            # self.sizer_left.Add(self.button_settings, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_left.Add(self.button_testimage, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_left.Add(self.button_help, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_left.Add(self.button_close, 0, wx.CENTER|wx.ALL, 5)

            # Right add items
            self.sizer_right.Add(self.sizer_grid_options, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_right.Add(self.sizer_paths, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_right.Add(self.sizer_paths_buttons, 0, wx.CENTER|wx.ALL, 5)

            # Collect items at main sizer
            self.sizer_main.Add(self.sizer_left, 0, wx.CENTER|wx.EXPAND)
            self.sizer_main.Add(self.sizer_right, 0, wx.CENTER|wx.EXPAND)

            self.SetSizer(self.sizer_main)
            self.sizer_main.Fit(parent)

            ### End __init__.

        def update_choiceprofile(self):
            self.list_of_profiles = listProfiles()
            self.profnames = []
            for p in self.list_of_profiles:
                self.profnames.append(p.name)
            self.profnames.append("Create a new profile")
            self.choiceProfile.SetItems(self.profnames)

        def createPathsWidget(self):
            new_paths_widget = wx.BoxSizer(wx.HORIZONTAL)
            st_new_paths = wx.StaticText(self, -1, "display" + str(len(self.paths_controls)+1) + "paths")
            tc_new_paths = wx.TextCtrl(self, -1, size=(500, -1))
            self.paths_controls.append(tc_new_paths)

            new_paths_widget.Add(st_new_paths, 0, wx.CENTER|wx.ALL, 5)
            new_paths_widget.Add(tc_new_paths, 0, wx.CENTER|wx.ALL|wx.EXPAND, 5)

            button_name = "browse-"+str(len(self.paths_controls)-1)
            button_new_browse = wx.Button(self, label="Browse", name=button_name)
            button_new_browse.Bind(wx.EVT_BUTTON, self.onBrowsePaths)
            new_paths_widget.Add(button_new_browse, 0, wx.CENTER|wx.ALL, 5)

            return new_paths_widget

        # Profile setting displaying functions.
        def populateFields(self, profile):
            self.tc_name.ChangeValue(profile.name)
            self.tc_delay.ChangeValue(str(profile.delayArray[0]))
            self.tc_offsets.ChangeValue(self.show_offset(profile.manual_offsets_useronly))
            show_inch = self.val_list_to_colonstr(profile.inches)
            self.tc_inches.ChangeValue(show_inch)
            # show_ppi = self.val_list_to_colonstr(profile.ppiArray)
            # self.tc_ppis.ChangeValue(show_ppi)
            show_bez = self.val_list_to_colonstr(profile.bezels)
            self.tc_bez.ChangeValue(show_bez)
            self.tc_hotkey.ChangeValue(self.show_hkbinding(profile.hkBinding))

            # Paths displays: get number to show from profile.
            while len(self.paths_controls) < len(profile.pathsArray):
                self.onAddDisplay(wx.EVT_BUTTON)
            while len(self.paths_controls) > len(profile.pathsArray):
                self.onRemoveDisplay(wx.EVT_BUTTON)
            for text_field, paths_list in zip(self.paths_controls, profile.pathsArray):
                text_field.ChangeValue(self.show_list_paths(paths_list))

            if profile.slideshow:
                self.cb_slideshow.SetValue(True)
            else:
                self.cb_slideshow.SetValue(False)

            if profile.spanmode == "single":
                self.ch_span.SetSelection(0)
            elif profile.spanmode == "multi":
                self.ch_span.SetSelection(1)
            else:
                pass
            if profile.sortmode == "shuffle":
                self.ch_sort.SetSelection(0)
            elif profile.sortmode == "alphabetical":
                self.ch_sort.SetSelection(1)
            else:
                pass

        def val_list_to_colonstr(self, array):
            list_strings = []
            if array:
                for item in array:
                    list_strings.append(str(item))
                return ";".join(list_strings)
            else:
                return ""

        def show_offset(self, offarray):
            offstr_arr = []
            offstr = ""
            if offarray:
                for offs in offarray:
                    offstr_arr.append(str(offs).strip("(").strip(")").replace(" ", ""))
                offstr = ";".join(offstr_arr)
                return offstr
            else:
                return ""

        def show_hkbinding(self, hktuple):
            if hktuple:
                hkstring = "+".join(hktuple)
                return hkstring
            else:
                return ""


        # Path display related functions.
        def show_list_paths(self, paths_list):
            # Format a list of paths into the set style of listed paths.
            if paths_list:
                pathsstring = ";".join(paths_list)
                return pathsstring
            else:
                return ""

        def onAddDisplay(self, event):
            new_disp_widget = self.createPathsWidget()
            self.sizer_paths.Add(new_disp_widget, 0, wx.CENTER|wx.ALL, 5)
            self.frame.fSizer.Layout()
            self.frame.Fit()

        def onRemoveDisplay(self, event):
            if self.sizer_paths.GetChildren():
                self.sizer_paths.Hide(len(self.paths_controls)-1)
                self.sizer_paths.Remove(len(self.paths_controls)-1)
                del self.paths_controls[-1]
                self.frame.fSizer.Layout()
                self.frame.Fit()

        def onBrowsePaths(self, event):
            dlg = BrowsePaths(None, self, event)
            dlg.ShowModal()


        # Top level button definitions
        def onClose(self, event):
            self.frame.Close(True)

        def onSelect(self, event):
            choiceObj = event.GetEventObject()
            if choiceObj.GetName() == "ProfileChoice":
                item = event.GetSelection()
                if event.GetString() == "Create a new profile":
                    self.onCreateNewProfile(event)
                else:
                    self.populateFields(self.list_of_profiles[item])
            else:
                pass

        def onApply(self, event):
            saved_file = self.onSave(event)
            print(saved_file)
            if saved_file is not None:
                saved_profile = ProfileData(saved_file)
                self.parent_tray_obj.reload_profiles(event)
                self.parent_tray_obj.start_profile(event, saved_profile)
            else:
                pass

        def onCreateNewProfile(self, event):
            self.choiceProfile.SetSelection(self.choiceProfile.FindString("Create a new profile"))

            self.tc_name.ChangeValue("")
            self.tc_delay.ChangeValue("")
            self.tc_offsets.ChangeValue("")
            self.tc_inches.ChangeValue("")
            # show_ppi = self.val_list_to_colonstr(profile.ppiArray)
            # self.tc_ppis.ChangeValue(show_ppi)
            self.tc_bez.ChangeValue("")
            self.tc_hotkey.ChangeValue("")

            # Paths displays: get number to show from profile.
            while len(self.paths_controls) < 1:
                self.onAddDisplay(wx.EVT_BUTTON)
            while len(self.paths_controls) > 1:
                self.onRemoveDisplay(wx.EVT_BUTTON)
            for text_field in self.paths_controls:
                text_field.ChangeValue("")

            self.cb_slideshow.SetValue(False)
            self.ch_span.SetSelection(-1)
            self.ch_sort.SetSelection(-1)

        def onDeleteProfile(self, event):
            profname = self.tc_name.GetLineText(0)
            fname = PROFILES_PATH + profname + ".profile"
            file_exists = os.path.isfile(fname)
            if not file_exists:
                msg = "Selected profile is not saved."
                show_message_dialog(msg, "Error")
                return
            # Open confirmation dialog
            dlg = wx.MessageDialog(None,
                                   "Do you want to delete profile:"+ profname +"?",
                                   'Confirm Delete',
                                   wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            if result == wx.ID_YES and file_exists:
                os.remove(fname)
            else:
                pass

        def onSave(self, event):
            tmp_profile = TempProfileData()
            tmp_profile.name = self.tc_name.GetLineText(0)
            tmp_profile.spanmode = self.ch_span.GetString(self.ch_span.GetSelection()).lower()
            tmp_profile.slideshow = self.cb_slideshow.GetValue()
            tmp_profile.delay = self.tc_delay.GetLineText(0)
            tmp_profile.sortmode = self.ch_sort.GetString(self.ch_sort.GetSelection()).lower()
            # tmp_profile.ppiArray = self.tc_ppis.GetLineText(0)
            tmp_profile.inches = self.tc_inches.GetLineText(0)
            tmp_profile.manual_offsets = self.tc_offsets.GetLineText(0)
            tmp_profile.bezels = self.tc_bez.GetLineText(0)
            tmp_profile.hkBinding = self.tc_hotkey.GetLineText(0)
            for text_field in self.paths_controls:
                tmp_profile.pathsArray.append(text_field.GetLineText(0))

            g_logger.info(tmp_profile.name)
            g_logger.info(tmp_profile.spanmode)
            g_logger.info(tmp_profile.slideshow)
            g_logger.info(tmp_profile.delay)
            g_logger.info(tmp_profile.sortmode)
            # g_logger.info(tmp_profile.ppiArray)
            g_logger.info(tmp_profile.inches)
            g_logger.info(tmp_profile.manual_offsets)
            g_logger.info(tmp_profile.bezels)
            g_logger.info(tmp_profile.hkBinding)
            g_logger.info(tmp_profile.pathsArray)

            if tmp_profile.TestSave():
                saved_file = tmp_profile.Save()
                self.update_choiceprofile()
                self.parent_tray_obj.reload_profiles(event)
                self.parent_tray_obj.register_hotkeys()
                # self.parent_tray_obj.register_hotkeys()
                self.choiceProfile.SetSelection(self.choiceProfile.FindString(tmp_profile.name))
                return saved_file
            else:
                g_logger.info("TestSave failed.")
                return None

        def onTestImage(self, event):
            # Use the settings currently written out in the fields!
            testimage = [PATH + "/resources/test.png"]
            if not os.path.isfile(testimage[0]):
                print(testimage)
                msg = "Test image not found in {}.".format(testimage)
                show_message_dialog(msg, "Error")
            ppi = None
            inches = self.tc_inches.GetLineText(0).split(";")
            if (inches == "") or (len(inches) < nDisplays):
                msg = "You must enter a diagonal inch value for every display, serparated by a semicolon ';'."
                show_message_dialog(msg, "Error")

            # print(inches)
            inches = [float(i) for i in inches]
            bezels = self.tc_bez.GetLineText(0).split(";")
            bezels = [float(b) for b in bezels]
            offsets = self.tc_offsets.GetLineText(0).split(";")
            offsets = [[int(i.split(",")[0]), int(i.split(",")[1])] for i in offsets]
            flat_offsets = []
            for off in offsets:
                for pix in off:
                    flat_offsets.append(pix)
            # print("flat_offsets= ", flat_offsets)
            # Use the simplified CLI profile class
            getDisplayData()
            profile = CLIProfileData(testimage,
                                     ppi,
                                     inches,
                                     bezels,
                                     flat_offsets,
                                    )
            changeWallpaperJob(profile)

        def onHelp(self, event):
            help_frame = HelpFrame()


    class BrowsePaths(wx.Dialog):
        def __init__(self, parent, parent_self, parent_event):
            wx.Dialog.__init__(self, parent, -1, 'Choose Image Source Directories', size=(500, 700))
            self.parent_self = parent_self
            self.parent_event = parent_event
            self.paths = []
            sizer_main = wx.BoxSizer(wx.VERTICAL)
            sizer_browse = wx.BoxSizer(wx.VERTICAL)
            sizer_textfield = wx.BoxSizer(wx.VERTICAL)
            sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
            self.dir3 = wx.GenericDirCtrl(self, -1,
                                          # style=wx.DIRCTRL_MULTIPLE,
                                          # style=0,
                                          size=(450, 550))
            sizer_browse.Add(self.dir3, 0, wx.CENTER|wx.ALL|wx.EXPAND, 5)
            self.tc_paths = wx.TextCtrl(self, -1, size=(450, -1))
            sizer_textfield.Add(self.tc_paths, 0, wx.CENTER|wx.ALL, 5)

            self.button_add = wx.Button(self, label="Add")
            self.button_remove = wx.Button(self, label="Remove")
            self.button_ok = wx.Button(self, label="Ok")
            self.button_cancel = wx.Button(self, label="Cancel")

            self.button_add.Bind(wx.EVT_BUTTON, self.onAdd)
            self.button_remove.Bind(wx.EVT_BUTTON, self.onRemove)
            self.button_ok.Bind(wx.EVT_BUTTON, self.onOk)
            self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

            sizer_buttons.Add(self.button_add, 0, wx.CENTER|wx.ALL, 5)
            sizer_buttons.Add(self.button_remove, 0, wx.CENTER|wx.ALL, 5)
            sizer_buttons.Add(self.button_ok, 0, wx.CENTER|wx.ALL, 5)
            sizer_buttons.Add(self.button_cancel, 0, wx.CENTER|wx.ALL, 5)

            sizer_main.Add(sizer_browse, 5, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND)
            sizer_main.Add(sizer_textfield, 5, wx.ALL|wx.ALIGN_CENTER)
            sizer_main.Add(sizer_buttons, 5, wx.ALL|wx.ALIGN_CENTER)
            self.SetSizer(sizer_main)
            self.SetAutoLayout(True)

        def onAdd(self, event):
            text_field = self.tc_paths.GetLineText(0)
            new_path = self.dir3.GetPath()
            self.paths.append(new_path)
            if text_field == "":
                text_field = new_path
            else:
                text_field = ";".join([text_field, new_path])
            self.tc_paths.SetValue(text_field)
            self.tc_paths.SetInsertionPointEnd()

        def onRemove(self, event):
            if len(self.paths) > 0:
                del self.paths[-1]
                text_field = ";".join(self.paths)
                self.tc_paths.SetValue(text_field)
                self.tc_paths.SetInsertionPointEnd()

        def onOk(self, event):
            paths_string = self.tc_paths.GetLineText(0)
            # If paths textctrl is empty, assume user wants current selection.
            if paths_string == "":
                paths_string = self.dir3.GetPath()
            button_obj = self.parent_event.GetEventObject()
            button_name = button_obj.GetName()
            button_id = int(button_name.split("-")[1])
            text_field = self.parent_self.paths_controls[button_id]
            old_text = text_field.GetLineText(0)
            if old_text == "":
                new_text = paths_string
            else:
                new_text = old_text + ";" + paths_string
            text_field.ChangeValue(new_text)
            self.Destroy()

        def onCancel(self, event):
            self.Destroy()



    class SettingsFrame(wx.Frame):
        def __init__(self, parent_tray_obj):
            wx.Frame.__init__(self, parent=None, title="Superpaper General Settings")
            self.fSizer = wx.BoxSizer(wx.VERTICAL)
            settings_panel = SettingsPanel(self, parent_tray_obj)
            self.fSizer.Add(settings_panel, 1, wx.EXPAND)
            self.SetAutoLayout(True)
            self.SetSizer(self.fSizer)
            self.Fit()
            self.Layout()
            self.Center()
            self.Show()

    class SettingsPanel(wx.Panel):
        def __init__(self, parent, parent_tray_obj):
            wx.Panel.__init__(self, parent)
            self.frame = parent
            self.parent_tray_obj = parent_tray_obj
            self.sizer_main = wx.BoxSizer(wx.VERTICAL)
            self.sizer_grid_settings = wx.GridSizer(5, 2, 5, 5)
            self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
            pnl = self
            st_logging = wx.StaticText(pnl, -1, "Logging")
            st_usehotkeys = wx.StaticText(pnl, -1, "Use hotkeys")
            st_hk_next = wx.StaticText(pnl, -1, "Hotkey: Next wallpaper")
            st_hk_pause = wx.StaticText(pnl, -1, "Hotkey: Pause slideshow")
            st_setcmd = wx.StaticText(pnl, -1, "Custom command")
            self.cb_logging = wx.CheckBox(pnl, -1, "")
            self.cb_usehotkeys = wx.CheckBox(pnl, -1, "")
            self.tc_hk_next = wx.TextCtrl(pnl, -1, size=(200, -1))
            self.tc_hk_pause = wx.TextCtrl(pnl, -1, size=(200, -1))
            self.tc_setcmd = wx.TextCtrl(pnl, -1, size=(200, -1))

            self.sizer_grid_settings.AddMany(
                [
                    (st_logging, 0, wx.ALIGN_RIGHT),
                    (self.cb_logging, 0, wx.ALIGN_LEFT),
                    (st_usehotkeys, 0, wx.ALIGN_RIGHT),
                    (self.cb_usehotkeys, 0, wx.ALIGN_LEFT),
                    (st_hk_next, 0, wx.ALIGN_RIGHT),
                    (self.tc_hk_next, 0, wx.ALIGN_LEFT),
                    (st_hk_pause, 0, wx.ALIGN_RIGHT),
                    (self.tc_hk_pause, 0, wx.ALIGN_LEFT),
                    (st_setcmd, 0, wx.ALIGN_RIGHT),
                    (self.tc_setcmd, 0, wx.ALIGN_LEFT),
                ]
            )
            self.update_fields()
            self.button_save = wx.Button(self, label="Save")
            self.button_close = wx.Button(self, label="Close")
            self.button_save.Bind(wx.EVT_BUTTON, self.onSave)
            self.button_close.Bind(wx.EVT_BUTTON, self.onClose)
            self.sizer_buttons.Add(self.button_save, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_buttons.Add(self.button_close, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_main.Add(self.sizer_grid_settings, 0, wx.CENTER|wx.EXPAND)
            self.sizer_main.Add(self.sizer_buttons, 0, wx.CENTER|wx.EXPAND)
            self.SetSizer(self.sizer_main)
            self.sizer_main.Fit(parent)

        def update_fields(self):
            g_settings = GeneralSettingsData()
            self.cb_logging.SetValue(g_settings.logging)
            self.cb_usehotkeys.SetValue(g_settings.use_hotkeys)
            self.tc_hk_next.ChangeValue(self.show_hkbinding(g_settings.hkBinding_next))
            self.tc_hk_pause.ChangeValue(self.show_hkbinding(g_settings.hkBinding_pause))
            self.tc_setcmd.ChangeValue(g_settings.set_command)

        def show_hkbinding(self, hktuple):
            hkstring = "+".join(hktuple)
            return hkstring

        def onSave(self, event):
            current_settings = GeneralSettingsData()
            show_help = current_settings.show_help

            fname = os.path.join(PATH, "general_settings")
            f = open(fname, "w")
            if self.cb_logging.GetValue():
                f.write("logging=true\n")
            else:
                f.write("logging=false\n")
            if self.cb_usehotkeys.GetValue():
                f.write("use hotkeys=true\n")
            else:
                f.write("use hotkeys=false\n")
            f.write("next wallpaper hotkey=" + self.tc_hk_next.GetLineText(0) + "\n")
            f.write("pause wallpaper hotkey=" + self.tc_hk_pause.GetLineText(0) + "\n")
            if show_help:
                f.write("show_help_at_start=true\n")
            else:
                f.write("show_help_at_start=false\n")
            f.write("set_command=" + self.tc_setcmd.GetLineText(0))
            f.close()
            # after saving file apply in tray object
            self.parent_tray_obj.read_general_settings()

        def onClose(self, event):
            self.frame.Close(True)


    class HelpFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, parent=None, title="Superpaper Help")
            self.fSizer = wx.BoxSizer(wx.VERTICAL)
            help_panel = HelpPanel(self)
            self.fSizer.Add(help_panel, 1, wx.EXPAND)
            self.SetAutoLayout(True)
            self.SetSizer(self.fSizer)
            self.Fit()
            self.Layout()
            self.Center()
            self.Show()

    class HelpPanel(wx.Panel):
        def __init__(self, parent):
            wx.Panel.__init__(self, parent)
            self.frame = parent
            self.sizer_main = wx.BoxSizer(wx.VERTICAL)
            self.sizer_helpcontent = wx.BoxSizer(wx.VERTICAL)
            self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)

            current_settings = GeneralSettingsData()
            show_help = current_settings.show_help

            st_show_at_start = wx.StaticText(self, -1, "Show this help at start")
            self.cb_show_at_start = wx.CheckBox(self, -1, "")
            self.cb_show_at_start.SetValue(show_help)
            self.button_close = wx.Button(self, label="Close")
            self.button_close.Bind(wx.EVT_BUTTON, self.onClose)
            self.sizer_buttons.Add(st_show_at_start, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_buttons.Add(self.cb_show_at_start, 0, wx.CENTER|wx.ALL, 5)
            self.sizer_buttons.Add(self.button_close, 0, wx.CENTER|wx.ALL, 5)

            help_str = """
How to use Superpaper:

In the Profile Configuration you can adjust all your wallpaper settings.
Only required options are name and wallpaper paths. Other application
wide settings can be changed in the Settings menu. Both are accessible
from the system tray menu.

IMPORTANT NOTE: For the wallpapers to be set correctly, you must set
in your OS the background fitting option to 'Span'.

NOTE: If your displays are not in a horizontal row, the pixel density
and offset corrections unfortunately do not work. In this case leave
the 'Diagonal inches', 'Offsets' and 'Bezels' fields empty.

Description of Profile Configuration options:
In the text field description an example is shown in parantheses and in
brackets the expected units of numerical values.

"Diagonal inches": The diagonal diameters of your monitors in
                                 order starting from the left most monitor.
                                 These affect the wallpaper only in "Single"
                                 spanmode.

"Spanmode": "Single" (span a single image across all monitors)
                        "Multi" (set a different image on every monitor.)

"Sort":  Applies to slideshow mode wallpaper order.

"Offsets":  Wallpaper alignment correction offsets for your displays
                   if using "Single" spanmode. Entered as "width,height"
                   pixel value pairs, pairs separated by a semicolon ";".
                   Positive offsets move the portion of the image on 
                   the monitor down and to the right, negative offets
                   up or left.

"Bezels":   Bezel correction for "Single" spanmode wallpaper. Use this
                  if you want the image to continue behind the bezels,
                  like a scenery does behind a window frame.

"Hotkey":   An optional key combination to apply/start the profile.
                    Supports up to 3 modifiers and a key. Valid modifiers
                    are 'control', 'super', 'alt' and 'shift'. Separate
                    keys with a '+', like 'control+alt+w'.

"display{N}paths":  Wallpaper folder paths for the display in the Nth
                            position from the left. Multiple can be entered with
                            the browse tool using "Add". If you have more than
                            one vertically stacked row, they should be listed
                            row by row starting from the top most row.

Tips:
    - You can use the given example profiles as templates: just change
       the name and whatever else, save, and its a new profile.
    - 'Align Test' feature allows you to test your offset and bezel settings.
       Display diagonals, offsets and bezels need to be entered.
"""
            st_help = wx.StaticText(self, -1, help_str)
            self.sizer_helpcontent.Add(st_help, 0, wx.EXPAND|wx.CENTER|wx.ALL, 5)

            self.sizer_main.Add(self.sizer_helpcontent, 0, wx.CENTER|wx.EXPAND)
            self.sizer_main.Add(self.sizer_buttons, 0, wx.CENTER|wx.EXPAND)
            self.SetSizer(self.sizer_main)
            self.sizer_main.Fit(parent)

        def onClose(self, event):
            if self.cb_show_at_start.GetValue() is True:
                current_settings = GeneralSettingsData()
                if current_settings.show_help is False:
                    current_settings.show_help = True
                    current_settings.Save()
            else:
                # Save that the help at start is not wanted.
                current_settings = GeneralSettingsData()
                show_help = current_settings.show_help
                if show_help:
                    current_settings.show_help = False
                    current_settings.Save()
            self.frame.Close(True)



    class TaskBarIcon(wx.adv.TaskBarIcon):
        def __init__(self, frame):
            self.g_settings = GeneralSettingsData()

            self.frame = frame
            super(TaskBarIcon, self).__init__()
            self.set_icon(TRAY_ICON)
            self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
            # profile initialization
            self.jobLock = Lock()
            getDisplayData()
            self.repeating_timer = None
            self.pause_item = None
            self.is_paused = False
            if DEBUG:
                g_logger.info("START Listing profiles for menu.")
            self.list_of_profiles = listProfiles()
            if DEBUG:
                g_logger.info("END Listing profiles for menu.")
            # Should now return an object if a previous profile was written or
            # None if no previous data was found
            self.active_profile = readActiveProfile()
            self.start_prev_profile(self.active_profile)
            # if self.active_profile is None:
            #     g_logger.info("Starting up the first profile found.")
            #     self.start_profile(wx.EVT_MENU, self.list_of_profiles[0])

            # self.hk = None
            # self.hk2 = None
            if self.g_settings.use_hotkeys is True:
                try:
                    # import keyboard # https://github.com/boppreh/keyboard
                    from system_hotkey import SystemHotkey
                    self.hk = SystemHotkey(check_queue_interval=0.05)
                    self.hk2 = SystemHotkey(
                        consumer=self.profile_consumer,
                        check_queue_interval=0.05)
                    self.seen_binding = set()
                except Exception as e:
                    g_logger.info(
                        "WARNING: Could not import keyboard hotkey hook library, \
    hotkeys will not work. Exception: {}".format(e))
                self.register_hotkeys()
            if self.g_settings.show_help is True:
                config_frame = ConfigFrame(self)
                help_frame = HelpFrame()



        def register_hotkeys(self):
            if self.g_settings.use_hotkeys is True:
                try:
                    # import keyboard # https://github.com/boppreh/keyboard
                    from system_hotkey import SystemHotkey
                except Exception as e:
                    g_logger.info(
                        "WARNING: Could not import keyboard hotkey hook library, \
    hotkeys will not work. Exception: {}".format(e))
                if "system_hotkey" in sys.modules:
                    try:
                        # Keyboard bindings: https://github.com/boppreh/keyboard
                        #
                        # Alternative KB bindings for X11 systems and Windows:
                        # system_hotkey https://github.com/timeyyy/system_hotkey
                        # seen_binding = set()
                        # self.hk = SystemHotkey(check_queue_interval=0.05)
                        # self.hk2 = SystemHotkey(
                        #     consumer=self.profile_consumer,
                        #     check_queue_interval=0.05)

                        # Unregister previous hotkeys
                        if self.seen_binding:
                            for binding in self.seen_binding:
                                try:
                                    self.hk.unregister(binding)
                                    if DEBUG:
                                        g_logger.info("Unreg hotkey {}".format(binding))
                                except:
                                    try:
                                        self.hk2.unregister(binding)
                                        if DEBUG:
                                            g_logger.info("Unreg hotkey {}".format(binding))
                                    except:
                                        if DEBUG:
                                            g_logger.info("Could not unreg hotkey '{}'".format(binding))
                            self.seen_binding = set()


                        # register general bindings
                        if self.g_settings.hkBinding_next not in self.seen_binding:
                            try:
                                self.hk.register(
                                    self.g_settings.hkBinding_next,
                                    callback=lambda x: self.next_wallpaper(wx.EVT_MENU),
                                    overwrite=False)
                                self.seen_binding.add(self.g_settings.hkBinding_next)
                            except:
                                msg = "Error: could not register hotkey {}. \
    Check that it is formatted properly and valid keys.".format(self.g_settings.hkBinding_next)
                                g_logger.info(msg)
                                g_logger.info(sys.exc_info()[0])
                                show_message_dialog(msg, "Error")
                        if self.g_settings.hkBinding_pause not in self.seen_binding:
                            try:
                                self.hk.register(
                                    self.g_settings.hkBinding_pause,
                                    callback=lambda x: self.pause_timer(wx.EVT_MENU),
                                    overwrite=False)
                                self.seen_binding.add(self.g_settings.hkBinding_pause)
                            except:
                                msg = "Error: could not register hotkey {}. \
    Check that it is formatted properly and valid keys.".format(self.g_settings.hkBinding_pause)
                                g_logger.info(msg)
                                g_logger.info(sys.exc_info()[0])
                                show_message_dialog(msg, "Error")
                        try:
                            hk.register(('control', 'super', 'shift', 'q'),
                                        callback=lambda x: self.on_exit(wx.EVT_MENU))
                        except:
                            pass
                        # register profile specific bindings
                        self.list_of_profiles = listProfiles()
                        for profile in self.list_of_profiles:
                            if DEBUG:
                                g_logger.info(
                                    "Registering binding: \
                                    {} for profile: {}"
                                    .format(profile.hkBinding, profile.name))
                            if (profile.hkBinding is not None and
                                    profile.hkBinding not in self.seen_binding):
                                try:
                                    self.hk2.register(profile.hkBinding, profile,
                                                      overwrite=False)
                                    self.seen_binding.add(profile.hkBinding)
                                except:
                                    msg = "Error: could not register hotkey {}. \
    Check that it is formatted properly and valid keys.".format(profile.hkBinding)
                                    g_logger.info(msg)
                                    g_logger.info(sys.exc_info()[0])
                                    show_message_dialog(msg, "Error")
                            elif profile.hkBinding in self.seen_binding:
                                msg = "Could not register hotkey: '{}' for profile: '{}'.\n\
It is already registered for another action.".format(profile.hkBinding, profile.name)
                                g_logger.info(msg)
                                show_message_dialog(msg, "Error")
                    except:
                        if DEBUG:
                            g_logger.info("Coulnd't register hotkeys, exception:")
                            g_logger.info(sys.exc_info()[0])



        def profile_consumer(self, event, hotkey, profile):
            if DEBUG:
                g_logger.info("Profile object is: {}".format(profile))
            self.start_profile(wx.EVT_MENU, profile[0][0])

        def read_general_settings(self):
            # THIS FAILS MISERABLY, creating additional tray items.
            # Reload settings by reloading the whole object.
            # BUG if logging is on, this creates additional logging handlers
            # leading to multiple log prints per event.
            # self.__init__(self.frame)
            self.g_settings = GeneralSettingsData()
            self.register_hotkeys()
            msg = "New settings are applied after an application restart. New hotkeys are registered."
            show_message_dialog(msg, "Info")

        def CreatePopupMenu(self):
            menu = wx.Menu()
            create_menu_item(menu, "Open Config Folder", self.open_config)
            create_menu_item(menu, "Profile Configuration", self.configure_profiles)
            create_menu_item(menu, "Settings", self.configure_settings)
            create_menu_item(menu, "Reload Profiles", self.reload_profiles)
            menu.AppendSeparator()
            for item in self.list_of_profiles:
                create_menu_item(menu, item.name, self.start_profile, item)
            menu.AppendSeparator()
            create_menu_item(menu, "Next Wallpaper", self.next_wallpaper)
            self.pause_item = create_menu_item(
                menu, "Pause Timer", self.pause_timer, kind=wx.ITEM_CHECK)
            self.pause_item.Check(self.is_paused)
            menu.AppendSeparator()
            create_menu_item(menu, 'About', self.on_about)
            create_menu_item(menu, 'Exit', self.on_exit)
            return menu

        def set_icon(self, path):
            icon = wx.Icon(path)
            self.SetIcon(icon, TRAY_TOOLTIP)

        def on_left_down(self, *event):
            g_logger.info('Tray icon was left-clicked.')

        def open_config(self, event):
            if platform.system() == "Windows":
                try:
                    os.startfile(PATH)
                except BaseException:
                    pass
            elif platform.system() == "Darwin":
                try:
                    subprocess.Popen(["open", PATH])
                except BaseException:
                    pass
            else:
                try:
                    subprocess.Popen(['xdg-open', PATH])
                except BaseException:
                    pass

        def configure_profiles(self, event):
            config_frame = ConfigFrame(self)

        def configure_settings(self, event):
            setting_frame = SettingsFrame(self)

        def reload_profiles(self, event):
            self.list_of_profiles = listProfiles()

        def start_prev_profile(self, profile):
            with self.jobLock:
                if profile is None:
                    g_logger.info("No previous profile was found.")
                else:
                    self.repeating_timer = runProfileJob(profile)

        def start_profile(self, event, profile):
            if DEBUG:
                g_logger.info("Start profile: {}".format(profile.name))
            if profile is None:
                g_logger.info(
                    "start_profile: profile is None. \
                    Do you have any profiles in /profiles?")
            elif self.active_profile is not None:
                if DEBUG:
                    g_logger.info(
                        "Check if the starting profile is already running: {}"
                        .format(profile.name))
                    g_logger.info(
                        "name check: {}, {}"
                        .format(profile.name,
                                self.active_profile.name))
                if profile.name == self.active_profile.name:
                    self.next_wallpaper(event)
                    return 0
                else:
                    with self.jobLock:
                        if (self.repeating_timer is not None and
                                self.repeating_timer.is_running):
                            self.repeating_timer.stop()
                        if DEBUG:
                            g_logger.info(
                                "Running quick profile job with profile: {}"
                                .format(profile.name))
                        quickProfileJob(profile)
                        if DEBUG:
                            g_logger.info(
                                "Starting timed profile job with profile: {}"
                                .format(profile.name))
                        self.repeating_timer = runProfileJob(profile)
                        self.active_profile = profile
                        writeActiveProfile(profile.name)
                        if DEBUG:
                            g_logger.info("Wrote active profile: {}"
                                          .format(profile.name))
                        return 0
            else:
                with self.jobLock:
                    if (self.repeating_timer is not None
                            and self.repeating_timer.is_running):
                        self.repeating_timer.stop()
                    if DEBUG:
                        g_logger.info(
                            "Running quick profile job with profile: {}"
                            .format(profile.name))
                    quickProfileJob(profile)
                    if DEBUG:
                        g_logger.info(
                            "Starting timed profile job with profile: {}"
                            .format(profile.name))
                    self.repeating_timer = runProfileJob(profile)
                    self.active_profile = profile
                    writeActiveProfile(profile.name)
                    if DEBUG:
                        g_logger.info("Wrote active profile: {}"
                                      .format(profile.name))
                    return 0

        def next_wallpaper(self, event):
            with self.jobLock:
                if (self.repeating_timer is not None
                        and self.repeating_timer.is_running):
                    self.repeating_timer.stop()
                    changeWallpaperJob(self.active_profile)
                    self.repeating_timer.start()
                else:
                    changeWallpaperJob(self.active_profile)

        def rt_stop(self):
            if (self.repeating_timer is not None
                    and self.repeating_timer.is_running):
                self.repeating_timer.stop()

        def pause_timer(self, event):
            # check if a timer is running and if it is, then try to stop/start
            if (self.repeating_timer is not None
                    and self.repeating_timer.is_running):
                self.repeating_timer.stop()
                self.is_paused = True
                if DEBUG:
                    g_logger.info("Paused timer")
            elif (self.repeating_timer is not None
                  and not self.repeating_timer.is_running):
                self.repeating_timer.start()
                self.is_paused = False
                if DEBUG:
                    g_logger.info("Resumed timer")
            else:
                g_logger.info("Current profile isn't using a timer.")

        def on_about(self, event):
            # Credit for AboutDiaglog example to Jan Bodnar of
            # http://zetcode.com/wxpython/dialogs/
            description = (
                "Superpaper is an advanced multi monitor wallpaper\n"
                +"manager for Unix and Windows operating systems.\n"
                +"Features include setting a single or multiple image\n"
                +"wallpaper, pixel per inch and bezel corrections,\n"
                +"manual pixel offsets for tuning, slideshow with\n"
                +"configurable file order, multiple path support and more."
                )

            licence = (
                "Superpaper is free software; you can redistribute\n"
                +"it and/or modify it under the terms of the MIT"
                +" License.\n\n"
                +"Superpaper is distributed in the hope that it will"
                +" be useful,\n"
                +"but WITHOUT ANY WARRANTY; without even the implied"
                +" warranty of\n"
                +"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n"
                +"See the MIT License for more details."
                )
            artists = "Icons kindly provided by Icons8 https://icons8.com"

            info = wx.adv.AboutDialogInfo()
            info.SetIcon(wx.Icon(TRAY_ICON, wx.BITMAP_TYPE_PNG))
            info.SetName('Superpaper')
            info.SetVersion(VERSION_STRING)
            info.SetDescription(description)
            info.SetCopyright('(C) 2019 Henri Hänninen')
            info.SetWebSite('https://github.com/hhannine/Superpaper/')
            info.SetLicence(licence)
            info.AddDeveloper('Henri Hänninen')
            info.AddArtist(artists)
            # info.AddDocWriter('Doc Writer')
            # info.AddTranslator('Tran Slator')
            wx.adv.AboutBox(info)

        def on_exit(self, event):
            self.rt_stop()
            wx.CallAfter(self.Destroy)
            self.frame.Close()

    class App(wx.App):

        def OnInit(self):
            frame = wx.Frame(None)
            self.SetTopWindow(frame)
            TaskBarIcon(frame)
            return True
except Exception as e:
    if DEBUG:
        g_logger.info("Failed to define tray applet classes. Is wxPython installed?")
        g_logger.info(e)


def cli_logic():
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
                        help="Run the full application with debugging g_logger.infos.")
    args = parser.parse_args()

    if args.debug:
        global DEBUG
        DEBUG = True
        g_logger.setLevel(logging.INFO)
        # Install exception handler
        # sys.excepthook = custom_exception_handler
        consoleHandler = logging.StreamHandler()
        g_logger.addHandler(consoleHandler)
        g_logger.info(args.setimages)
        g_logger.info(args.ppi)
        g_logger.info(args.inches)
        g_logger.info(args.bezels)
        g_logger.info(args.offsets)
        g_logger.info(args.command)
        g_logger.info(args.debug)
    if args.debug and len(sys.argv) == 2:
        tray_loop()
    else:
        if not args.setimages:
            g_logger.info("Exception: You must pass image(s) to set as \
wallpaper with '-s' or '--setimages'. Exiting.")
            exit()
        else:
            for file in args.setimages:
                if not os.path.isfile(file):
                    g_logger.error("Exception: One of the passed images was not \
a file: ({fname}). Exiting.".format(fname=file))
                    exit()
        if args.bezels and not (args.ppi or args.inches):
            g_logger.info("The bezel correction feature needs display PPIs, \
provide these with --inches or --ppi.")
        if args.offsets and len(args.offsets) % 2 != 0:
            g_logger.error("Exception: Number of offset pixels not even. If passing manual \
offsets, give width and height offset for each display, even if \
not actually offsetting every display. Exiting.")
            exit()
        if args.command:
            if len(args.command) > 1:
                g_logger.error("Exception: Remember to put the custom command in quotes. \
Exiting.")
                exit()
            global G_SET_COMMAND_STRING
            G_SET_COMMAND_STRING = args.command[0]

        getDisplayData()
        profile = CLIProfileData(args.setimages,
                                 args.ppi,
                                 args.inches,
                                 args.bezels,
                                 args.offsets,
                                )
        job_thread = changeWallpaperJob(profile)
        job_thread.join()


def tray_loop():
    if not os.path.isdir(PROFILES_PATH):
        os.mkdir(PROFILES_PATH)
    if "wx" in sys.modules:
        app = App(False)
        app.MainLoop()
    else:
        print("ERROR: Module 'wx' import has failed. Is it installed? \
GUI unavailable, exiting.")
        g_logger.error("ERROR: Module 'wx' import has failed. Is it installed? \
GUI unavailable, exiting.")
        exit()


# MAIN


def main():
    if not len(sys.argv) > 1:
        tray_loop()
    else:
        cli_logic()


if __name__ == "__main__":
    main()
