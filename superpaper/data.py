"""
Data storage classes for Superpaper.

Written by Henri Hänninen.
"""

import logging
import math
import os
import platform
import random
import datetime
import sys

import superpaper.sp_logging as sp_logging
from superpaper.message_dialog import show_message_dialog
import superpaper.wallpaper_processing as wpproc
import superpaper.sp_paths as sp_paths
from superpaper.sp_paths import (PATH, CONFIG_PATH, PROFILES_PATH, TEMP_PATH)



# Profile and data handling, back-end interface.
def list_profiles():
    """Lists profiles as initiated objects from the sp_paths.PROFILES_PATH."""
    files = sorted(os.listdir(sp_paths.PROFILES_PATH))
    profile_list = []
    for pfle in files:
        try:
            if pfle.endswith(".profile"):
                profile_list.append(ProfileData(os.path.join(sp_paths.PROFILES_PATH, pfle)))
        except Exception as exep:  # TODO implement proper error catching for ProfileData init
            msg = ("There was an error when loading profile '{}'.\n".format(pfle)
                   + "Would you like to delete it? Choosing 'No' will just ignore the profile."
            )
            sp_logging.G_LOGGER.info(msg)
            sp_logging.G_LOGGER.info(exep)
            res = show_message_dialog(msg, "Error", style="YES_NO")
            if res:
                # remove pfle
                print("removing:", os.path.join(sp_paths.PROFILES_PATH, pfle))
                os.remove(os.path.join(sp_paths.PROFILES_PATH, pfle))
                continue
            else:
                continue
    return profile_list

def open_profile(profile):
    """Returns a ProfileData object."""
    prof_file = os.path.join(sp_paths.PROFILES_PATH, profile + ".profile")
    if os.path.isfile(prof_file):
        prof = ProfileData(prof_file)
    elif os.path.isfile(profile):
        prof = ProfileData(profile)
    else:
        prof = None
    return prof

def read_active_profile():
    """Reads last active profile from file at startup."""
    fname = os.path.join(sp_paths.TEMP_PATH, "running_profile")
    profname = ""
    profile = None
    if os.path.isfile(fname):
        rp_file = open(fname, "r")
        try:
            for line in rp_file:     # loop through line by line
                line.rstrip("\r\n")
                profname = line
                # if sp_logging.DEBUG:
                #     sp_logging.G_LOGGER.info("read profile name from 'running_profile': %s",
                #                              profname)
                prof_file = os.path.join(sp_paths.PROFILES_PATH, profname + ".profile")
                if os.path.isfile(prof_file):
                    profile = ProfileData(prof_file)
                else:
                    profile = None
                    sp_logging.G_LOGGER.info("Exception: Previously run profile configuration \
                        file not found. Is the filename same as the \
                        profile name: %s?", profname)
        finally:
            rp_file.close()
    else:
        rp_file = open(fname, "x")
        rp_file.close()
        profile = None
    return profile

def write_active_profile(profname):
    """Writes active profile name to file after profile has changed."""
    fname = os.path.join(sp_paths.TEMP_PATH, "running_profile")
    rp_file = open(fname, "w")
    rp_file.write(profname)
    rp_file.close()



class GeneralSettingsData(object):
    """Object to store and save application wide settings."""

    def __init__(self):
        self.logging = False
        self.use_hotkeys = True
        self.hk_binding_next = None
        self.hk_binding_pause = None
        self.set_command = ""
        self.browse_default_dir = ""
        self.show_help = True
        self.warn_large_img = True
        self.parse_settings()

    def parse_settings(self):
        """Parse general_settings file. Create it if it doesn't exists."""
        fname = os.path.join(CONFIG_PATH, "general_settings")
        if os.path.isfile(fname):
            general_settings_file = open(fname, "r")
            try:
                for line in general_settings_file:
                    words = line.strip().split("=")
                    if words[0] == "logging":
                        wrds1 = words[1].strip().lower()
                        if wrds1 == "true":
                            self.logging = True
                            sp_logging.LOGGING = True
                            sp_logging.DEBUG = True
                            sp_logging.G_LOGGER = logging.getLogger("default")
                            sp_logging.G_LOGGER.setLevel(logging.INFO)
                            # Install exception handler
                            sys.excepthook = sp_logging.custom_exception_handler
                            sp_logging.FILE_HANDLER = logging.FileHandler(
                                os.path.join(TEMP_PATH, "log"),
                                mode="w")
                            sp_logging.G_LOGGER.addHandler(sp_logging.FILE_HANDLER)
                            sp_logging.CONSOLE_HANDLER = logging.StreamHandler()
                            sp_logging.G_LOGGER.addHandler(sp_logging.CONSOLE_HANDLER)
                            sp_logging.G_LOGGER.info("Enabled logging to file.")
                    elif words[0] == "use hotkeys":
                        wrds1 = words[1].strip().lower()
                        if wrds1 == "true":
                            self.use_hotkeys = True
                        else:
                            self.use_hotkeys = False
                        if sp_logging.DEBUG:
                            sp_logging.G_LOGGER.info("use_hotkeys: %s", self.use_hotkeys)
                    elif words[0] == "next wallpaper hotkey":
                        binding_strings = words[1].strip().split("+")
                        if binding_strings:
                            self.hk_binding_next = tuple(binding_strings)
                        if sp_logging.DEBUG:
                            sp_logging.G_LOGGER.info("hk_binding_next: %s", self.hk_binding_next)
                    elif words[0] == "pause wallpaper hotkey":
                        binding_strings = words[1].strip().split("+")
                        if binding_strings:
                            self.hk_binding_pause = tuple(binding_strings)
                        if sp_logging.DEBUG:
                            sp_logging.G_LOGGER.info("hk_binding_pause: %s", self.hk_binding_pause)
                    elif words[0] == "set_command":
                        wpproc.G_SET_COMMAND_STRING = words[1].strip()
                        self.set_command = wpproc.G_SET_COMMAND_STRING
                    elif words[0].strip() == "show_help_at_start":
                        show_state = words[1].strip().lower()
                        if show_state == "false":
                            self.show_help = False
                        else:
                            pass
                    elif words[0].strip() == "warn_large_img":
                        show_state = words[1].strip().lower()
                        if show_state == "false":
                            self.warn_large_img = False
                        else:
                            pass
                    elif words[0].strip() == "browse_default_dir":
                        self.browse_default_dir = words[1].strip()
                    else:
                        sp_logging.G_LOGGER.info("GeneralSettings parse Exception: Unkown general setting: %s",
                                                 words[0])
            finally:
                general_settings_file.close()
        else:
            # if file does not exist, create it and write default values.
            general_settings_file = open(fname, "x")
            general_settings_file.write("logging=false\n")
            if platform.system() == "Darwin":
                general_settings_file.write("use hotkeys=false\n")
            else:
                general_settings_file.write("use hotkeys=true\n")
            general_settings_file.write("next wallpaper hotkey=control+super+w\n")
            self.hk_binding_next = ("control", "super", "w")
            general_settings_file.write("pause wallpaper hotkey=control+super+shift+p\n")
            self.hk_binding_pause = ("control", "super", "shift", "p")
            general_settings_file.write("set_command=\n")
            general_settings_file.write("browse_default_dir=\n")
            general_settings_file.write("warn_large_img=true")
            general_settings_file.close()

    def save_settings(self):
        """Save the current state of the general settings object."""

        fname = os.path.join(CONFIG_PATH, "general_settings")
        general_settings_file = open(fname, "w")

        if self.logging:
            general_settings_file.write("logging=true\n")
        else:
            general_settings_file.write("logging=false\n")

        if self.use_hotkeys:
            general_settings_file.write("use hotkeys=true\n")
        else:
            general_settings_file.write("use hotkeys=false\n")

        if self.hk_binding_next:
            hk_string = "+".join(self.hk_binding_next)
            general_settings_file.write("next wallpaper hotkey={}\n".format(hk_string))

        if self.hk_binding_pause:
            hk_string_p = "+".join(self.hk_binding_pause)
            general_settings_file.write("pause wallpaper hotkey={}\n".format(hk_string_p))

        if self.show_help:
            general_settings_file.write("show_help_at_start=true\n")
        else:
            general_settings_file.write("show_help_at_start=false\n")

        general_settings_file.write("set_command={}\n".format(self.set_command))
        general_settings_file.write("browse_default_dir={}\n".format(self.browse_default_dir))

        if self.warn_large_img:
            general_settings_file.write("warn_large_img=true")
        else:
            general_settings_file.write("warn_large_img=false")
        general_settings_file.close()



class ProfileDataException(Exception):
    """ProfileData initialization error handler."""
    def __init__(self, message, profile_name, parse_file, errors):
        super().__init__(message)
        print(message, profile_name, parse_file)
        print(errors)


class ProfileData(object):
    """
    Central data type of Superpaper, in which wallpaper settings are recorded.

    A cornerstone goal of Superpaper is to allow the user to save wallpaper
    presets that are easy to change between. These settings include the
    images to use, slideshow timer, spanning mode etc. Profiles are saved to
    .profile files and parsed when creating a profile data object.
    """
    def __init__(self, profile_file):
        if not wpproc.RESOLUTION_ARRAY:
            msg = "Cannot parse profile, monitor resolution data is missing."
            show_message_dialog(msg)
            sp_logging.G_LOGGER(msg)
            exit()

        self.file = profile_file
        self.name = "default_profile"
        self.spanmode = "single"  # single / advanced / multi
        self.spangroups = None
        self.slideshow = True
        self.delay_list = [600]
        self.sortmode = "shuffle"  # shuffle / alphabetical / date_seeded_shuffle
        self.ppimode = False
        self.ppi_array = wpproc.NUM_DISPLAYS * [100]
        self.ppi_array_relative_density = []
        self.inches = []
        self.manual_offsets = wpproc.NUM_DISPLAYS * [(0, 0)]
        self.manual_offsets_useronly = []
        self.bezels = []
        self.bezel_px_offsets = []
        self.hk_binding = None
        self.perspective = "default"
        self.paths_array = []

        self.parse_profile(self.file)
        if self.ppimode is True:
            self.compute_relative_densities()
            if self.bezels:
                self.compute_bezel_px_offsets()
        self.file_handler = self.Filehandler(self.paths_array, self.sortmode)

    def parse_profile(self, parse_file):
        """Read wallpaper profile settings from file."""
        profile_file = open(parse_file, "r")
        try:
            for line in profile_file:
                line.strip()
                words = line.split("=")
                if words[0] == "name":
                    self.name = words[1].strip()
                elif words[0] == "spanmode":
                    wrd1 = words[1].strip().lower()
                    if wrd1 == "single":
                        self.spanmode = wrd1
                    elif wrd1 == "advanced":
                        self.spanmode = wrd1
                    elif wrd1 == "multi":
                        self.spanmode = wrd1
                    else:
                        sp_logging.G_LOGGER.info("Exception: unknown spanmode: %s \
                                in profile: %s", words[1], self.name)
                elif words[0] == "spangroups":
                    self.spangroups = []
                    groups = words[1].strip().split(",")
                    for grp in groups:
                        try:
                            ids = [int(idx) for idx in grp]
                            self.spangroups.append(sorted(list(set(ids)))) # drop duplicates
                        except ValueError:
                            self.spangroups = None
                elif words[0] == "slideshow":
                    wrd1 = words[1].strip().lower()
                    if wrd1 == "true":
                        self.slideshow = True
                    else:
                        self.slideshow = False
                elif words[0] == "delay":
                    self.delay_list = []
                    delay_strings = words[1].strip().split(";")
                    for delstr in delay_strings:
                        self.delay_list.append(float(delstr))
                elif words[0] == "sortmode":
                    wrd1 = words[1].strip().lower()
                    if wrd1 == "shuffle":
                        self.sortmode = wrd1
                    elif wrd1 == "date_seeded_shuffle":
                        self.sortmode = wrd1
                    elif wrd1 == "alphabetical":
                        self.sortmode = wrd1
                    else:
                        sp_logging.G_LOGGER.info("Exception: unknown sortmode: %s \
                                in profile: %s", words[1], self.name)
                elif words[0] == "offsets":
                    # Use PPI mode algorithm to do cuts.
                    # Defaults assume uniform pixel density
                    # if no custom values are given.
                    offs = []
                    offs_user_only = []
                    # w1,h1;w2,h2;...
                    offset_strings = words[1].strip().split(";")
                    for offstr in offset_strings:
                        res_str = offstr.split(",")
                        try:
                            offs.append((int(res_str[0]), int(res_str[1])))
                            offs_user_only.append((int(res_str[0]),
                                                   int(res_str[1])))
                        except (ValueError, IndexError):
                            offs.append((0, 0))
                            offs_user_only.append((0, 0))
                    while len(offs) < wpproc.NUM_DISPLAYS:
                        offs.append((0, 0))
                        offs_user_only.append((0, 0))
                    self.ppimode = True
                    self.manual_offsets = offs
                    self.manual_offsets_useronly = offs_user_only
                elif words[0] == "bezels":
                    bez_mm_strings = words[1].strip().split(";")
                    for bezstr in bez_mm_strings:
                        self.bezels.append(float(bezstr))
                elif words[0] == "ppi":
                    self.ppimode = True
                    # overwrite initialized arrays.
                    self.ppi_array = []
                    self.ppi_array_relative_density = []
                    ppi_strings = words[1].strip().split(";")
                    for ppistr in ppi_strings:
                        self.ppi_array.append(int(ppistr))
                elif words[0] == "diagonal_inches":
                    self.ppimode = True
                    # overwrite initialized arrays.
                    self.ppi_array = []
                    self.ppi_array_relative_density = []
                    inch_strings = words[1].strip().split(";")
                    self.inches = []
                    for inchstr in inch_strings:
                        self.inches.append(float(inchstr))
                    self.ppi_array = self.compute_ppis(self.inches)
                elif words[0] == "hotkey":
                    binding_strings = words[1].strip().split("+")
                    self.hk_binding = tuple(binding_strings)
                    # if sp_logging.DEBUG:
                    #     sp_logging.G_LOGGER.info("hkBinding: %s", self.hk_binding)
                elif words[0] == "perspective":
                    self.perspective = words[1].strip()
                    # if sp_logging.DEBUG:
                    #     sp_logging.G_LOGGER.info("perspective preset: %s", self.perspective)
                elif words[0].startswith("display"):
                    paths = words[1].strip().split(";")
                    paths = list(filter(None, paths))  # drop empty strings
                    self.paths_array.append(paths)
                else:
                    sp_logging.G_LOGGER.info("Unknown setting line in config: %s", line)
        except Exception as excep:
            profile_file.close()
            raise ProfileDataException("There was an error parsing the profile:",
                                       self.name, self.file, excep)
        finally:
            profile_file.close()

    def compute_ppis(self, inches):
        """Compute monitor PPIs from user input diagonal inches."""
        if len(inches) < wpproc.NUM_DISPLAYS:
            sp_logging.G_LOGGER.info("Exception: Number of read display diagonals was: \
                                     %s , but the number of displays was found to be: %s",
                                     str(len(inches)),
                                     str(wpproc.NUM_DISPLAYS)
                                     )
            sp_logging.G_LOGGER.info("Falling back to no PPI correction.")
            self.ppimode = False
            return wpproc.NUM_DISPLAYS * [100]
        else:
            ppi_array = []
            for inch, res in zip(inches, wpproc.RESOLUTION_ARRAY):
                diagonal_px = math.sqrt(res[0]**2 + res[1]**2)
                px_per_inch = diagonal_px / inch
                ppi_array.append(px_per_inch)
            if sp_logging.DEBUG:
                sp_logging.G_LOGGER.info("Computed PPIs: %s", ppi_array)
            return ppi_array

    def compute_relative_densities(self):
        """
        Normalizes the ppi_array list such that the max ppi has the relative value 1.0.

        This means that every other display has an equal relative density or a lesser
        value. The benefit of this normalization is that the resulting corrected
        image sections never have to be scaled up in the end, which would happen with
        relative densities of over 1.0. This presumably yields a slight improvement
        in the resulting image quality in some worst case scenarios.
        """
        if self.ppi_array:
            max_density = max(self.ppi_array)
        else:
            sp_logging.G_LOGGER("Couldn't compute relative densities: %s, %s", self.name, self.file)
            return 1
        for ppi in self.ppi_array:
            self.ppi_array_relative_density.append((1 / max_density) * float(ppi))
        # if sp_logging.DEBUG:
        #     sp_logging.G_LOGGER.info("relative pixel densities: %s",
        #                              self.ppi_array_relative_density)

    def compute_bezel_px_offsets(self):
        """Computes bezel sizes in pixels based on display PPIs."""
        if self.ppi_array:
            max_ppi = max(self.ppi_array)
        else:
            sp_logging.G_LOGGER("Couldn't compute relative densities: %s, %s", self.name, self.file)
            return 1
        
        bez_px_offs=[0]   # never offset 1st disp, anchor to it.
        inch_per_mm = 1.0 / 25.4
        for bez_mm in self.bezels:
            bez_px_offs.append(
                round(float(max_ppi) * inch_per_mm * bez_mm)
            )
        if sp_logging.DEBUG:
            sp_logging.G_LOGGER.info(
                "Bezel px calculation: initial manual offset: %s, \
                and bezel pixels: %s",
                self.manual_offsets,
                bez_px_offs)
        if len(bez_px_offs) < wpproc.NUM_DISPLAYS:
            if sp_logging.DEBUG:
                sp_logging.G_LOGGER.info(
                    "Bezel px calculation: Too few bezel mm values given! "
                    "Appending zeros."
                )
            while (len(bez_px_offs) < wpproc.NUM_DISPLAYS):
                bez_px_offs.append(0)
        elif len(bez_px_offs) > wpproc.NUM_DISPLAYS:
            if sp_logging.DEBUG:
                sp_logging.G_LOGGER.info(
                    "Bezel px calculation: Got more bezel mm values than expected!"
                )
            # Currently ignore list tail if there are too many bezel values
        # Add these horizontal offsets to manual_offsets:
        # Avoid offsetting the leftmost anchored display i==0
        for i in range(1, min(len(bez_px_offs), wpproc.NUM_DISPLAYS)):
            # Add previous offsets to ones further away to the right.
            # Each display needs to be offset by the given bezel relative to
            # the display to its left, which can be shifted relative to
            # the anchor.
            bez_px_offs[i]+=bez_px_offs[i-1]
            self.manual_offsets[i] = (self.manual_offsets[i][0] + bez_px_offs[i],
                                        self.manual_offsets[i][1])
        self.bezel_px_offsets = bez_px_offs
        if sp_logging.DEBUG:
            sp_logging.G_LOGGER.info(
                "Bezel px calculation: resulting combined manual offset: %s",
                self.manual_offsets)

    def next_wallpaper_files(self, peek=False):
        """Asks the file handler iterator for next image(s) for the wallpaper."""
        return self.file_handler.next_wallpaper_files(peek=peek)

    class Filehandler(object):
        """
        Handles picking wallpapers from the assigned paths.

        Since multiple paths are supported per monitor, this class
        lists all valid images on a monitor by monitor basis and then
        orders the list according to sortmode. Allows for shuffling of the
        wallpapers, i.e. non-repeating randomized list, which is re-randomized
        once it has been exhausted.
        """
        def __init__(self, paths_array, sortmode):
            # A list of lists if there is more than one monitor with distinct
            # input paths.
            self.all_files_in_paths = []
            self.paths_array = paths_array
            self.sortmode = sortmode
            for paths_list in paths_array:
                list_of_images = []
                for path in paths_list:
                    # Add list items to the end of the list instead of
                    # appending the list to the list.
                    if not os.path.exists(path):
                        message = "A path was not found: '{}'.\n\
Use absolute paths for best reliabilty.".format(path)
                        sp_logging.G_LOGGER.info(message)
                        show_message_dialog(message, "Error")
                        continue
                    else:
                        # List only images that are of supported type.
                        if os.path.isfile(path):
                            if path.lower().endswith(wpproc.G_SUPPORTED_IMAGE_EXTENSIONS):
                                list_of_images += [path]
                            else:
                                pass
                        else:
                            list_of_images += [os.path.join(path, f)
                                            for f in os.listdir(path)
                                            if f.lower().endswith(wpproc.G_SUPPORTED_IMAGE_EXTENSIONS)
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

        def next_wallpaper_files(self, peek=False):
            """Calls its internal iterators to give the next image for each monitor."""
            files = []
            for iterable in self.iterators:
                if peek:
                    next_image = iterable.__peek__()
                    # print("PEEKED: {}".format(next_image))
                else:
                    next_image = iterable.__next__()
                    # print("NEXT: {}".format(next_image))
                if os.path.isfile(next_image):
                    files.append(next_image)
                else:
                    # reload all files by initializing
                    if sp_logging.DEBUG:
                        sp_logging.G_LOGGER.info("Ran into an invalid file, reinitializing..")
                    self.__init__(self.paths_array, self.sortmode)
                    files = self.next_wallpaper_files()
                    break
            return files

        class ImageList:
            """Image list iterable that can reinitialize itself once it has been gone through."""
            def __init__(self, filelist, sortmode):
                self.counter = 0
                self.files = filelist
                self.sortmode = sortmode
                self.arrange_list()

            def __iter__(self):
                return self

            def __next__(self):
                if self.counter < len(self.files):
                    image = self.files[self.counter]
                else:
                    self.counter = 0
                    self.arrange_list()
                    image = self.files[self.counter]
                # print(self.counter)
                # print("next {}".format([self.files[self.counter]]))
                self.counter += 1
                return image
            
            def __peek__(self):
                if self.counter < len(self.files):
                    image = self.files[self.counter]
                else:
                    self.counter = 0
                    self.arrange_list()
                    image = self.files[self.counter]
                # print(self.counter)
                # print("peek {}".format([self.files[self.counter]]))
                return image

            def arrange_list(self):
                """Reorders the image list as requested. Mostly for reoccuring shuffling."""
                if self.sortmode == "shuffle":
                    random.shuffle(self.files)
                elif self.sortmode == "date_seeded_shuffle":
                    today = datetime.datetime.now()
                    random.Random(today.strftime("%Y%m%d%H")).shuffle(self.files)
                elif self.sortmode == "alphabetical":
                    self.files.sort()
                else:
                    sp_logging.G_LOGGER.info(
                        "ImageList.arrange_list: unknown sortmode: %s",
                        self.sortmode)



class CLIProfileData(ProfileData):
    """
    Stripped down version of the ProfileData object for CLI usage.

    Notable differences are that this can be initialized with input data
    and this redefines the next_wallpaper_files function to just return
    the images given as input.
    """

    def __init__(self, files, advanced=False, perspective=None, spangroups=None, offsets=None):
        self.name = "cli"
        self.files = []
        self.spanmode = ""  # single / multi
        self.spangroups = spangroups
        self.ppimode = False # keep this for legacy profile support
        self.perspective = perspective
        self.manual_offsets = wpproc.NUM_DISPLAYS * [(0, 0)]

        if len(files) == 1 and not advanced:
            self.spanmode = "single"
        elif advanced:
            self.spanmode = "advanced"
        else:
            self.spanmode = "multi"

        if offsets:
            off_pairs_zip = zip(*[iter(offsets)]*2)
            off_pairs = [tuple(p) for p in off_pairs_zip]
            for off, i in zip(off_pairs, range(len(self.manual_offsets))):
                self.manual_offsets[i] = off
            for pair in self.manual_offsets:
                self.manual_offsets[self.manual_offsets.index(pair)] = (int(pair[0]), int(pair[1]))

        for item in files:
            self.files.append(os.path.realpath(item))

    def next_wallpaper_files(self):
        """Returns a list of the real paths of the images given at construction time."""
        return self.files



class TempProfileData(object):
    """Data object to test the validity of user input and for saving said input into profiles."""
    def __init__(self):
        self.name = None
        self.spanmode = None
        self.spangroups = None
        self.slideshow = None
        self.delay = None
        self.sortmode = None
        self.inches = None
        self.manual_offsets = None
        self.bezels = None
        self.hk_binding = None
        self.perspective = None
        self.paths_array = []

    def save(self):
        """Saves the TempProfile into a file."""
        if self.name is not None:
            fname = os.path.join(PROFILES_PATH, self.name + ".profile")
            try:
                tpfile = open(fname, "w")
            except IOError:
                msg = "Cannot write to file {}".format(fname)
                show_message_dialog(msg, "Error")
                return None
            tpfile.write("name=" + str(self.name) + "\n")
            if self.spanmode:
                tpfile.write("spanmode=" + str(self.spanmode) + "\n")
            if self.spangroups:
                tpfile.write("spangroups=" + str(self.spangroups) + "\n")
            if self.slideshow is not None:
                tpfile.write("slideshow=" + str(self.slideshow) + "\n")
            if self.delay:
                tpfile.write("delay=" + str(self.delay) + "\n")
            if self.sortmode:
                tpfile.write("sortmode=" + str(self.sortmode) + "\n")
            if self.inches:
                tpfile.write("diagonal_inches=" + str(self.inches) + "\n")
            if self.manual_offsets:
                tpfile.write("offsets=" + str(self.manual_offsets) + "\n")
            if self.bezels:
                tpfile.write("bezels=" + str(self.bezels) + "\n")
            if self.hk_binding:
                tpfile.write("hotkey=" + str(self.hk_binding) + "\n")
            if self.perspective:
                tpfile.write("perspective=" + str(self.perspective) + "\n")
            if self.paths_array:
                for paths in self.paths_array:
                    tpfile.write("display" + str(self.paths_array.index(paths))
                                 + "paths=" + paths + "\n")

            tpfile.close()
            return fname
        else:
            print("tmp.Save(): name is not set.")
            return None

    def test_save(self):
        """Tests whether the user input for profile settings is valid."""
        valid_profile = False
        if self.name is not None and self.name.strip() != "":
            fname = os.path.join(PROFILES_PATH, self.name + ".deleteme")
            try:
                testfile = open(fname, "w")
                testfile.close()
                os.remove(fname)
            except IOError:
                msg = "Cannot write to file {}".format(fname)
                show_message_dialog(msg, "Error")
                return False
            if self.spanmode == "single":
                if len(self.paths_array) > 1:
                    msg = "When spanning a single image across all monitors, \
only one paths field is needed."
                    show_message_dialog(msg, "Error")
                    return False
            if self.spanmode == "multi":
                if len(self.paths_array) < 2:
                    msg = "When setting a different image on every display, \
each display needs its own paths field."
                    show_message_dialog(msg, "Error")
                    return False
            if self.spangroups:
                list_grps = self.spangroups.split(",")
                for grp in list_grps:
                    for idx in grp:
                        try:
                            val = int(idx)
                        except ValueError:
                            return False
            if self.slideshow is True and not self.delay:
                msg = "When using slideshow you need to enter a delay."
                show_message_dialog(msg, "Info")
                return False
            if self.delay:
                try:
                    val = float(self.delay)
                    if val < 20:
                        msg = "It is advisable to set the slideshow delay to \
be at least 20 seconds due to the time the image processing takes."
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
                    msg = "Display diagonals must be given in numeric values \
using decimal point and separated by semicolon ';'."
                    show_message_dialog(msg, "Error")
                    return False
            if self.manual_offsets:
                if self.is_list_offsets(self.manual_offsets):
                    pass
                else:
                    msg = "Display offsets must be given in (width,height) pixel \
pairs."
                    show_message_dialog(msg, "Error")
                    return False
            if self.bezels:
                if self.is_list_float(self.bezels):
                    if self.manual_offsets:
                        if len(self.manual_offsets.split(";")) < len(self.bezels.split(";")):
                            msg = "When using both offset and bezel \
corrections, take care to enter an offset for each display that you \
enter a bezel thickness."
                            show_message_dialog(msg, "Error")
                            return False
                        else:
                            pass
                    else:
                        pass
                else:
                    msg = "Display bezels must be given in millimeters using \
decimal point and separated by semicolon ';'."
                    show_message_dialog(msg, "Error")
                    return False
            if self.hk_binding:
                if self.is_valid_hotkey(self.hk_binding):
                    pass
                else:
                    msg = "Hotkey must be given as 'mod1+mod2+mod3+key'. \
Valid modifiers are 'control', 'super', 'alt', 'shift'."
                    show_message_dialog(msg, "Error")
                    return False
            if self.paths_array:
                if self.is_list_valid_paths(self.paths_array):
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

    def is_list_float(self, input_string):
        """Tests if input string is a colon separated list of floats."""
        is_floats = True
        list_input = input_string.split(";")
        for item in list_input:
            try:
                val = float(item)
            except ValueError:
                sp_logging.G_LOGGER.info("float type check failed for: '%s'", val)
                return False
        return is_floats

    def is_list_offsets(self, input_string):
        """Checks that input string is a valid list of offsets."""
        list_input = input_string.split(";")
        # if len(list_input) < wpproc.NUM_DISPLAYS:
        #     msg = "Enter an offset for every display, even if it is (0,0)."
        #     show_message_dialog(msg, "Error")
        #     return False
        try:
            for off_pair in list_input:
                offset = off_pair.split(",")
                if len(offset) != 2:
                    return False
                try:
                    val_w = int(offset[0])
                    val_h = int(offset[1])
                except ValueError:
                    sp_logging.G_LOGGER.info("int type check failed for: '%s' or '%s",
                                             val_w, val_h)
                    return False
        except TypeError:
            return False
        # Passed tests.
        return True

    def is_valid_hotkey(self, input_string):
        """A dummy / placeholder method for checking input hotkey."""
        # Validity is hard to properly verify here.
        # Instead do it when registering hotkeys at startup.
        input_string = "" + input_string
        return True

    def is_list_valid_paths(self, input_list):
        """Verifies that input list contains paths and that they're valid."""
        if input_list == [""]:
            msg = "At least one path for wallpapers must be given."
            show_message_dialog(msg, "Error")
            return False
        if "" in input_list:
            msg = "Add an image source for every display present."
            show_message_dialog(msg, "Error")
            return False
        if self.spangroups:
            num_groups = len(self.spangroups.split(','))
            if len(input_list) < num_groups:
                msg = "Add an image source for every span group."
                show_message_dialog(msg, "Error")
                return False
        for path_list_str in input_list:
            path_list = path_list_str.split(";")
            for path in path_list:
                if os.path.isdir(path) is True:
                    supported_files = [f for f in os.listdir(path)
                                       if f.endswith(wpproc.G_SUPPORTED_IMAGE_EXTENSIONS)]
                    if supported_files:
                        continue
                    else:
                        msg = "Path '{}' does not contain supported image files.".format(path)
                        show_message_dialog(msg, "Error")
                        return False
                elif os.path.isfile(path) is True:
                    if path.endswith(wpproc.G_SUPPORTED_IMAGE_EXTENSIONS):
                        continue
                    else:
                        msg = "Image '{}' is not a supported image file.".format(path)
                        show_message_dialog(msg, "Error")
                        return False
                else:
                    msg = "Path '{}' was not recognized as a directory.".format(path)
                    show_message_dialog(msg, "Error")
                    return False
        valid_pathsarray = True
        return valid_pathsarray
