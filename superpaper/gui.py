"""
New wallpaper configuration GUI for Superpaper.
"""
import os

import superpaper.sp_logging as sp_logging
import superpaper.wallpaper_processing as wpproc
from superpaper.configuration_dialogs import BrowsePaths, HelpFrame
from superpaper.data import GeneralSettingsData, ProfileData, TempProfileData, CLIProfileData, list_profiles
from superpaper.message_dialog import show_message_dialog
from superpaper.sp_paths import PATH, CONFIG_PATH, PROFILES_PATH
from superpaper.wallpaper_processing import NUM_DISPLAYS, get_display_data, change_wallpaper_job

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
        self.sizer_settings_right = wx.BoxSizer(wx.HORIZONTAL)
        # bottom_half: bottom button row
        self.sizer_bottom_buttonrow = wx.BoxSizer(wx.HORIZONTAL)
        # settings GUI properties
        self.tc_width = 160  # standard width for wx.TextCtrl etc elements.
        self.show_advanced_settings = False

        # top half
        self.wpprev_pnl = WallpaperPreviewPanel(self.frame)
        self.sizer_top_half.Add(self.wpprev_pnl, 0, wx.CENTER|wx.EXPAND, 5)
        
        # bottom half
        
        # profile sizer contents
        self.create_sizer_profiles()

        # settings sizer left contents
        self.create_sizer_settings_left()

        # settings sizer right contents
        self.create_sizer_settings_right()

        # bottom button row contents
        self.create_sizer_bottom_buttonrow()


        # Add sub-sizers to bottom_half
        #    Note: horizontal sizer needs children to have proportion = 1
        #    in order to expand them horizontally instead of vertically.
        self.sizer_setting_sizers.Add(self.sizer_settings_left, 1, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_setting_sizers.Add(self.sizer_settings_right, 1, wx.CENTER|wx.EXPAND|wx.ALL, 5)

        self.sizer_bottom_half.Add(self.sizer_profiles, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_bottom_half.Add(self.sizer_setting_sizers, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_bottom_half.Add(self.sizer_bottom_buttonrow, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)

        # Collect items at main sizer
        self.sizer_main.Add(self.sizer_top_half, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_main.Add(self.sizer_bottom_half, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)

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
        self.button_new.Bind(wx.EVT_BUTTON, self.onCreateNewProfile)
        self.button_save.Bind(wx.EVT_BUTTON, self.onSave)
        self.button_delete.Bind(wx.EVT_BUTTON, self.onDeleteProfile)

        # Add elements to the sizer
        self.sizer_profiles.Add(st_choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(st_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.tc_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_new, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_delete, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_profiles.Add(self.button_save, 0, wx.CENTER|wx.ALL, 5)

    def create_sizer_settings_left(self):
        # span mode sizer
        self.sizer_setting_span_mode = wx.StaticBoxSizer(wx.VERTICAL, self, "Span Mode")
        radio_choices_spanmode = ["Simple span", "Advanced span", "Separate image for every display"]
        self.radiobox_spanmode = wx.RadioBox(self, wx.ID_ANY, 
                                             choices=radio_choices_spanmode,
                                             style=wx.RA_VERTICAL 
                                            )
        self.sizer_setting_span_mode.Add(self.radiobox_spanmode, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # slideshow sizer
        self.sizer_setting_slideshow = wx.StaticBoxSizer(wx.VERTICAL, self, "Wallpaper Slideshow")
        statbox_parent_sshow = self.sizer_setting_slideshow.GetStaticBox()
        self.st_sshow_sort = wx.StaticText(statbox_parent_sshow, -1, "Slideshow order:")
        self.ch_sshow_sort = wx.Choice(statbox_parent_sshow, -1, name="SortChoice",
                                 size=(self.tc_width, -1),
                                 choices=["Shuffle", "Alphabetical"])
        self.st_sshow_delay = wx.StaticText(statbox_parent_sshow, -1, "Delay (minutes):")
        # st_sshow_delay_units = wx.StaticText(self, -1, "minutes")
        self.tc_sshow_delay = wx.TextCtrl(statbox_parent_sshow, -1, size=(self.tc_width, -1)) # TODO right-align numeric data
        self.cb_slideshow = wx.CheckBox(statbox_parent_sshow, -1, "Slideshow")
        # disable ch_sshow_sort and tc_sshow_delay based on the Check state of the CheckBox
        self.st_sshow_sort.Disable()
        self.st_sshow_delay.Disable()
        self.tc_sshow_delay.Disable()
        self.ch_sshow_sort.Disable()
        self.cb_slideshow.Bind(wx.EVT_CHECKBOX, self.onCheckboxSlideshow)
        self.sizer_setting_slideshow.Add(self.cb_slideshow, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_slideshow.Add(self.st_sshow_delay, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_slideshow.Add(self.tc_sshow_delay, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_slideshow.Add(self.st_sshow_sort, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_slideshow.Add(self.ch_sshow_sort, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # hotkey sizer
        self.sizer_setting_hotkey = wx.StaticBoxSizer(wx.VERTICAL, self, "Hotkey")
        statbox_parent_hkey = self.sizer_setting_hotkey.GetStaticBox()
        self.cb_hotkey = wx.CheckBox(statbox_parent_hkey, -1, "Bind a hotkey to this profile")
        st_hotkey_bind = wx.StaticText(statbox_parent_hkey, -1, "Hotkey to bind:")
        st_hotkey_bind.Disable()
        self.tc_hotkey_bind = wx.TextCtrl(statbox_parent_hkey, -1, size=(self.tc_width, -1))
        self.tc_hotkey_bind.Disable()
        self.hotkey_bind_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.hotkey_bind_sizer.Add(st_hotkey_bind, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.hotkey_bind_sizer.Add(self.tc_hotkey_bind, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_setting_hotkey.Add(self.cb_hotkey, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_setting_hotkey.Add(self.hotkey_bind_sizer, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        # TODO disable tc based on checkbox
        self.cb_hotkey.Bind(wx.EVT_CHECKBOX, self.onCheckboxHotkey)


        # Add subsizers to the left column sizer
        self.sizer_settings_left.Add(self.sizer_setting_span_mode, 0, wx.CENTER|wx.EXPAND, 5)
        self.sizer_settings_left.Add(self.sizer_setting_slideshow, 0, wx.CENTER|wx.EXPAND, 5)
        self.sizer_settings_left.Add(self.sizer_setting_hotkey, 0, wx.CENTER|wx.EXPAND, 5)

    def create_sizer_settings_right(self):
        # TODO Some settings in the right column are CONDITIONAL: bezel corr, maybe diag inches?
        # bezel correction TODO don't show if span mode is multi image or simple span.
        if True:
            self.create_sizer_settings_advanced()
        # self.sizer_settings_right.Add(self.sizer_setting_, 0, wx.CENTER|wx.EXPAND)

        # paths sizer contents
        self.create_sizer_paths()

    def create_sizer_paths(self):
        self.sizer_setting_paths = wx.StaticBoxSizer(wx.VERTICAL, self, "Wallpaper Paths")
        statbox_parent_paths = self.sizer_setting_paths.GetStaticBox()
        st_paths_info = wx.StaticText(statbox_parent_paths, -1, "Browse to add your wallpaper files or source folders here:")
        self.path_listctrl = wx.ListCtrl(statbox_parent_paths, -1,
                                         style=wx.LC_REPORT
                                        #  | wx.BORDER_SUNKEN
                                         | wx.BORDER_SIMPLE
                                        #  | wx.BORDER_STATIC
                                        #  | wx.BORDER_THEME
                                        #  | wx.BORDER_NONE
                                        #  | wx.LC_EDIT_LABELS
                                         | wx.LC_SORT_ASCENDING
                                        #  | wx.LC_NO_HEADER
                                        #  | wx.LC_VRULES
                                        #  | wx.LC_HRULES
                                        #  | wx.LC_SINGLE_SEL
                                        )
        test_src = [("0", "path1"), ("0", "image1"), ("1", "image2")]
        self.path_listctrl.InsertColumn(0, 'Display', wx.LIST_FORMAT_RIGHT, width = 100)
        self.path_listctrl.InsertColumn(1, 'Source')
        for i in test_src:
            index = self.path_listctrl.InsertItem(test_src.index(i), i[0])
            self.path_listctrl.SetItem(index, 1, i[1])
        self.sizer_setting_paths.Add(st_paths_info, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_paths.Add(self.path_listctrl, 1, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        # Buttons
        self.sizer_setting_paths_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.button_browse = wx.Button(statbox_parent_paths, label="Browse")
        self.button_remove_source = wx.Button(statbox_parent_paths, label="Remove selected source")
        self.button_browse.Bind(wx.EVT_BUTTON, self.onBrowsePaths)
        self.button_remove_source.Bind(wx.EVT_BUTTON, self.onRemoveSource)
        self.sizer_setting_paths_buttons.Add(self.button_browse, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_setting_paths_buttons.Add(self.button_remove_source, 0, wx.CENTER|wx.ALL, 5)
        # add button sizer to parent paths sizer
        self.sizer_setting_paths.Add(self.sizer_setting_paths_buttons, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)


        # Default span mode is simple span so the initial ListCtrl
        # should have only one column

        self.sizer_settings_right.Add(self.sizer_setting_paths, 1, wx.CENTER|wx.EXPAND|wx.ALL, 5)

    def create_sizer_settings_advanced(self):
        self.sizer_setting_adv = wx.StaticBoxSizer(wx.VERTICAL, self, "Advanced Wallpaper Adjustment")
        statbox_parent_adv = self.sizer_setting_adv.GetStaticBox()

        # Fallback Diagonal Inches
        self.sizer_setting_diaginch = wx.StaticBoxSizer(wx.VERTICAL, self, "Display Diagonal Sizes")
        statbox_parent_diaginch = self.sizer_setting_diaginch.GetStaticBox()
        st_diaginch_override = wx.StaticText(
            statbox_parent_diaginch, -1,
            "Manual display size input:"
        )
        self.button_override = wx.Button(statbox_parent_diaginch, label="Override detected sizes")
        self.button_override.Bind(wx.EVT_BUTTON, self.onOverrideSizes)
        self.sizer_setting_diaginch.Add(st_diaginch_override, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_setting_diaginch.Add(self.button_override, 0, wx.CENTER|wx.ALL, 5)

        # Bezels
        self.sizer_setting_bezels = wx.StaticBoxSizer(wx.VERTICAL, self, "Bezel Correction")
        statbox_parent_bezels = self.sizer_setting_bezels.GetStaticBox()
        self.cb_bezels = wx.CheckBox(statbox_parent_bezels, -1, "Apply bezel correction")
        self.cb_bezels.Bind(wx.EVT_CHECKBOX, self.onCheckboxBezels)
        st_bezels = wx.StaticText(
            statbox_parent_bezels, -1,
            "Bezel pair thicknesses, incl. gap (millimeters):"
        )
        st_bezels.Disable()
        self.sizer_setting_bezels.Add(self.cb_bezels, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_bezels.Add(st_bezels, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        tc_list_sizer_bez = wx.BoxSizer(wx.HORIZONTAL)
        self.tc_list_bezels = self.list_of_textctrl(statbox_parent_bezels, wpproc.NUM_DISPLAYS-1)
        for tc in self.tc_list_bezels:
            tc_list_sizer_bez.Add(tc, 0, wx.ALIGN_LEFT|wx.ALL, 5)
            tc.Disable()
        self.sizer_setting_bezels.Add(tc_list_sizer_bez, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # Offsets
        self.sizer_setting_offsets = wx.StaticBoxSizer(wx.VERTICAL, self, "Manual Display Offsets")
        statbox_parent_offsets = self.sizer_setting_offsets.GetStaticBox()
        self.cb_offsets = wx.CheckBox(statbox_parent_offsets, -1, "Apply manual offsets")
        self.cb_offsets.Bind(wx.EVT_CHECKBOX, self.onCheckboxOffsets)
        st_offsets = wx.StaticText(
            statbox_parent_offsets, -1,
            "Manual wallpaper offsets/panning in pixels (x,y=px,px):"
        )
        st_offsets.Disable()
        self.sizer_setting_offsets.Add(self.cb_offsets, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_offsets.Add(st_offsets, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        tc_list_sizer_offs = wx.BoxSizer(wx.HORIZONTAL)
        self.tc_list_offsets = self.list_of_textctrl(statbox_parent_offsets, wpproc.NUM_DISPLAYS)
        for tc in self.tc_list_offsets:
            tc_list_sizer_offs.Add(tc, 0, wx.ALIGN_LEFT|wx.ALL, 5)
            tc.SetValue("0,0")
            tc.Disable()
        self.sizer_setting_offsets.Add(tc_list_sizer_offs, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # Add setting subsizers to the adv settings sizer
        self.sizer_setting_adv.Add(self.sizer_setting_diaginch, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_setting_adv.Add(self.sizer_setting_bezels, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_setting_adv.Add(self.sizer_setting_offsets, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)

        self.sizer_settings_right.Add(self.sizer_setting_adv, 1, wx.CENTER|wx.EXPAND|wx.ALL, 5)

    def create_sizer_diaginch_override(self):
        self.sizer_setting_diaginch.Clear(True)
        statbox_parent_diaginch = self.sizer_setting_diaginch.GetStaticBox()
        self.cb_diaginch = wx.CheckBox(statbox_parent_diaginch, -1, "Input display sizes manually")
        self.cb_diaginch.Bind(wx.EVT_CHECKBOX, self.onCheckboxDiaginch)
        st_diaginch = wx.StaticText(
            statbox_parent_diaginch, -1,
            "Display diagonal sizes (inches):"
        )
        st_diaginch.Disable()
        self.sizer_setting_diaginch.Add(self.cb_diaginch, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_diaginch.Add(st_diaginch, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        tc_list_sizer_diag = wx.BoxSizer(wx.HORIZONTAL)
        self.tc_list_diaginch = self.list_of_textctrl(statbox_parent_diaginch, wpproc.NUM_DISPLAYS)
        for tc in self.tc_list_diaginch:
            tc_list_sizer_diag.Add(tc, 0, wx.ALIGN_LEFT|wx.ALL, 5)
            tc.Disable()
        self.sizer_setting_diaginch.Add(tc_list_sizer_diag, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_setting_adv.Layout()
        self.sizer_main.Fit(self.frame)

    def create_sizer_bottom_buttonrow(self):
        self.button_help = wx.Button(self, label="Help")
        self.button_align_test = wx.Button(self, label="Align Test")
        self.button_apply = wx.Button(self, label="Apply")
        self.button_close = wx.Button(self, label="Close")

        self.button_apply.Bind(wx.EVT_BUTTON, self.onApply)
        self.button_align_test.Bind(wx.EVT_BUTTON, self.onAlignTest)
        self.button_help.Bind(wx.EVT_BUTTON, self.onHelp)
        self.button_close.Bind(wx.EVT_BUTTON, self.onClose)

        self.sizer_bottom_buttonrow.Add(self.button_help, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_bottom_buttonrow.Add(self.button_align_test, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer_bottom_buttonrow.AddStretchSpacer()
        self.sizer_bottom_buttonrow.Add(self.button_apply, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.sizer_bottom_buttonrow.Add(self.button_close, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

    #
    # Helper methods
    #
    def update_choiceprofile(self):
        """Reload profile list into the choice box."""
        self.list_of_profiles = list_profiles()
        self.profnames = []
        for prof in self.list_of_profiles:
            self.profnames.append(prof.name)
        self.profnames.append("Create a new profile")
        self.choice_profiles.SetItems(self.profnames)

    def list_of_textctrl(self, ctrl_parent, num_disp):
        tcrtl_list = []
        for i in range(num_disp):
            tcrtl_list.append(
                wx.TextCtrl(ctrl_parent, -1, size=(self.tc_width/2, -1))
            )
        return tcrtl_list

    def sizer_toggle_children(self, sizer, bool_state):
        for child in sizer.GetChildren():
            if child.IsSizer():
                self.sizer_toggle_children(child.GetSizer(), bool_state)
            else:
                widget = child.GetWindow()
                if (
                    isinstance(widget, wx.TextCtrl) or
                    isinstance(widget, wx.StaticText) or
                    isinstance(widget, wx.Choice)
                ):
                    widget.Enable(bool_state)

    #
    # Event methods
    #
    def onCheckboxSlideshow(self, event):
        cb_state = self.cb_slideshow.GetValue()
        sizer = self.sizer_setting_slideshow
        self.sizer_toggle_children(sizer, cb_state)

    def onCheckboxHotkey(self, event):
        cb_state = self.cb_hotkey.GetValue()
        sizer = self.hotkey_bind_sizer
        self.sizer_toggle_children(sizer, cb_state)


    def onCheckboxBezels(self, event):
        cb_state = self.cb_bezels.GetValue()
        sizer = self.sizer_setting_bezels
        self.sizer_toggle_children(sizer, cb_state)

    def onCheckboxOffsets(self, event):
        cb_state = self.cb_offsets.GetValue()
        sizer = self.sizer_setting_offsets
        self.sizer_toggle_children(sizer, cb_state)

    def onCheckboxDiaginch(self, event):
        cb_state = self.cb_diaginch.GetValue()
        sizer = self.sizer_setting_diaginch
        self.sizer_toggle_children(sizer, cb_state)


    #
    # Top level button definitions
    #
    def onOverrideSizes(self, event):
        self.create_sizer_diaginch_override()

    def onBrowsePaths(self, event):
        """Opens the pick paths dialog."""
        dlg = BrowsePaths(self, self.show_advanced_settings)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            self.path_list_data = dlg.path_list_data
        dlg.Destroy()

    def onRemoveSource(self, event):
        """Removes selection from wallpaper source ListCtrl."""
        pass

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
        if (inches == "") or (len(inches) < wpproc.NUM_DISPLAYS):
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
        self.preview_size = (1000,666)
        wx.Panel.__init__(self, parent, size=self.preview_size)
        self.frame = parent
        self.SetBackgroundColour(wx.BLACK)
