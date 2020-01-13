"""
New wallpaper configuration GUI for Superpaper.
"""
import os

import superpaper.sp_logging as sp_logging
from superpaper.data import GeneralSettingsData, ProfileData, TempProfileData, CLIProfileData, list_profiles
from superpaper.message_dialog import show_message_dialog
from superpaper.wallpaper_processing import NUM_DISPLAYS, get_display_data, change_wallpaper_job
from superpaper.sp_paths import PATH, CONFIG_PATH, PROFILES_PATH

try:
    import wx
    import wx.adv
except ImportError:
    exit()


class ConfigFrame(wx.Frame):
    """Wallpaper configuration dialog frame base class."""
    def __init__(self, parent_tray_obj):
        wx.Frame.__init__(self, parent=None, title="Superpaper Wallpaper Configuration")
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        config_panel = WallpaperPanel(self, parent_tray_obj)
        self.frame_sizer.Add(config_panel, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(self.frame_sizer)
        self.Fit()
        self.Layout()
        self.Center()
        self.Show()

class WallpaperPanel(wx.Panel):
    """This class defines the wallpaper config dialog UI."""
    def __init__(self, parent, parent_tray_obj):
        wx.Panel.__init__(self, parent)
        self.frame = parent
        self.parent_tray_obj = parent_tray_obj
        self.sizer_main = wx.BoxSizer(wx.VERTICAL)
        self.sizer_top_half = wx.BoxSizer(wx.HORIZONTAL) # wallpaper/monitor preview
        self.sizer_bottom_half = wx.BoxSizer(wx.HORIZONTAL) # settings, buttons etc
        # bottom_half: setting sizers
        self.sizer_profiles = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_setting_sizers = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_settings_left = wx.BoxSizer(wx.VERTICAL)
        self.sizer_settings_right = wx.BoxSizer(wx.VERTICAL)
        # bottom_half: bottom button row
        self.sizer_bottom_buttonrow = wx.BoxSizer(wx.HORIZONTAL)

        # top half

        
        # bottom half
        
        # profile sizer contents
        self.button_new = wx.Button(self, label="New")
        self.button_save = wx.Button(self, label="Save")
        self.button_delete = wx.Button(self, label="Delete")

        # settings sizer left contents
        #    span mode
        self.sizer_setting_span_mode = wx.StaticBoxSizer(wx.VERTICAL, self, "Span mode")

        self.sizer_setting_slideshow = wx.StaticBoxSizer(wx.VERTICAL, self, "Slideshow")

        self.sizer_setting_hotkey = wx.StaticBoxSizer(wx.VERTICAL, self, "Hotkey")

        # settings sizer right contents

        # bezel correction TODO TBD whether to put this on left or right

        # paths sizer contents contents

        # bottom button row contents
        self.button_align_test = wx.Button(self, label="Align Test")    # TODO maybe align left?
        self.button_help = wx.Button(self, label="Help")                # TODO maybe align left?
        self.button_apply = wx.Button(self, label="Apply")
        self.button_close = wx.Button(self, label="Close")

        # Add sub-sizers to bottom_half

        # Collect items at main sizer
        self.sizer_main.Add(self.sizer_top_half, 0, wx.CENTER|wx.EXPAND)
        self.sizer_main.Add(self.sizer_bottom_half, 0, wx.CENTER|wx.EXPAND)

        self.SetSizer(self.sizer_main)
        self.sizer_main.Fit(parent)

        ### End __init__.