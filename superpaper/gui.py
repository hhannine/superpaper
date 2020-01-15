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
        self.tc_width = 160
        # top half
        self.wpprev_pnl = WallpaperPreviewPanel(self.frame)
        self.sizer_top_half.Add(self.wpprev_pnl, 0, wx.CENTER|wx.EXPAND)
        
        # bottom half
        
        # profile sizer contents
        self.create_sizer_profiles()

        # settings sizer left contents
        self.create_sizer_settins_left()

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
        self.sizer_bottom_buttonrow.AddStretchSpacer()
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

    #
    # Sizer creation methods
    #
    def create_sizer_profiles(self):
        # choice menu
        self.list_of_profiles = list_profiles()
        self.profnames = []
        for prof in self.list_of_profiles:
            self.profnames.append(prof.name)
        self.profnames.append("Create a new profile")
        self.choice_profiles = wx.Choice(self, -1, name="ProfileChoice", choices=self.profnames)
        self.choice_profiles.Bind(wx.EVT_CHOICE, self.onSelect)
        st_choice_profiles = wx.StaticText(self, -1, "Setting profiles:")
        # name txt ctrl
        st_name = wx.StaticText(self, -1, "Profile name:")
        self.tc_name = wx.TextCtrl(self, -1, size=(self.tc_width, -1))
        # buttons
        self.button_new = wx.Button(self, label="New")
        self.button_save = wx.Button(self, label="Save")
        self.button_delete = wx.Button(self, label="Delete")

        # Add elements to the sizer
        self.sizer_profiles.Add(st_choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(st_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.tc_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_new, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_delete, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_save, 0, wx.CENTER|wx.ALL, 5)

    def create_sizer_settins_left(self):
        #    span mode
        self.sizer_setting_span_mode = wx.StaticBoxSizer(wx.VERTICAL, self, "Span mode")

        self.sizer_setting_slideshow = wx.StaticBoxSizer(wx.VERTICAL, self, "Slideshow")
        # st_slide = wx.StaticText(self, -1, "Slideshow")
        st_sshow_sort = wx.StaticText(self, -1, "Slideshow order:")
        self.ch_sshow_sort = wx.Choice(self, -1, name="SortChoice",
                                 size=(self.tc_width, -1),
                                 choices=["Shuffle", "Alphabetical"])
        st_sshow_delay = wx.StaticText(self, -1, "Delay:")
        st_sshow_delay_units = wx.StaticText(self, -1, "minutes")
        self.tc_sshow_delay = wx.TextCtrl(self, -1, size=(self.tc_width, -1))
        self.cb_slideshow = wx.CheckBox(self, -1, "Slideshow")  # Put the title in the left column
        # TODO disable ch_sshow_sort and tc_sshow_delay based on the Check state of the CheckBox


        self.sizer_setting_hotkey = wx.StaticBoxSizer(wx.VERTICAL, self, "Hotkey")

        self.sizer_settings_left.Add(self.sizer_setting_span_mode, 0, wx.CENTER|wx.EXPAND)
        self.sizer_settings_left.Add(self.sizer_setting_slideshow, 0, wx.CENTER|wx.EXPAND)
        self.sizer_settings_left.Add(self.sizer_setting_hotkey, 0, wx.CENTER|wx.EXPAND)


    def update_choiceprofile(self):
        """Reload profile list into the choice box."""
        self.list_of_profiles = list_profiles()
        self.profnames = []
        for prof in self.list_of_profiles:
            self.profnames.append(prof.name)
        self.profnames.append("Create a new profile")
        self.choice_profiles.SetItems(self.profnames)

    #
    # Top level button definitions
    #
    def onClose(self, event):
        """Closes the profile config panel."""
        self.frame.Close(True)

    def onSelect(self, event):
        """Acts once a profile is picked in the dropdown menu."""
        event_object = event.GetEventObject()
        if event_object.GetName() == "ProfileChoice":
            item = event.GetSelection()
            if event.GetString() == "Create a new profile":
                self.onCreateNewProfile(event)
            else:
                self.populate_fields(self.list_of_profiles[item])
        else:
            pass

    def onApply(self, event):
        """Applies the currently open profile. Saves it first."""
        saved_file = self.onSave(event)
        print(saved_file)
        if saved_file is not None:
            saved_profile = ProfileData(saved_file)
            self.parent_tray_obj.reload_profiles(event)
            self.parent_tray_obj.start_profile(event, saved_profile)
        else:
            pass

    def onSave(self, event):
        """Saves currently open profile into file. A test method is called to verify data."""
        # tmp_profile = TempProfileData()
        # tmp_profile.name = self.tc_name.GetLineText(0)
        # tmp_profile.spanmode = self.ch_span.GetString(self.ch_span.GetSelection()).lower()
        # tmp_profile.slideshow = self.cb_slideshow.GetValue()
        # tmp_profile.delay = self.tc_delay.GetLineText(0)
        # tmp_profile.sortmode = self.ch_sort.GetString(self.ch_sort.GetSelection()).lower()
        # tmp_profile.inches = self.tc_inches.GetLineText(0)
        # tmp_profile.manual_offsets = self.tc_offsets.GetLineText(0)
        # tmp_profile.bezels = self.tc_bez.GetLineText(0)
        # tmp_profile.hk_binding = self.tc_hotkey.GetLineText(0)
        # for text_field in self.paths_controls:
        #     tmp_profile.paths_array.append(text_field.GetLineText(0))

        # sp_logging.G_LOGGER.info(tmp_profile.name)
        # sp_logging.G_LOGGER.info(tmp_profile.spanmode)
        # sp_logging.G_LOGGER.info(tmp_profile.slideshow)
        # sp_logging.G_LOGGER.info(tmp_profile.delay)
        # sp_logging.G_LOGGER.info(tmp_profile.sortmode)
        # sp_logging.G_LOGGER.info(tmp_profile.inches)
        # sp_logging.G_LOGGER.info(tmp_profile.manual_offsets)
        # sp_logging.G_LOGGER.info(tmp_profile.bezels)
        # sp_logging.G_LOGGER.info(tmp_profile.hk_binding)
        # sp_logging.G_LOGGER.info(tmp_profile.paths_array)

        # if tmp_profile.test_save():
        #     saved_file = tmp_profile.save()
        #     self.update_choiceprofile()
        #     self.parent_tray_obj.reload_profiles(event)
        #     self.parent_tray_obj.register_hotkeys()
        #     # self.parent_tray_obj.register_hotkeys()
        #     self.choice_profiles.SetSelection(self.choice_profiles.FindString(tmp_profile.name))
        #     return saved_file
        # else:
        #     sp_logging.G_LOGGER.info("test_save failed.")
        #     return None
        pass

    def onCreateNewProfile(self, event):
        """Empties the config dialog fields."""
        # self.choice_profiles.SetSelection(
        #     self.choice_profiles.FindString("Create a new profile")
        #     )

        # self.tc_name.ChangeValue("")
        # self.tc_delay.ChangeValue("")
        # self.tc_offsets.ChangeValue("")
        # self.tc_inches.ChangeValue("")
        # self.tc_bez.ChangeValue("")
        # self.tc_hotkey.ChangeValue("")

        # # Paths displays: get number to show from profile.
        # while len(self.paths_controls) < 1:
        #     self.onAddDisplay(wx.EVT_BUTTON)
        # while len(self.paths_controls) > 1:
        #     self.onRemoveDisplay(wx.EVT_BUTTON)
        # for text_field in self.paths_controls:
        #     text_field.ChangeValue("")

        # self.cb_slideshow.SetValue(False)
        # self.ch_span.SetSelection(-1)
        # self.ch_sort.SetSelection(-1)
        pass

    def onDeleteProfile(self, event):
        """Deletes the currently selected profile after getting confirmation."""
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

    def onAlignTest(self, event):
        """Align test, takes alignment settings from open profile and sets a test image wp."""
        # Use the settings currently written out in the fields!
        testimage = [os.path.join(PATH, "superpaper/resources/test.png")]
        if not os.path.isfile(testimage[0]):
            print(testimage)
            msg = "Test image not found in {}.".format(testimage)
            show_message_dialog(msg, "Error")
        ppi = None
        inches = self.tc_inches.GetLineText(0).split(";")
        if (inches == "") or (len(inches) < NUM_DISPLAYS):
            msg = "You must enter a diagonal inch value for every \
display, serparated by a semicolon ';'."
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
        get_display_data()
        profile = CLIProfileData(testimage,
                                 ppi,
                                 inches,
                                 bezels,
                                 flat_offsets,
                                )
        change_wallpaper_job(profile)

    def onHelp(self, event):
        """Open help dialog."""
        help_frame = HelpFrame()



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
        wx.Panel.__init__(self, parent, size=(1000,666))
        self.frame = parent
        self.SetBackgroundColour(wx.BLACK)
