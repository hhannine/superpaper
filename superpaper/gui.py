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
        config_panel = WallpaperSettingsPanel(self, parent_tray_obj)
        self.frame_sizer.Add(config_panel, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(self.frame_sizer)
        self.Fit()
        self.Layout()
        self.Center()
        self.Show()

class WallpaperSettingsPanel(wx.Panel):
    """This class defines the wallpaper config dialog UI."""
    def __init__(self, parent, parent_tray_obj):
        wx.Panel.__init__(self, parent)
        self.frame = parent
        self.parent_tray_obj = parent_tray_obj
        self.sizer_main = wx.BoxSizer(wx.VERTICAL)
        self.sizer_top_half = wx.BoxSizer(wx.HORIZONTAL) # wallpaper/monitor preview
        self.sizer_bottom_half = wx.BoxSizer(wx.VERTICAL) # settings, buttons etc
        # bottom_half: setting sizers
        self.sizer_profiles = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_setting_sizers = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_settings_left = wx.BoxSizer(wx.VERTICAL)
        self.sizer_settings_right = wx.BoxSizer(wx.VERTICAL)
        # bottom_half: bottom button row
        self.sizer_bottom_buttonrow = wx.BoxSizer(wx.HORIZONTAL)

        # top half
        self.wpprev_pnl = WallpaperPreviewPanel(self.frame)
        self.sizer_top_half.Add(self.wpprev_pnl, 0, wx.CENTER|wx.EXPAND)
        
        # bottom half
        
        # profile sizer contents
        # choice menu
        # name txt ctrl
        self.button_new = wx.Button(self, label="New")
        self.button_save = wx.Button(self, label="Save")
        self.button_delete = wx.Button(self, label="Delete")
        self.sizer_profiles.Add(self.button_new, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_delete, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_save, 0, wx.CENTER|wx.ALL, 5)

        # settings sizer left contents
        #    span mode
        self.sizer_setting_span_mode = wx.StaticBoxSizer(wx.VERTICAL, self, "Span mode")

        self.sizer_setting_slideshow = wx.StaticBoxSizer(wx.VERTICAL, self, "Slideshow")

        self.sizer_setting_hotkey = wx.StaticBoxSizer(wx.VERTICAL, self, "Hotkey")

        self.sizer_settings_left.Add(self.sizer_setting_span_mode, 0, wx.CENTER|wx.EXPAND)
        self.sizer_settings_left.Add(self.sizer_setting_slideshow, 0, wx.CENTER|wx.EXPAND)
        self.sizer_settings_left.Add(self.sizer_setting_hotkey, 0, wx.CENTER|wx.EXPAND)

        # settings sizer right contents
        # TODO Some settings in the right column are CONDITIONAL: bezel corr, maybe diag inches?
        # bezel correction TODO TBD whether to put this on left or right

        # self.sizer_settings_right.Add(self.sizer_setting_, 0, wx.CENTER|wx.EXPAND)

        # paths sizer contents
        self.sizer_setting_paths = wx.StaticBoxSizer(wx.VERTICAL, self, "Wallpaper paths")

        self.sizer_settings_right.Add(self.sizer_setting_paths, 0, wx.CENTER|wx.EXPAND)



        # bottom button row contents
        self.button_help = wx.Button(self, label="Help")                # TODO maybe align left?
        self.button_align_test = wx.Button(self, label="Align Test")    # TODO maybe align left?
        self.button_apply = wx.Button(self, label="Apply")
        self.button_close = wx.Button(self, label="Close")
        self.sizer_bottom_buttonrow.Add(self.button_help, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_bottom_buttonrow.Add(self.button_align_test, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_bottom_buttonrow.Add(self.button_apply, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.sizer_bottom_buttonrow.Add(self.button_close, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        # Add sub-sizers to bottom_half
        self.sizer_setting_sizers.Add(self.sizer_settings_left, 0, wx.CENTER|wx.EXPAND)
        self.sizer_setting_sizers.Add(self.sizer_settings_right, 0, wx.CENTER|wx.EXPAND)

        self.sizer_bottom_half.Add(self.sizer_profiles, 0, wx.CENTER|wx.EXPAND)
        self.sizer_bottom_half.Add(self.sizer_setting_sizers, 0, wx.CENTER|wx.EXPAND)
        self.sizer_bottom_half.Add(self.sizer_bottom_buttonrow, 0, wx.CENTER|wx.EXPAND)

        # Collect items at main sizer
        self.sizer_main.Add(self.sizer_top_half, 0, wx.CENTER|wx.EXPAND)
        self.sizer_main.Add(self.sizer_bottom_half, 0, wx.CENTER|wx.EXPAND)

        self.SetSizer(self.sizer_main)
        self.sizer_main.Fit(parent)

        ### End __init__.



class WallpaperPreviewPanel(wx.Panel):
    """
    Wallpaper & monitor preview panel.

    Previews wallpaper settings as applied to the input image.
    In the advanced mode allows the user to enter their monitor
    setup, which will then be saved into a file as a monitor
    configuration. Method looks up saved setups to see if one
    exists that matches the given resolutions, offsets and sizes.
    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size=(1200,800))
        self.frame = parent
        self.SetBackgroundColour(wx.BLACK)
