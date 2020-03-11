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
        bmp = wximg.Scale(target_w, target_h).Resize(self.tsize, pos).ConvertToBitmap()
        return bmp

    #
    # BUTTON methods
    #

    def onAdd(self, event):
        """Adds selected path to export field."""
        path_data_tuples = []
        sel_path = self.dir3.GetPath()
        # self.dir3.GetPaths(paths) # could use this to be more efficient but it does not will the list
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

In the Wallpaper Configuration you can adjust all your wallpaper settings.
Only required options are name and wallpaper source. Other application
wide settings can be changed in the Settings menu. Both are accessible
from the system tray menu.

IMPORTANT NOTE: For the wallpapers to be set correctly, you must set
in your OS the background fitting option to 'Span'.

Description of Wallpaper Configuration 'advanced span' options:
        In advanced mode PPI and bezel corrections are applied
        to the wallpaper.

    - Display positions:
            test1
            test2

    - Bezel correction:
            1
            2

    - Monitor size detection:
            3
            4

Tips:
        - You can use the given example profiles as templates: just change
          the name and whatever else, save, and its a new profile.
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
