#!/usr/bin/env python3

import os
import platform
import subprocess
import math
import random
import sys
import argparse
import signal
from time import sleep
from pathlib import Path
from operator import itemgetter
from threading import Timer

from PIL import Image
from screeninfo import get_monitors
try:
    import wx
    import wx.adv
    # import wx.lib.agw.hyperlink as hl
except BaseException:
    # wx = None
    # wxadv = None
    pass
if platform.system() == "Windows":
    import ctypes
elif platform.system() == "Linux":
    # KDE has special needs
    if os.environ.get("DESKTOP_SESSION") == "/usr/share/xsessions/plasma":
        import dbus


# Global variables

# list of display resolutions (width,height), use tuples.
resolutionArray = []
# list of display offsets (width,height), use tuples.
dipslayOffsetArray = []

DEBUG = False
VERBOSE = False
LOGGING = False
nDisplays = 0
canvasSize = [0, 0]
PATH = os.path.dirname(os.path.realpath(__file__))
TEMP_PATH = PATH + "/temp/"
if not os.path.isdir(TEMP_PATH):
    os.mkdir(TEMP_PATH)
PROFILES_PATH = PATH + "/profiles/"
TRAY_TOOLTIP = "Superpaper"
TRAY_ICON = PATH + "/resources/default.png"
VERSION_STRING = "0.8"
g_set_command_string = ""

if LOGGING:
    sys.stdout = open(PATH + "/log.txt", "w")


class GeneralSettingsData(object):
    def __init__(self):
        self.logging = False
        self.use_hotkeys = True
        self.hkBinding_next = None
        self.hkBinding_pause = None
        self.parse_settings()

    def parse_settings(self):
        global DEBUG, LOGGING
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
                            sys.stdout = open(PATH + "/log.txt", "w")
                    elif words[0] == "use hotkeys":
                        wrds1 = words[1].strip().lower()
                        if wrds1 == "true":
                            self.use_hotkeys = True
                        else:
                            if DEBUG:
                                print("(", words[1], ")")
                            self.use_hotkeys = False
                        if DEBUG:
                            print("use_hotkeys:", self.use_hotkeys)
                    elif words[0] == "next wallpaper hotkey":
                        binding_strings = words[1].strip().split("+")
                        self.hkBinding_next = tuple(binding_strings)
                        if DEBUG:
                            print("hkBinding_next:", self.hkBinding_next)
                    elif words[0] == "pause wallpaper hotkey":
                        binding_strings = words[1].strip().split("+")
                        self.hkBinding_pause = tuple(binding_strings)
                        if DEBUG:
                            print("hkBinding_pause:", self.hkBinding_pause)
                    elif words[0] == "set_command":
                        g_set_command_string = words[1].strip()
                    else:
                        print("Exception: Unkown general setting: ", words[0])
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


class ProfileData(object):
    # def __init__(self, name, monitorMode, wpMode, pathArray):
    def __init__(self, file):
        self.name = "default_profile"
        self.spanmode = "single"  # single / multi
        self.slideshow = True
        self.delayArray = [600]
        self.sortmode = "shuffle"  # shuffle ( random , sorted? )
        self.ppimode = False
        self.ppiArray = nDisplays * [100]
        self.ppiArrayRelDensity = []
        self.manual_offsets = nDisplays * [(0, 0)]
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
                        print("Exception: unknown spanmode: ", words[1],
                                " in profile: ", self.name)
                elif words[0] == "slideshow":
                    wrd1 = words[1].strip().lower()
                    if wrd1 == "true":
                        self.slideshow = True
                    else:
                        if DEBUG:
                            print("(", words[1], ")")
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
                        print("Exception: unknown sortmode: ", words[1],
                                " in profile: ", self.name)
                elif words[0] == "offsets":
                    # Use PPI mode algorithm to do cuts.
                    # Defaults assume uniform pixel density
                    # if no custom values are given.
                    self.ppimode = True
                    self.manual_offsets = []
                    # w1,h1;w2,h2;...
                    offsetStrings = words[1].rstrip().split(";")
                    for str in offsetStrings:
                        res_str = str.split(",")
                        self.manual_offsets.append((int(res_str[0]),
                                                    int(res_str[1])))
                elif words[0] == "bezels":
                    bezelMillimeter_Strings = words[1].rstrip().split(";")
                    for str in bezelMillimeter_Strings:
                        self.bezels.append(float(str))
                elif words[0] == "ppi":
                    self.ppimode = True
                    # overwrite initialized arrays.
                    self.ppiArray = []
                    self.ppiArrayRelDensity = []
                    ppiStrings = words[1].rstrip().split(";")
                    for str in ppiStrings:
                        self.ppiArray.append(int(str))
                elif words[0] == "diagonal_inches":
                    self.ppimode = True
                    # overwrite initialized arrays.
                    self.ppiArray = []
                    self.ppiArrayRelDensity = []
                    inchStrings = words[1].rstrip().split(";")
                    inches = []
                    for str in inchStrings:
                        inches.append(float(str))
                    self.ppiArray = self.computePPIs(inches)
                elif words[0] == "hotkey":
                    binding_strings = words[1].strip().split("+")
                    self.hkBinding = tuple(binding_strings)
                    if DEBUG:
                        print("hkBinding:", self.hkBinding)
                elif words[0].startswith("display"):
                    paths = words[1].rstrip().split(";")
                    self.pathsArray.append(paths)
                else:
                    print("Unknown setting line in config:", line)
        finally:
            f.close()

    def computePPIs(self, inches):
        if len(inches) < nDisplays:
            print("Exception: Number of read display diagonals was: "
                + len(inches)
                + ", but the number of displays was found to be: "
                + nDisplays)
            print("Falling back to no PPI correction.")
            self.ppimode = False
            return nDisplays * [100]
        else:
            ppiArray = []
            for inch, res in zip(inches, resolutionArray):
                diagonal_px = math.sqrt(res[0]**2 + res[1]**2)
                px_per_inch = diagonal_px / inch
                ppiArray.append(px_per_inch)
            if DEBUG:
                print("Computed PPIs: ", ppiArray)
            return ppiArray

    def computeRelativeDensities(self):
        max_density = max(self.ppiArray)
        for ppi in self.ppiArray:
            self.ppiArrayRelDensity.append((1 / max_density) * float(ppi))
        if DEBUG:
            print("relative pixel densities: ", self.ppiArrayRelDensity)

    def computeBezelPixelOffsets(self):
        inch_per_mm = 1.0 / 25.4
        for bez_mm, ppi in zip(self.bezels, self.ppiArray):
            self.bezel_px_offsets.append(
                round(float(ppi) * inch_per_mm * bez_mm))
        if DEBUG:
            print(
                "Bezel px calculation: initial manual offset: ",
                self.manual_offsets,
                "and bezel pixels: ",
                self.bezel_px_offsets)
        # Add these horizontal offsets to manual_offsets:
        # Avoid offsetting the leftmost anchored display i==0
        # -1 since last display doesn't have a next display.
        for i in range(len(self.bezel_px_offsets) - 1):
            self.manual_offsets[i + 1] = (self.manual_offsets[i + 1][0] +
                                          self.bezel_px_offsets[i + 1] +
                                          self.bezel_px_offsets[i], 
                                          self.manual_offsets[i + 1][1])
        if DEBUG:
            print(
                "Bezel px calculation: resulting combined manual offset: ",
                self.manual_offsets)

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
                    list_of_images += [os.path.join(path, f)
                                       for f in os.listdir(path)]
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
                        print("Ran into an invalid file, reinitializing..")
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
                        print("Shuffling files: ", self.files)
                    random.shuffle(self.files)
                    if DEBUG and VERBOSE:
                        print("Shuffled files: ", self.files)
                elif self.sortmode == "alphabetical":
                    self.files.sort()
                    if DEBUG and VERBOSE:
                        print("Sorted files: ", self.files)
                else:
                    print(
                        "ImageList.ArrangeList: unknown sortmode: ",
                        self.sortmode)


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
            for off, i in zip(off_pairs,range(len(self.manual_offsets))):
                self.manual_offsets[i] = off

        self.ppiArrayRelDensity = []
        self.bezels = bezels
        self.bezel_px_offsets = []
        self.files = files
        #
        if self.ppimode is True:
            self.computeRelativeDensities()
            if self.bezels:
                self.computeBezelPixelOffsets()

    def NextWallpaperFiles(self):
        return self.files


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
    global nDisplays, resolutionArray, dipslayOffsetArray
    resolutionArray = []
    dipslayOffsetArray = []
    monitors = get_monitors()
    nDisplays = len(monitors)
    for m_index in range(len(monitors)):
        res = []
        offset = []
        res.append(monitors[m_index].width)
        res.append(monitors[m_index].height)
        offset.append(monitors[m_index].x)
        offset.append(monitors[m_index].y)
        resolutionArray.append(tuple(res))
        dipslayOffsetArray.append(tuple(offset))
    # Check that the display offsets are sane, i.e. translate the values if
    # there are any negative values (Windows).
    # Top-most edge of the crop tuples.
    topmost_offset = min(dipslayOffsetArray, key=itemgetter(1))[1]
    if topmost_offset < 0:
        if DEBUG:
            print("Negative topmost display offset: ", dipslayOffsetArray)
        translate_offsets = []
        for offset in dipslayOffsetArray:
            translate_offsets.append((offset[0], offset[1] - topmost_offset))
        dipslayOffsetArray = translate_offsets
        if DEBUG:
            print("Sanitised display offset: ", dipslayOffsetArray)
    if DEBUG:
        print(
            "getDisplayData output: nDisplays = ",
            nDisplays,
            resolutionArray,
            dipslayOffsetArray)
        print(res, offset)


def computeCanvas(res_array):
    # Assuming horizontal display arrangement.
    canvasWidth = 0
    for res in res_array:
        canvasWidth += res[0]
    if len(res_array) == 1:
        canvasHeight = res_array[0][1]
    else:
        # Tallest display sets the canvas height with single row.
        canvasHeight = max(res_array, key=itemgetter(1))[1]
    if DEBUG:
        print(
            "res_array: ",
            res_array,
            "canvasWidth: ",
            canvasWidth,
            ", canvasHeight: ",
            canvasHeight)
    canvasSize = [canvasWidth, canvasHeight]
    return canvasSize


def computeResolutionArrayPPIcorrection(res_array, ppiArrayRelDensity):
    eff_resolutionArray = []
    for i in range(len(res_array)):
        effw = round(res_array[i][0] / ppiArrayRelDensity[i])
        effh = round(res_array[i][1] / ppiArrayRelDensity[i])
        eff_resolutionArray.append((effw, effh))
    return eff_resolutionArray


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
            print(
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
            print(
                "Error: result image not of correct size. Cropped size: ",
                cropped_res.size,
                " desired size: ",
                res)
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
            print(
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
            print(
                "Error: result image not of correct size. Cropped size: ",
                cropped_res.size,
                " desired size: ",
                res)
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
        print("get_all_centers: Not enough manual offsets: ", len(
            manual_offsets), " for displays: ", len(resarr_eff))
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
        print("centers: ", centers)
    return centers


def get_lefttop_from_center(center, res):
    return (center[0] - round(res[0] / 2), center[1] - round(res[1] / 2))


def get_rightbottom_from_lefttop(lefttop, res):
    return (lefttop[0] + res[0], lefttop[1] + res[1])


def get_horizontal_radius(res):
    return round(res[0] / 2)


def computeCropTuples(resolutionArray_eff, manual_offsets):
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
    centers = get_all_centers(resolutionArray_eff, manual_offsets)
    for center, res in zip(centers, resolutionArray_eff):
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
            print("crop_tuples: ", crop_tuples)
        return crop_tuples  # [(left, up, right, bottom),...]
    else:
        crop_tuples_translated = translate_crops(
            crop_tuples, (leftmost, topmost))
        if DEBUG:
            print("crop_tuples_translated: ", crop_tuples_translated)
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
        print(file)
    img = Image.open(file)
    canvasTuple = tuple(computeCanvas(resolutionArray))
    img_resize = resizeToFill(img, canvasTuple)
    if DEBUG:
        print(
            "resized image to size: ",
            img_resize.size,
            " to fill canvas of size: ",
            canvasTuple)
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
        print(file)
    img = Image.open(file)
    resolutionArray_eff = computeResolutionArrayPPIcorrection(
        resolutionArray, profile.ppiArrayRelDensity)

    # Cropping now sections of the image to be shown, USE EFFECTIVE WORKING
    # SIZES. Also EFFECTIVE SIZE Offsets are now required.
    manual_offsets = profile.manual_offsets
    cropped_images = []
    crop_tuples = computeCropTuples(resolutionArray_eff, manual_offsets)
    # larger working size needed to fill all the normalized lower density
    # displays. Takes account manual offsets that might require extra space.
    canvasTuple_eff = tuple(computeWorkingCanvas(crop_tuples))
    # Image is now the height of the eff tallest display + possible manual
    # offsets and the width of the combined eff widths + possible manual
    # offsets.
    img_workingsize = resizeToFill(img, canvasTuple_eff)
    if DEBUG:
        print(
            "ppi_corr: resized image to size: ",
            img_workingsize.size,
            " to fill canvas of size: ",
            canvasTuple_eff)
    # Simultaneously make crops at working size and then resize down to actual
    # resolution from resolutionArray as needed.
    for crop, res in zip(crop_tuples, resolutionArray):
        crop_img = img_workingsize.crop(crop)
        if crop_img.size == res:
            cropped_images.append(crop_img)
        else:
            crop_img = crop_img.resize(res, resample=Image.LANCZOS)
            cropped_images.append(crop_img)
    # Combine crops to a single canvas of the size of the actual desktop
    # actual combined size of the display resolutions
    canvasTuple_fin = tuple(computeCanvas(resolutionArray))
    combinedImage = Image.new("RGB", canvasTuple_fin, color=0)
    combinedImage.load()
    for i in range(len(cropped_images)):
        combinedImage.paste(cropped_images[i], dipslayOffsetArray[i])
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
        print(files)
    img_resized = []
    for file, res in zip(files, resolutionArray):
        image = Image.open(file)
        img_resized.append(resizeToFill(image, res))
    canvasTuple = tuple(computeCanvas(resolutionArray))
    combinedImage = Image.new("RGB", canvasTuple, color=0)
    combinedImage.load()
    for i in range(len(files)):
        combinedImage.paste(img_resized[i], dipslayOffsetArray[i])
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
        print("Unknown platform.system(): ", pltform)


def setWallpaper_linux(outputfile):
    file = "file://" + outputfile
    set_command = g_set_command_string
    if DEBUG:
        print(file)
    # subprocess.run(["gsettings", "set", "org.cinnamon.desktop.background",
    # "picture-uri", file])  # Old working command for backup

    desk_env = os.environ.get("DESKTOP_SESSION")
    if DEBUG:
        print("DESKTOP_SESSION is: '{env}'".format(env=desk_env))

    if set_command != "":
        if set_command == "feh":
            subprocess.run("feh", " --bg-scale", "--no-xinerama", outputfile)
        else:
            os.system(set_command.format(image=outputfile))
    elif desk_env in ["gnome", "gnome-wayland", "unity", "ubuntu"]:
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
    elif desk_env in ["pantheon"]:
        subprocess.run(["set-wallpaper", outputfile])
    elif desk_env in ["xfce", "xubuntu"]:
        read_prop = subprocess.Popen(["xfconf-query",
                                      "-c",
                                      "xfce4-desktop",
                                      "-p",
                                      "/backdrop",
                                      "-l"],
                                     stdout=subprocess.PIPE)
        props = read_prop.stdout.read().decode("utf-8").split("\n")
        for prop in props:
            if "last-image" in prop or "image-path" in prop:
                os.system(
                    "xfconf-query -c xfce4-desktop -p " +
                    prop +
                    " -s ''")
                os.system(
                    "xfconf-query -c xfce4-desktop -p " +
                    prop +
                    " -s '%s'" %
                    outputfile)
            if "image-show" in prop:
                os.system(
                    "xfconf-query -c xfce4-desktop -p " +
                    prop +
                    " -s 'true'")
    elif desk_env in ["lubuntu", "Lubuntu"]:
        subprocess.run("pcmanfm", "-w", outputfile)
    elif desk_env in ["/usr/share/xsessions/plasma"]:
        kde_is_a_very_special_de(outputfile)
    elif "i3" in desk_env:
        subprocess.run("feh", " --bg-scale", "--no-xinerama", outputfile)
    else:
        if set_command == "":
            print(
                "Your DE could not be detected to set the wallpaper. \
                You need to set the 'set_command' option in your \
                settings file superpaper/general_settings")
            sys.exit(1)
        else:
            os.system(set_command.format(image=outputfile))


def kde_is_a_very_special_de(outputfile):
    script = """
var listDesktops = desktops();
print (listDesktops);
d = listDesktops[{index}];
d.wallpaperPlugin = "org.kde.image";
d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
d.writeConfig("Image", "file://{filename}")
"""
    # outputfile needs to be split into monitor pieces since KDE is special
    img = Image.open(outputfile)
    outputname = os.path.splitext(outputfile)[0]
    img_names = []
    id = 0
    for res, offset in zip(resolutionArray, dipslayOffsetArray):
        left = offset[0]
        top = offset[1]
        right = left + res[0]
        bottom = top + res[1]
        crop_tuple = (left, top, right, bottom)
        cropped_img = img.crop(crop_tuple)
        fname = outputname + "-kde-" + str(id) + ".png"
        img_names.append(fname)
        cropped_img.save(fname, "PNG")
        id += 1
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
    if "-a" in outputfile:
        oldfileid = "-b"
    elif "-b" in outputfile:
        oldfileid = "-a"
    else:
        print("problem identifying output file parity.")
        sys.exit(1)
    for f in os.listdir(TEMP_PATH):
        if oldfileid in f:
            os.remove(os.path.join(TEMP_PATH, f))


def changeWallpaperJob(profile):
    if profile.spanmode.startswith("single") and profile.ppimode is False:
        spanSingleImage(profile)
    elif profile.spanmode.startswith("single") and profile.ppimode is True:
        spanSingleImagePPIcorrection(profile)
    elif profile.spanmode.startswith("multi"):
        setMultipleImages(profile)
    else:
        print("Unkown profile spanmode: (", profile.spanmode, ")")


def runProfileJob(profile):
    repeating_timer = None
    getDisplayData()  # Check here so new profile has fresh data.
    if DEBUG:
        print("running profile job with profile: ", profile.name)

    if not profile.slideshow:
        if DEBUG:
            print("Running a one-off wallpaper change.")
        changeWallpaperJob(profile)
    elif profile.slideshow:
        if DEBUG:
            print("Running wallpaper slideshow.")
        changeWallpaperJob(profile)
        repeating_timer = RepeatedTimer(
            profile.delayArray[0], changeWallpaperJob, profile)
    return repeating_timer


def quickProfileJob(profile):
    # Look for old temp image:
    files = [i for i in os.listdir(TEMP_PATH)
            if os.path.isfile(os.path.join(TEMP_PATH,i))
            and i.startswith(profile.name + "-")]
    if DEBUG:
        print("quickswitch file lookup: ", files)
    if files:
        setWallpaper(os.path.join(TEMP_PATH, files[0]))
    else:
        if DEBUG:
            print("Old file for quickswitch was not found.", files)


# Profile and data handling
def listProfiles():
    files = sorted(os.listdir(PROFILES_PATH))
    profile_list = []
    for i in range(len(files)):
        profile_list.append(ProfileData(PROFILES_PATH + files[i]))
        if DEBUG:
            print("Listed profile:", profile_list[i].name)
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
                    print("read profile name from 'running_profile':", 
                        profname)
                profile = ProfileData(PROFILES_PATH + profname + ".txt")
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

def create_menu_item(menu, label, func, *args, **kwargs):
    item = wx.MenuItem(menu, -1, label, **kwargs)
    menu.Bind(wx.EVT_MENU, lambda event: func(event, *args), id=item.GetId())
    menu.Append(item)
    return item

try:
    class TaskBarIcon(wx.adv.TaskBarIcon):
        def __init__(self, frame):
            g_settings = GeneralSettingsData()

            self.frame = frame
            super(TaskBarIcon, self).__init__()
            self.set_icon(TRAY_ICON)
            self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
            # profile initialization
            getDisplayData()
            self.repeating_timer = None
            self.pause_item = None
            self.is_paused = False
            if DEBUG:
                print("START Listing profiles for menu.")
            self.list_of_profiles = listProfiles()
            if DEBUG:
                print("END Listing profiles for menu.")
            # Should now return an object if a previous profile was written or
            # None if no previous data was found
            self.active_profile = readActiveProfile()
            self.start_prev_profile(self.active_profile)
            if self.active_profile is None:
                print("Starting up the first profile found.")
                self.start_profile(wx.EVT_MENU, self.list_of_profiles[0])

            if g_settings.use_hotkeys is True:
                try:
                    # import keyboard # https://github.com/boppreh/keyboard
                    from system_hotkey import SystemHotkey
                except Exception as e:
                    print(
                        "Could not import keyboard hotkey hook library, \
                        hotkeys will not work. Exception: ",
                        e)
                try:
                    # Keyboard bindings: https://github.com/boppreh/keyboard
                    #
                    # Alternative KB bindings for X11 systems and Windows:
                    # system_hotkey https://github.com/timeyyy/system_hotkey
                    seen_binding = set()
                    hk = SystemHotkey(check_queue_interval=0.05)
                    hk2 = SystemHotkey(
                        consumer=self.profile_consumer,
                        check_queue_interval=0.05)
                    # register general bindings
                    if g_settings.hkBinding_next not in seen_binding:
                        hk.register(
                            g_settings.hkBinding_next,
                            callback=lambda x: self.next_wallpaper(wx.EVT_MENU))
                        seen_binding.add(g_settings.hkBinding_next)
                    if g_settings.hkBinding_pause not in seen_binding:
                        hk.register(
                            g_settings.hkBinding_pause,
                            callback=lambda x: self.pause_timer(wx.EVT_MENU))
                        seen_binding.add(g_settings.hkBinding_pause)
                    hk.register(('control', 'super', 'shift', 'q'),
                                callback=lambda x: self.on_exit(wx.EVT_MENU))
                    # register profile specific bindings
                    for profile in self.list_of_profiles:
                        if DEBUG:
                            print(
                                "Registering binding: ",
                                profile.hkBinding,
                                "for profile: ",
                                profile.name)
                        if (profile.hkBinding is not None and 
                                profile.hkBinding not in seen_binding):
                            hk2.register(profile.hkBinding, profile)
                            seen_binding.add(profile.hkBinding)
                        elif profile.hkBinding in seen_binding:
                            print(
                                "Could not register hotkey:",
                                profile.hkBinding,
                                "for profile:",
                                profile.name,
                                ". It is already registered elsewhere.")
                except Exception as e:
                    if DEBUG:
                        print("Coulnd't register hotkeys, exception:")
                        print(e)

        def profile_consumer(self, event, hotkey, profile):
            if DEBUG:
                print("Profile object is: ", profile)
            self.start_profile(wx.EVT_MENU, profile[0][0])

        def CreatePopupMenu(self):
            menu = wx.Menu()
            create_menu_item(menu, "Open config folder", self.open_config)
            create_menu_item(menu, "Reload profiles", self.reload_profiles)
            menu.AppendSeparator()
            for item in self.list_of_profiles:
                create_menu_item(menu, item.name, self.start_profile, item)
            menu.AppendSeparator()
            create_menu_item(menu, "Next wallpaper", self.next_wallpaper)
            self.pause_item = create_menu_item(
                menu, "Pause timer", self.pause_timer, kind=wx.ITEM_CHECK)
            self.pause_item.Check(self.is_paused)
            menu.AppendSeparator()
            create_menu_item(menu, 'About', self.on_about)
            create_menu_item(menu, 'Exit', self.on_exit)
            return menu

        def set_icon(self, path):
            icon = wx.Icon(path)
            self.SetIcon(icon, TRAY_TOOLTIP)

        def on_left_down(self, *event):
            print('Tray icon was left-clicked.')

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

        def reload_profiles(self, event):
            self.list_of_profiles = listProfiles()

        def start_prev_profile(self, profile):
            if profile is None:
                print("No previous profile was found.")
            else:
                self.repeating_timer = runProfileJob(profile)

        def start_profile(self, event, profile):
            if DEBUG:
                print("Start profile: ", profile.name)
            if profile is None:
                print(
                    "start_profile: profile is None. \
                    Do you have any profiles in /profiles?")
            elif self.active_profile is not None:
                if DEBUG:
                    print(
                        "Check if the starting profile is already running: ",
                        profile.name)
                    print(
                        "name check: ",
                        profile.name,
                        self.active_profile.name)
                if profile.name == self.active_profile.name:
                    print(
                        "start_profile: Do nothing if attempting to \
                        change to the current profile.")
                else:
                    if (self.repeating_timer is not None and
                            self.repeating_timer.is_running):
                        self.repeating_timer.stop()
                    if DEBUG:
                        print(
                            "Running quick profile job with profile: ",
                            profile.name)
                    quickProfileJob(profile)
                    if DEBUG:
                        print(
                            "Starting timed profile job with profile: ",
                            profile.name)
                    self.repeating_timer = runProfileJob(profile)
                    self.active_profile = profile
                    writeActiveProfile(profile.name)
                    if DEBUG:
                        print("Wrote active profile: ", profile.name)
            else:
                if (self.repeating_timer is not None
                        and self.repeating_timer.is_running):
                    self.repeating_timer.stop()
                if DEBUG:
                    print(
                        "Running quick profile job with profile: ",
                        profile.name)
                quickProfileJob(profile)
                if DEBUG:
                    print(
                        "Starting timed profile job with profile: ",
                        profile.name)
                self.repeating_timer = runProfileJob(profile)
                self.active_profile = profile
                writeActiveProfile(profile.name)
                if DEBUG:
                    print("Wrote active profile: ", profile.name)

        def next_wallpaper(self, event):
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
                    print("Paused timer")
            elif (self.repeating_timer is not None
                  and not self.repeating_timer.is_running):
                self.repeating_timer.start()
                self.is_paused = False
                if DEBUG:
                    print("Resumed timer")
            else:
                print("Current profile isn't using a timer.")

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
            info.SetWebSite('http://www.github.com')
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
        print("Failed to define tray applet classes. Is wxPython installed?")
        print(e)


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
                            Substitute /path/to/image.jpg by '{image}'.")
    args = parser.parse_args()

    if DEBUG:
        print(args.setimages)
        print(args.ppi)
        print(args.inches)
        print(args.bezels)
        print(args.offsets)
        print(args.command)
    if not args.setimages:
        print("Exception: You must pass image(s) to set as \
            wallpaper with '-s' or '--setimages'. Exiting.")
        exit()
    else:
        for file in args.setimages:
            if not os.path.isfile(file):
                print("Exception: One of the passed images was not \
                    a file: ({fname}). Exiting.".format(fname=file))
                exit()
    if args.bezels and not (args.ppi or args.inches):
        print("The bezel correction feature needs display PPIs, \
                provide these with --inches or --ppi.")
    if len(args.offsets) % 2 != 0:
        print("Exception: Number of offset pixels not even. If passing manual \
            offsets, give width and height offset for each display, even if \
            not actually offsetting every display. Exiting.")
        exit()
    if args.command:
        if len(args.command) > 1:
            print("Exception: Remember to put the custom command in quotes. \
            Exiting.")
            exit()
        g_set_command_string = args.command

    getDisplayData()
    profile = CLIProfileData(args.setimages,
                             args.ppi,
                             args.inches,
                             args.bezels,
                             args.offsets,
                             )
    changeWallpaperJob(profile)


def tray_loop():
    if not os.path.isdir(PROFILES_PATH):
        os.mkdir(PROFILES_PATH)
    app = App(False)
    app.MainLoop()

# MAIN


def main():
    if not len(sys.argv) > 1:
        tray_loop()
    else:
        cli_logic()


if __name__ == "__main__":
    main()
