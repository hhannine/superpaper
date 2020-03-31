"""
GUI dialogs for Superpaper.
"""
import os

import superpaper.sp_logging as sp_logging
import superpaper.wallpaper_processing as wpproc
from superpaper.data import GeneralSettingsData, ProfileData, TempProfileData, CLIProfileData, list_profiles
from superpaper.message_dialog import show_message_dialog
from superpaper.wallpaper_processing import NUM_DISPLAYS, get_display_data, change_wallpaper_job
from superpaper.sp_paths import PATH, CONFIG_PATH, PROFILES_PATH

try:
    import wx
    import wx.adv
except ImportError:
    exit()



class BrowsePaths(wx.Dialog):
    """Path picker dialog class."""
    def __init__(self, parent, use_multi_image, defdir):
        wx.Dialog.__init__(self, parent, -1, 'Choose image source directories or image files', size=(750, 850))
        BMP_SIZE = 32
        self.tsize = (BMP_SIZE, BMP_SIZE)
        self.il = wx.ImageList(BMP_SIZE, BMP_SIZE)

        self.use_multi_image = use_multi_image
        self.path_list_data = []
        self.paths = []
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_browse = wx.BoxSizer(wx.VERTICAL)
        self.sizer_paths_list = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)

        self.defdir = defdir
        self.dir3 = wx.GenericDirCtrl(
            self, -1,
            #   size=(450, 550),
            #   style=wx.DIRCTRL_SHOW_FILTERS|wx.DIRCTRL_MULTIPLE,
            #   style=wx.DIRCTRL_MULTIPLE,
            dir=self.defdir,
            filter="Image files (*.jpg, *.png)|*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tiff;*.webp"
        )
        sizer_browse.Add(self.dir3, 1, wx.CENTER|wx.ALL|wx.EXPAND, 5)
        st_paths_list = wx.StaticText(
            self, -1,
            "Selected wallpaper source directories and files:"
        )
        self.sizer_paths_list.Add(st_paths_list, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.create_paths_listctrl(self.use_multi_image)

        if self.use_multi_image:
            sizer_radio = wx.BoxSizer(wx.VERTICAL)
            radio_choices_displays = ["Display {}".format(i) for i in range(wpproc.NUM_DISPLAYS)]
            self.radiobox_displays = wx.RadioBox(self, wx.ID_ANY,
                                                 label="Select display to add sources to",
                                                 choices=radio_choices_displays,
                                                 style=wx.RA_HORIZONTAL
                                                )
            sizer_radio.Add(self.radiobox_displays, 0, wx.CENTER|wx.ALL|wx.EXPAND, 5)

        # Buttons
        self.button_add = wx.Button(self, label="Add source")
        self.button_remove = wx.Button(self, label="Remove source")
        self.button_defdir = wx.Button(self, label="Save as browse start")
        self.button_clrdefdir = wx.Button(self, label="Clear browse start")
        self.button_ok = wx.Button(self, label="Ok")
        self.button_cancel = wx.Button(self, label="Cancel")

        self.button_add.Bind(wx.EVT_BUTTON, self.onAdd)
        self.button_remove.Bind(wx.EVT_BUTTON, self.onRemove)
        self.button_defdir.Bind(wx.EVT_BUTTON, self.onDefDir)
        self.button_clrdefdir.Bind(wx.EVT_BUTTON, self.onClrDefDir)
        self.button_ok.Bind(wx.EVT_BUTTON, self.onOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        sizer_buttons.Add(self.button_add, 0, wx.CENTER|wx.ALL, 5)
        sizer_buttons.Add(self.button_remove, 0, wx.CENTER|wx.ALL, 5)
        sizer_buttons.AddStretchSpacer()
        sizer_buttons.Add(self.button_defdir, 0, wx.CENTER|wx.ALL, 5)
        sizer_buttons.Add(self.button_clrdefdir, 0, wx.CENTER|wx.ALL, 5)
        sizer_buttons.AddStretchSpacer()
        sizer_buttons.Add(self.button_ok, 0, wx.CENTER|wx.ALL, 5)
        sizer_buttons.Add(self.button_cancel, 0, wx.CENTER|wx.ALL, 5)

        sizer_main.Add(sizer_browse, 1, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND)
        sizer_main.Add(self.sizer_paths_list, 0, wx.ALL|wx.ALIGN_CENTER)
        if self.use_multi_image:
            sizer_main.Add(sizer_radio, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
        sizer_main.Add(sizer_buttons, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer_main)
        self.SetAutoLayout(True)

    def create_paths_listctrl(self, use_multi_image):
        if use_multi_image:
            self.paths_listctrl = wx.ListCtrl(self, -1,
                                              size=(740, 200),
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
            self.paths_listctrl.InsertColumn(0, 'Display', wx.LIST_FORMAT_RIGHT, width = 100)
            self.paths_listctrl.InsertColumn(1, 'Source', width = 620)
        else:
            # show simpler listing without header if only one wallpaper target
            self.paths_listctrl = wx.ListCtrl(self, -1,
                                              size=(740, 200),
                                              style=wx.LC_REPORT
                                              #  | wx.BORDER_SUNKEN
                                              | wx.BORDER_SIMPLE
                                              #  | wx.BORDER_STATIC
                                              #  | wx.BORDER_THEME
                                              #  | wx.BORDER_NONE
                                              #  | wx.LC_EDIT_LABELS
                                              #  | wx.LC_SORT_ASCENDING
                                              | wx.LC_NO_HEADER
                                              #  | wx.LC_VRULES
                                              #  | wx.LC_HRULES
                                              #  | wx.LC_SINGLE_SEL
                                             )
            self.paths_listctrl.InsertColumn(0, 'Source', width = 720)

        # Add the item list to the control
        self.paths_listctrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.sizer_paths_list.Add(self.paths_listctrl, 0, wx.CENTER|wx.ALL|wx.EXPAND, 5)

    def append_to_listctrl(self, data_row):
        if self.use_multi_image:
            img_id = self.add_to_imagelist(data_row[1])
            index = self.paths_listctrl.InsertItem(self.paths_listctrl.GetItemCount(), data_row[0], img_id)
            self.paths_listctrl.SetItem(index, 1, data_row[1])
        else:
            img_id = self.add_to_imagelist(data_row[0])
            index = self.paths_listctrl.InsertItem(self.paths_listctrl.GetItemCount(), data_row[0], img_id)
            # self.paths_listctrl.SetItem(index, 1, data[1])

    def add_to_imagelist(self, path):
        folder_bmp =  wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_TOOLBAR, self.tsize)
        # file_bmp =  wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_TOOLBAR, self.tsize)
        if os.path.isdir(path):
            img_id = self.il.Add(folder_bmp)
        else:
            thumb_bmp = self.create_thumb_bmp(path)
            img_id = self.il.Add(thumb_bmp)
        return img_id

    def create_thumb_bmp(self, filename):
        wximg = wx.Image(filename, type=wx.BITMAP_TYPE_ANY)
        imgsize = wximg.GetSize()
        w2h_ratio = imgsize[0]/imgsize[1]
        if w2h_ratio > 1:
            target_w = self.tsize[0]
            target_h = target_w/w2h_ratio
            pos = (0, round((target_w - target_h)/2))
        else:
            target_h = self.tsize[1]
            target_w = target_h*w2h_ratio
            pos = (round((target_h - target_w)/2), 0)
        bmp = wximg.Scale(target_w,
                          target_h,
                          quality=wx.IMAGE_QUALITY_BOX_AVERAGE
                         ).Resize(self.tsize,
                                  pos
                                 ).ConvertToBitmap()
        return bmp

    #
    # BUTTON methods
    #

    def onAdd(self, event):
        """Adds selected path to export field."""
        path_data_tuples = []
        sel_path = self.dir3.GetPath()
        # self.dir3.GetPaths(paths) # more efficient but couldn't get to work
        if self.use_multi_image:
            # Extra column in advanced mode
            disp_id = str(self.radiobox_displays.GetSelection())
            self.append_to_listctrl([disp_id, sel_path])
        else:
            self.append_to_listctrl([sel_path])

    def onRemove(self, event):
        """Removes last appended path from export field."""
        # TODO remove btn should be disabled if not in valid selection
        item = self.paths_listctrl.GetFocusedItem()
        if item != -1:
            self.paths_listctrl.DeleteItem(item)

    def onDefDir(self, event):
        sel_path = self.dir3.GetPath()
        if os.path.isdir(sel_path):
            self.defdir = sel_path
            current_settings = GeneralSettingsData()
            current_settings.browse_default_dir = self.defdir.strip()
            current_settings.save_settings()
        else:
            pass

    def onClrDefDir(self, event):
        self.defdir = ""
        current_settings = GeneralSettingsData()
        current_settings.browse_default_dir = ""
        current_settings.save_settings()


    def onOk(self, event):
        """Exports path to parent Profile Config dialog."""
        columns = self.paths_listctrl.GetColumnCount()
        for idx in range(self.paths_listctrl.GetItemCount()):
            item_dat = []
            for col in range(columns):
                item_dat.append(self.paths_listctrl.GetItemText(idx, col))
            self.path_list_data.append(item_dat)
        # print(self.path_list_data)
        # if listctrl is empty, onOk maybe could pass on the selected item? or disable OK if list is empty?
        self.EndModal(wx.ID_OK)


    def onCancel(self, event):
        """Closes path picker, throwing away selections."""
        self.Destroy()





class PerspectiveConfig(wx.Dialog):
    """Perspective data configuration dialog."""
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1,
                           'Configure wallpaper perspective rotations',
                           #    size=(750, 850)
                          )
        self.tc_width = 150
        self.display_sys = parent.display_sys
        self.persp_dict = parent.display_sys.perspective_dict

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        # sizer_common = wx.BoxSizer(wx.VERTICAL)
        # sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)



        # self.sizer_setting_slideshow = wx.StaticBoxSizer(wx.VERTICAL, self, "Wallpaper Slideshow")
        # statbox_parent_sshow = self.sizer_setting_slideshow.GetStaticBox()
        # sizer_sshow_subsettings = wx.GridSizer(2, 5, 5)
        # self.st_sshow_sort = wx.StaticText(statbox_parent_sshow, -1, "Slideshow order:")
        # self.ch_sshow_sort = wx.Choice(statbox_parent_sshow, -1, name="SortChoice",
        #                          size=(self.tc_width*0.7, -1),
        #                          choices=["Shuffle", "Alphabetical"])
        # self.st_sshow_delay = wx.StaticText(statbox_parent_sshow, -1, "Delay (minutes):")
        # self.tc_sshow_delay = wx.TextCtrl(
        #     statbox_parent_sshow, -1,
        #     size=(self.tc_width*0.69, -1),
        #     style=wx.TE_RIGHT
        # )


        # Master options
        self.cb_master = wx.CheckBox(self, -1, "Use perspective corrections")

        # Profile options
        self.create_profile_opts()

        # Display perspective config
        self.create_display_opts(wpproc.NUM_DISPLAYS)

        # Bottom row buttons
        self.create_bottom_butts()

        sizer_main.Add(self.cb_master, 0, wx.ALL|wx.ALIGN_LEFT, 5)
        sizer_main.Add(self.sizer_prof_opts, 1, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
        sizer_main.Add(self.sizer_disp_opts, 1, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
        sizer_main.Add(self.sizer_buttons, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer_main)
        self.Fit()

    def create_profile_opts(self):
        """Create sizer for perspective profile options."""
        self.sizer_prof_opts = wx.StaticBoxSizer(wx.VERTICAL, self, "Perspective profile")
        statbox_profs = self.sizer_prof_opts.GetStaticBox()
        self.profnames = list(self.persp_dict.keys())
        self.profnames.append("Create a new profile")
        self.choice_profiles = wx.Choice(statbox_profs, -1,
                                         name="ProfileChoice", choices=self.profnames)
        self.choice_profiles.Bind(wx.EVT_CHOICE, self.onSelect)
        st_choice_profiles = wx.StaticText(statbox_profs, -1, "Perspective profiles:")
        # name txt ctrl
        st_name = wx.StaticText(statbox_profs, -1, "Profile name:")
        self.tc_name = wx.TextCtrl(statbox_profs, -1, size=(self.tc_width, -1))
        # buttons
        self.button_new = wx.Button(statbox_profs, label="New")
        self.button_save = wx.Button(statbox_profs, label="Save")
        self.button_delete = wx.Button(statbox_profs, label="Delete")
        self.button_new.Bind(wx.EVT_BUTTON, self.onCreateNewProfile)
        self.button_save.Bind(wx.EVT_BUTTON, self.onSave)
        self.button_delete.Bind(wx.EVT_BUTTON, self.onDeleteProfile)

        # Add elements to the sizer
        self.sizer_prof_opts.Add(st_choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_opts.Add(self.choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_opts.Add(st_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_opts.Add(self.tc_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_opts.Add(self.button_new, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_opts.Add(self.button_save, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_opts.Add(self.button_delete, 0, wx.CENTER|wx.ALL, 5)


    def create_display_opts(self, num_disps):
        """Create sizer for display perspective options."""
        self.sizer_disp_opts = wx.StaticBoxSizer(wx.VERTICAL, self,
                                                 "Display perspective configuration")
        cols = 8
        gap = 5
        self.grid = wx.FlexGridSizer(cols, gap, gap)

        # header
        hd_id = wx.StaticText(self, -1, "Display")
        hd_sax = wx.StaticText(self, -1, "Swivel axis")
        hd_san = wx.StaticText(self, -1, "Swivel angle")
        hd_sol = wx.StaticText(self, -1, "Swiv. ax. lat. offs.")
        hd_sod = wx.StaticText(self, -1, "Swiv. ax. dep. offs.")
        hd_tan = wx.StaticText(self, -1, "Tilt angle")
        hd_tov = wx.StaticText(self, -1, "Tilt ax. ver. offs.")
        hd_tod = wx.StaticText(self, -1, "Tilt ax. dep. offs.")
        self.grid.Add(hd_id, 0, wx.ALL, 5)
        self.grid.Add(hd_sax, 0, wx.ALL, 5)
        self.grid.Add(hd_san, 0, wx.ALL, 5)
        self.grid.Add(hd_sol, 0, wx.ALL, 5)
        self.grid.Add(hd_sod, 0, wx.ALL, 5)
        self.grid.Add(hd_tan, 0, wx.ALL, 5)
        self.grid.Add(hd_tov, 0, wx.ALL, 5)
        self.grid.Add(hd_tod, 0, wx.ALL, 5)

        # Fill grid rows
        self.grid_rows = []
        for i in range(num_disps):
            row = self.display_opt_widget_row(i)
            self.grid_rows.append(row)
            sizer_row = [(item, 0, wx.ALL|wx.ALIGN_RIGHT, 5) for item in row]
            self.grid.AddMany(sizer_row)

        # Build sizer
        self.sizer_disp_opts.Add(self.grid, 0, wx.ALL|wx.EXPAND, 5)

    def display_opt_widget_row(self, row_id):
        """Return a display option widget row."""
        row_id = wx.StaticText(self, -1, str(row_id))
        row_sax = wx.Choice(self, -1, name="SwivelAxisChoice",
                            size=(self.tc_width*0.7, -1),
                            choices=["No swivel", "Left", "Right"])
        row_san = wx.TextCtrl(self, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_sol = wx.TextCtrl(self, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_sod = wx.TextCtrl(self, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_tan = wx.TextCtrl(self, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_tov = wx.TextCtrl(self, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_tod = wx.TextCtrl(self, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        # Prefill neutral data
        row_sax.SetSelection(0)
        row_san.SetValue("0")
        row_sol.SetValue("0")
        row_sod.SetValue("0")
        row_tan.SetValue("0")
        row_tov.SetValue("0")
        row_tod.SetValue("0")

        row = [row_id, row_sax, row_san, row_sol, row_sod, row_tan, row_tov, row_tod]
        return row


    def create_bottom_butts(self):
        """Create sizer for bottom row buttons."""
        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)

        self.button_add = wx.Button(self, label="Add source")
        self.button_remove = wx.Button(self, label="Remove source")
        self.button_ok = wx.Button(self, label="Ok")
        self.button_cancel = wx.Button(self, label="Cancel")

        # self.button_add.Bind(wx.EVT_BUTTON, self.onAdd)
        # self.button_remove.Bind(wx.EVT_BUTTON, self.onRemove)
        # self.button_ok.Bind(wx.EVT_BUTTON, self.onOk)
        # self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self.sizer_buttons.Add(self.button_add, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_remove, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.AddStretchSpacer()
        self.sizer_buttons.Add(self.button_ok, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_cancel, 0, wx.CENTER|wx.ALL, 5)


    #
    # Button methods
    #
    def onSelect(self, evt):
        pass

    def onSave(self, evt):
        pass

    def onDeleteProfile(self, evt):
        pass

    def onCreateNewProfile(self, evt):
        pass




class SettingsFrame(wx.Frame):
    """Settings dialog frame."""
    def __init__(self, parent_tray_obj):
        wx.Frame.__init__(self, parent=None, title="Superpaper General Settings")
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_panel = SettingsPanel(self, parent_tray_obj)
        self.frame_sizer.Add(settings_panel, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(self.frame_sizer)
        self.Fit()
        self.Layout()
        self.Center()
        self.Show()

class SettingsPanel(wx.Panel):
    """Settings dialog contents."""
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
        """Updates dialog field contents."""
        g_settings = GeneralSettingsData()
        self.cb_logging.SetValue(g_settings.logging)
        self.cb_usehotkeys.SetValue(g_settings.use_hotkeys)
        self.tc_hk_next.ChangeValue(self.show_hkbinding(g_settings.hk_binding_next))
        self.tc_hk_pause.ChangeValue(self.show_hkbinding(g_settings.hk_binding_pause))
        self.tc_setcmd.ChangeValue(g_settings.set_command)

    def show_hkbinding(self, hktuple):
        """Formats hotkey tuple as a readable string."""
        hkstring = "+".join(hktuple)
        return hkstring

    def onSave(self, event):
        """Saves settings to file."""
        current_settings = GeneralSettingsData()

        current_settings.logging = self.cb_logging.GetValue()
        current_settings.use_hotkeys = self.cb_usehotkeys.GetValue()
        if self.tc_hk_next.GetLineText(0):
            current_settings.hk_binding_next = tuple(
                self.tc_hk_next.GetLineText(0).strip().split("+")
            )
        else:
            current_settings.hk_binding_next = None
        if self.tc_hk_pause.GetLineText(0):
            current_settings.hk_binding_pause = tuple(
                self.tc_hk_pause.GetLineText(0).strip().split("+")
            )
        else:
            current_settings.hk_binding_pause = None

        current_settings.set_command = self.tc_setcmd.GetLineText(0).strip()

        current_settings.save_settings()
        # after saving file apply in tray object
        self.parent_tray_obj.read_general_settings()

    def onClose(self, event):
        """Closes settings panel."""
        self.frame.Close(True)






class HelpFrame(wx.Frame):
    """Help dialog frame."""
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="Superpaper Help")
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        help_panel = HelpPanel(self)
        self.frame_sizer.Add(help_panel, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(self.frame_sizer)
        self.Fit()
        self.Layout()
        self.Center()
        self.Show()

class HelpPanel(wx.Panel):
    """Help dialog contents."""
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

In the Wallpaper Configuration you can adjust all your wallpaper settings.  Other  application  wide
settings  can be  changed in the  Settings menu.  Both  are  accessible from the  system tray menu.

IMPORTANT NOTE: For the wallpapers to be set correctly, you must set in your OS the background
fitting option to 'Span'.

Description of Wallpaper Configuration 'advanced span' options:
    In advanced mode PPI and bezel corrections are applied to the wallpaper. The following settings
    are used to configure this:

    - Physical display positions:
            In 'advanced span' mode Superpaper corrects for different pixel densities between displays
            and this means that to get a corretly  spanned image across  the monitor array,  the  relative
            physical locations of the displays needs to be known.  A  configuration  is guessed but if your
            monitors  are  arranged  in  another  way,  you  can  adjust  the  positions  of  the  displays  by
            entering the 'Positions' tool and dragging the display previews.

    - Bezel correction:
            Display bezel thicknesses and gaps can be taken into account when computing the wallpaper
            span.  Enter bezel sizes by selecting  'Configure bezels'  in  Advanced  Wallpaper  Adjustment
            subsection. Adjacent bezels and gap are added together.

    - Display size detection:
            To apply PPI correction Superpaper needs to know the physical sizes of your displays.  These
            are  attempted to be detected  automatically.  If this fails,  you can enter  the  correct  values
            under 'Display Diagonal Sizes'.

Tips:
    - You can use the given example profiles as templates: just change the name and whatever else,
      save, and its a new profile.
    - 'Align Test' feature allows you to test your offset and bezel settings.
"""
        st_help = wx.StaticText(self, -1, help_str)
        self.sizer_helpcontent.Add(st_help, 0, wx.EXPAND|wx.CENTER|wx.ALL, 5)

        self.sizer_main.Add(self.sizer_helpcontent, 0, wx.CENTER|wx.EXPAND)
        self.sizer_main.Add(self.sizer_buttons, 0, wx.CENTER|wx.EXPAND)
        self.SetSizer(self.sizer_main)
        self.sizer_main.Fit(parent)

    def onClose(self, event):
        """Closes help dialog. Saves checkbox state as needed."""
        if self.cb_show_at_start.GetValue() is True:
            current_settings = GeneralSettingsData()
            if current_settings.show_help is False:
                current_settings.show_help = True
                current_settings.save_settings()
        else:
            # Save that the help at start is not wanted.
            current_settings = GeneralSettingsData()
            show_help = current_settings.show_help
            if show_help:
                current_settings.show_help = False
                current_settings.save_settings()
        self.frame.Close(True)




class HelpPopup(wx.PopupTransientWindow):
    """Popup to show a bit of static text"""
    def __init__(self, parent, text,
                 show_image_quality = False,
                 advanced_span = False,
                 style = wx.BORDER_DEFAULT):
        wx.PopupTransientWindow.__init__(self, parent, style)
        self.preview = parent
        if show_image_quality:
            self.advanced_on = self.preview.frame.show_advanced_settings
            self.show_image_quality = not self.preview.frame.use_multi_image
        else:
            self.advanced_on = False
            self.show_image_quality = False
        pnl = wx.Panel(self)
        # pnl.SetBackgroundColour("CADET BLUE")

        st = wx.StaticText(pnl, -1, text)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(st, 0, wx.ALL, 5)
        if self.show_image_quality:
            st_qual = wx.StaticText(pnl, -1, self.string_ideal_image_size())
            sizer.Add(st_qual, 0, wx.ALL, 5)
        pnl.SetSizer(sizer)
        sizer.Fit(pnl)
        sizer.Fit(self)
        self.Layout()

    def ProcessLeftDown(self, evt):
        return wx.PopupTransientWindow.ProcessLeftDown(self, evt)

    def OnDismiss(self):
        self.Destroy()

    def string_ideal_image_size(self):
        "Return a sentence what the minimum source image size is for best quality."
        senten = ("For the best image quality with current settings your\n"
                  r" wallpapers should be {} or larger.")
        if self.advanced_on:
            if self.preview.frame.cb_offsets.GetValue():
                offsets = []
                for tc in self.preview.frame.tc_list_offsets:
                    off_str = tc.GetValue().split(",")
                    try:
                        offsets.append(
                            (int(off_str[0]), int(off_str[1]))
                        )
                    except (ValueError, IndexError):
                        offsets.append(
                            (0, 0)
                        )
            else:
                offsets = wpproc.NUM_DISPLAYS * [(0, 0)]
            crops = self.preview.display_sys.get_ppi_norm_crops(offsets)
            canv = wpproc.compute_working_canvas(crops)
        else:
            canv = wpproc.compute_canvas(
                wpproc.RESOLUTION_ARRAY,
                wpproc.DISPLAY_OFFSET_ARRAY
            )
        res_str = "{}x{}".format(canv[0], canv[1])
        fin = senten.format(res_str)
        return fin
