"""
GUI dialogs for Superpaper.
"""
import os
import time

import superpaper.perspective as persp
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

RESOURCES_PATH = os.path.join(PATH, "superpaper/resources")
TRAY_ICON = os.path.join(RESOURCES_PATH, "superpaper.png")

class BrowsePaths(wx.Dialog):
    """Path picker dialog class."""
    def __init__(self, parent, use_multi_image, defdir, num_span_groups=None):
        wx.Dialog.__init__(self, parent, -1,
                           'Choose image source directories or image files',
                           size=(250, 250),
                           style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
        # self.SetMinSize((250, 250))
        BMP_SIZE = 32
        self.tsize = (BMP_SIZE, BMP_SIZE)
        self.il = wx.ImageList(BMP_SIZE, BMP_SIZE)

        if num_span_groups:
            self.num_wallpaper_area = num_span_groups
            self.wp_area_name = "Group"
        else:
            self.num_wallpaper_area = wpproc.NUM_DISPLAYS
            self.wp_area_name = "Display"
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
        self.cb_showhidden = wx.CheckBox(self, -1, "Show hidden files")
        self.cb_showhidden.Bind(wx.EVT_CHECKBOX, self.onCheckboxShowHidden)
        sizer_browse.Add(self.cb_showhidden, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        st_paths_list = wx.StaticText(
            self, -1,
            "Selected wallpaper source directories and files:"
        )
        self.sizer_paths_list.Add(st_paths_list, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.create_paths_listctrl(self.use_multi_image)

        if self.use_multi_image:
            sizer_radio = wx.BoxSizer(wx.VERTICAL)
            radio_choices_displays = [
                self.wp_area_name + " {}".format(i) for i in range(self.num_wallpaper_area)
            ]
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

        sizer_main.Add(sizer_browse, 1, wx.ALL|wx.EXPAND)
        sizer_main.Add(self.sizer_paths_list, 0, wx.ALL|wx.EXPAND)
        if self.use_multi_image:
            sizer_main.Add(sizer_radio, 0, wx.ALL|wx.EXPAND, 5)
        sizer_main.Add(sizer_buttons, 0, wx.ALL|wx.EXPAND, 5)
        # self.SetSizer(sizer_main)
        self.SetSizerAndFit(sizer_main)
        self.SetSize((-1, 650))
        # self.SetAutoLayout(True)

    def create_paths_listctrl(self, use_multi_image):
        if use_multi_image:
            self.paths_listctrl = wx.ListCtrl(self, -1,
                                              size=(-1, -1),
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
            self.paths_listctrl.InsertColumn(0, self.wp_area_name, wx.LIST_FORMAT_RIGHT, width=100)
            self.paths_listctrl.InsertColumn(1, 'Source', width=620)
        else:
            # show simpler listing without header if only one wallpaper target
            self.paths_listctrl = wx.ListCtrl(self, -1,
                                              size=(-1, -1),
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
            self.paths_listctrl.InsertColumn(0, 'Source', width=720)

        # Add the item list to the control
        self.paths_listctrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.sizer_paths_list.Add(self.paths_listctrl, 1, wx.CENTER|wx.ALL|wx.EXPAND, 5)

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
        bmp = wximg.Scale(round(target_w),
                          round(target_h),
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

    def onCheckboxShowHidden(self, event):
        self.dir3.ShowHidden(self.cb_showhidden.GetValue())


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




class DisplayPositionEntry(wx.Frame):
    """Display position fine control dialog."""
    def __init__(self, parent, dragged_positions=False):
        wx.Frame.__init__(self, parent.frame, -1,
                          'Enter display positions'
                          )
        self.ToggleWindowStyle(wx.STAY_ON_TOP)
        self.SetIcon(wx.Icon(TRAY_ICON, wx.BITMAP_TYPE_PNG))
        self.Bind(wx.EVT_CLOSE, self.OnClose)


        self.tc_width = 100
        self.parent = parent
        self.frame = parent # help dialog looks for this name
        self.parent.button_save.Disable()
        self.parent.button_cancel.Disable()
        self.display_sys = parent.display_sys
        if dragged_positions:
            self.parent.export_offsets(self.display_sys)  # export dragged offsets first
        self.old_ppinorm_offs = self.display_sys.get_ppinorm_offsets()  # back up the offsets

        self.help_bmp = wx.ArtProvider.GetBitmap(wx.ART_QUESTION, wx.ART_BUTTON, (20, 20))

        sizer_main = wx.BoxSizer(wx.VERTICAL)

        # Display position config
        self.create_position_config(wpproc.NUM_DISPLAYS)

        # Bottom row buttons
        self.create_bottom_butts()

        self.set_unit_labels(self.cb_use_px.GetValue())

        sizer_main.Add(self.sizer_pos_conf, 0, wx.ALL|wx.EXPAND, 5)
        sizer_main.Add(self.sizer_buttons, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer_main)
        self.Fit()
        self.populate_fields()
        self.Center()
        self.Show()

    def create_position_config(self, num_disps):
        """Create display position entry and data grid sizer."""
        cols = 7
        gap = 5
        self.sizer_pos_conf = wx.BoxSizer(wx.VERTICAL)
        self.grid = wx.FlexGridSizer(cols, gap, gap)

        # header
        hd_id = wx.StaticText(self, -1, "Display")
        self.hd_left = wx.StaticText(self, -1, "Left")
        self.hd_top = wx.StaticText(self, -1, "Top")
        self.hd_right = wx.StaticText(self, -1, "Right")
        self.hd_bott = wx.StaticText(self, -1, "Bottom")
        self.hd_left_new = wx.StaticText(self, -1, "Left new")
        self.hd_top_new = wx.StaticText(self, -1, "Top new")
        self.grid.Add(hd_id, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(self.hd_left, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(self.hd_top, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(self.hd_right, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(self.hd_bott, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(self.hd_left_new, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(self.hd_top_new, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)

        # Fill grid rows
        self.grid_rows = []
        for i in range(num_disps):
            row = self.display_opt_widget_row(i)
            self.grid_rows.append(row)
            sizer_row = [(item, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 1)
                         for item in row]
            self.grid.AddMany(sizer_row)
        self.sizer_pos_conf.Add(self.grid, 0, wx.EXPAND|wx.ALL, 0)

    def display_opt_widget_row(self, row_id):
        """Return a display position config widget row."""
        # statbox_disp_opts = self.sizer_disp_opts.GetStaticBox()
        statbox_disp_opts = self
        row_id = wx.StaticText(statbox_disp_opts, -1, str(row_id))
        row_left = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width, -1),
                               style=wx.TE_RIGHT|wx.TE_READONLY)
        row_top = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width, -1),
                              style=wx.TE_RIGHT|wx.TE_READONLY)
        row_right = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width, -1),
                                style=wx.TE_RIGHT|wx.TE_READONLY)
        row_bottom = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width, -1),
                                 style=wx.TE_RIGHT|wx.TE_READONLY)
        row_left_new = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width, -1),
                                   style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        row_top_new = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width, -1),
                                  style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)

        row_left.Disable()
        row_top.Disable()
        row_right.Disable()
        row_bottom.Disable()

        row_left_new.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)
        row_top_new.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)


        row = [row_id, row_left, row_top, row_right, row_bottom, row_left_new, row_top_new]
        return row

    def set_unit_labels(self, use_px):
        """Show units in column labels."""
        if use_px:
            unit_str = "[px]"
        else:
            unit_str = "[mm]"
        self.hd_left.SetLabel("Left " + unit_str)
        self.hd_top.SetLabel("Top " + unit_str)
        self.hd_right.SetLabel("Right " + unit_str)
        self.hd_bott.SetLabel("Bottom " + unit_str)
        self.hd_left_new.SetLabel("Left new " + unit_str)
        self.hd_top_new.SetLabel("Top new " + unit_str)

    def create_bottom_butts(self):
        """Create sizer for bottom row buttons."""
        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)

        self.cb_use_px = wx.CheckBox(self, -1, "Use pixels (exact)")
        self.cb_use_px.SetValue(False)
        self.cb_use_px.Bind(wx.EVT_CHECKBOX, self.onCbusepx)

        self.button_preview = wx.Button(self, label="Preview")
        self.button_apply = wx.Button(self, label="Apply")
        self.button_cancel = wx.Button(self, label="Cancel")

        self.button_preview.Bind(wx.EVT_BUTTON, self.onPreview)
        self.button_apply.Bind(wx.EVT_BUTTON, self.onApply)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self.button_help_pos = wx.BitmapButton(self, bitmap=self.help_bmp)
        self.button_help_pos.Bind(wx.EVT_BUTTON, self.onHelpExactPositions)

        self.sizer_buttons.Add(self.cb_use_px, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        self.sizer_buttons.AddStretchSpacer()
        self.sizer_buttons.Add(self.button_help_pos, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_preview, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_apply, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_cancel, 0, wx.CENTER|wx.ALL, 5)

    def OnEnter(self, evt):
        """Bind pressing Enter in the txtctrl to update preview."""
        self.onPreview(evt)

    def OnClose(self, evt):
        """Make closing out behave as cancellation."""
        self.onCancel(evt)

    def onCbusepx(self, event):
        """Updates units of shown position data."""
        use_px = self.cb_use_px.GetValue()
        self.convert_units(use_px)
        self.set_unit_labels(use_px)

    def update_offsets_and_redraw(self):
        """Collect display postitions and redraw preview."""
        max_ppi = self.display_sys.max_ppi()
        if self.cb_use_px.GetValue():
            unit_mult = 1
        else:
            unit_mult = max_ppi/25.4 # convert ppi to px/mm
        offs = []
        for row in self.grid_rows:
            new_off = []
            for tc in row[-2:]:
                tc_val = tc.GetValue()
                try:
                    new_off.append(float(tc_val)*unit_mult)
                except ValueError:
                    if tc_val:
                        msg = "Entered value '{}' is not valid.".format(tc_val)
                    else:
                        msg = "Please enter a position for every display. Some value is empty."
                    show_message_dialog(msg)
                    return False
            offs.append(tuple(new_off))
        offs = self.sanitize_offs(offs)

        self.display_sys.update_ppinorm_offsets(offs)
        self.parent.display_data = self.display_sys.get_disp_list(True)
        self.parent.refresh_preview(use_ppi_px=True, force_refresh=True)
        self.parent.create_shapes()
        self.parent.frame.Refresh()

        self.populate_fields()
        return True

    def onPreview(self, event):
        """Updates the display preview based on the entered position values."""
        self.update_offsets_and_redraw()

    def onApply(self, event):
        """Apply display positions and close dialog."""
        res = self.update_offsets_and_redraw()
        if res:
            self.parent.button_save.Enable()
            self.parent.button_cancel.Enable()
            self.parent.positions_dragged = False
            self.Destroy()

    def onCancel(self, event):
        """Closes display position config, throwing away unsaved contents."""
        # Restore old offsets
        self.display_sys.update_ppinorm_offsets(self.old_ppinorm_offs)
        # redraw preview with restored data
        self.parent.display_data = self.display_sys.get_disp_list(True)
        self.parent.refresh_preview(use_ppi_px=True, force_refresh=True)
        self.parent.create_shapes()
        self.parent.frame.Refresh()
        # close dialog
        self.parent.button_save.Enable()
        self.parent.button_cancel.Enable()
        self.Destroy()

    def onHelpExactPositions(self, evt):
        """Popup exact position entry main help."""
        text = ("In this dialog you may adjust the positions of your displays\n"
                "more accurately by either entering measurements or just\n"
                "fine tune the dragged positions by trial and error. You can\n"
                "either enter the positions in millimeters or in the pixels\n"
                "of the used image. Position update might be inaccurate if you\n"
                "need to move a display substantially outside the shown area.\n"
                "In this case save the current position and then proceed to\n"
                "correct the position further.\n"
                "\n"
                "Current positions of the edges of each display Left, Top,\n"
                "Right, Bottom are given as measured from the top left\n"
                "corner of the display area such that the left-most and\n"
                "top-most edge are at 0. Right, Bottom edge positions\n"
                "include bezel sizes."
                )
        pop = HelpPopup(self, text,
                        show_image_quality=False,
                        )
        btn = evt.GetEventObject()
        pos = btn.ClientToScreen((0, 0))
        sz = btn.GetSize()
        pop.Position(pos, (0, sz[1]))
        pop.Popup()


    def populate_fields(self):
        """Populate config fields from DisplaySystem offsets."""
        max_ppi = self.display_sys.max_ppi()
        if self.cb_use_px.GetValue():
            unit_mult = 1
        else:
            unit_mult = 1 / (max_ppi/25.4) # convert ppi to px/mm
        crops = self.display_sys.get_ppi_norm_crops(wpproc.NUM_DISPLAYS*[(0, 0)])
        bezels = self.display_sys.bezels_in_px()
        for row, ltrb, bez in zip(self.grid_rows, crops, bezels):
            row[0].SetLabel(str(self.grid_rows.index(row)))
            row[1].SetValue(str(ltrb[0]*unit_mult))
            row[2].SetValue(str(ltrb[1]*unit_mult))
            row[3].SetValue(str((ltrb[2] + bez[0])*unit_mult))
            row[4].SetValue(str((ltrb[3] + bez[1])*unit_mult))
            row[5].SetValue(str(ltrb[0]*unit_mult))
            row[6].SetValue(str(ltrb[1]*unit_mult))

    def convert_units(self, use_px):
        """Convert table data between px and mm in place."""
        max_ppi = self.display_sys.max_ppi()
        if use_px:
            # convert from mm to px
            unit_mult = max_ppi / 25.4
        else:
            # convert from px to mm
            unit_mult = 1 / (max_ppi/25.4)
        for row in self.grid_rows:
            for tc in row[1:]:
                curval = tc.GetValue()
                if curval:
                    tc.SetValue(str(unit_mult * float(curval)))

    def sanitize_offs(self, offsets):
        """Return offsets translated to be non-negative, anchoring to (0,0)."""
        sanitized_offs = []
        leftmost_offset = min([off[0] for off in offsets])
        topmost_offset = min([off[1] for off in offsets])
        for off in offsets:
            sanitized_offs.append(
                (
                    off[0] - leftmost_offset,
                    off[1] - topmost_offset
                )
            )
        return sanitized_offs


class PerspectiveConfig(wx.Dialog):
    """Perspective data configuration dialog."""
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1,
                           'Configure wallpaper perspective rotations',
                           #    size=(750, 850)
                          )
        self.tc_width = 150
        self.frame = parent
        self.display_sys = parent.display_sys
        self.persp_dict = self.display_sys.perspective_dict
        self.test_image = None
        self.help_bmp = wx.ArtProvider.GetBitmap(wx.ART_QUESTION, wx.ART_BUTTON, (20, 20))
        self.warn_large_img = GeneralSettingsData().warn_large_img

        sizer_main = wx.BoxSizer(wx.VERTICAL)

        # Master options
        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        self.cb_master = wx.CheckBox(self, -1, "Use perspective corrections")
        self.cb_master.SetValue(self.display_sys.use_perspective)
        # self.cb_master.Bind(wx.EVT_CHECKBOX, self.onCbmaster)
        self.button_help_persp = wx.BitmapButton(self, bitmap=self.help_bmp)
        self.button_help_persp.Bind(wx.EVT_BUTTON, self.onHelpPerspective)
        sizer_top.Add(self.cb_master, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_top.AddStretchSpacer()
        sizer_top.Add(self.button_help_persp, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 10)

        # Profile options
        self.create_profile_opts()

        # Display perspective config
        self.create_display_opts(wpproc.NUM_DISPLAYS)

        # Bottom row buttons
        self.create_bottom_butts()

        # sizer_main.Add(self.cb_master, 0, wx.ALL|wx.ALIGN_LEFT, 5)
        sizer_main.Add(sizer_top, 0, wx.ALL|wx.EXPAND, 0)
        sizer_main.Add(self.sizer_prof_opts, 0, wx.ALL|wx.EXPAND, 5)
        sizer_main.Add(self.sizer_disp_opts, 0, wx.ALL|wx.EXPAND, 5)
        sizer_main.Add(self.sizer_buttons, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer_main)
        self.Fit()
        if self.display_sys.default_perspective:
            self.populate_fields(self.display_sys.default_perspective)
            self.choice_profiles.SetSelection(
                self.choice_profiles.FindString(self.display_sys.default_perspective)
            )

    def create_profile_opts(self):
        """Create sizer for perspective profile options."""
        self.sizer_prof_opts = wx.StaticBoxSizer(wx.VERTICAL, self, "Perspective profile")
        statbox_profs = self.sizer_prof_opts.GetStaticBox()

        self.sizer_prof_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.profnames = list(self.persp_dict.keys())
        self.profnames.append("Create a new profile")
        self.choice_profiles = wx.Choice(statbox_profs, -1,
                                         name="ProfileChoice", choices=self.profnames)
        self.choice_profiles.Bind(wx.EVT_CHOICE, self.onSelect)
        st_choice_profiles = wx.StaticText(statbox_profs, -1, "Perspective profiles:")
        # name txt ctrl
        st_name = wx.StaticText(statbox_profs, -1, "Profile name:")
        self.tc_name = wx.TextCtrl(statbox_profs, -1, size=(self.tc_width, -1))
        self.tc_name.SetMaxLength(14)
        # buttons
        self.button_new = wx.Button(statbox_profs, label="New")
        self.button_save = wx.Button(statbox_profs, label="Save")
        self.button_delete = wx.Button(statbox_profs, label="Delete")
        self.button_help_perspprof = wx.BitmapButton(statbox_profs, bitmap=self.help_bmp)
        self.button_new.Bind(wx.EVT_BUTTON, self.onCreateNewProfile)
        self.button_save.Bind(wx.EVT_BUTTON, self.onSave)
        self.button_delete.Bind(wx.EVT_BUTTON, self.onDeleteProfile)
        self.button_help_perspprof.Bind(wx.EVT_BUTTON, self.onHelpPersProfile)

        # Add profile bar items to the sizer
        self.sizer_prof_bar.Add(st_choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_bar.Add(self.choice_profiles, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_bar.Add(st_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_bar.Add(self.tc_name, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_bar.Add(self.button_new, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_bar.Add(self.button_save, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_bar.Add(self.button_delete, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_prof_bar.AddStretchSpacer()
        self.sizer_prof_bar.Add(self.button_help_perspprof, 0, wx.CENTER|wx.LEFT, 5)

        self.sizer_prof_opts.Add(self.sizer_prof_bar, 0,
                                 wx.EXPAND|wx.ALL, 5)
        sline = wx.StaticLine(statbox_profs, -1, style=wx.LI_HORIZONTAL)
        self.sizer_prof_opts.Add(sline, 0, wx.EXPAND|wx.ALL, 5)

        # Profile related options
        self.cb_dispsys_def = wx.CheckBox(statbox_profs, -1, "Default for this display setup")
        sizer_centr_disp = wx.BoxSizer(wx.HORIZONTAL)
        st_centr_disp = wx.StaticText(statbox_profs, -1, "Central display:")
        disp_ids = [str(idx) for idx in range(wpproc.NUM_DISPLAYS)]
        self.choice_centr_disp = wx.Choice(statbox_profs, -1,
                                           name="CentDispChoice", choices=disp_ids)
        self.choice_centr_disp.SetSelection(0)
        sizer_centr_disp.Add(st_centr_disp, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_centr_disp.Add(self.choice_centr_disp, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

        sizer_viewer_off = wx.BoxSizer(wx.HORIZONTAL)
        st_vwroffs = wx.StaticText(statbox_profs, -1,
                                   "Viewer offset from central display center [mm]:")
        self.stlist_vieweroffs = [
            wx.StaticText(statbox_profs, -1, "hor:"),
            wx.StaticText(statbox_profs, -1, "ver:"),
            wx.StaticText(statbox_profs, -1, "dist:"),
        ]
        self.tclist_vieweroffs = [
            wx.TextCtrl(statbox_profs, -1, size=(self.tc_width*0.69, -1), style=wx.TE_RIGHT),
            wx.TextCtrl(statbox_profs, -1, size=(self.tc_width*0.69, -1), style=wx.TE_RIGHT),
            wx.TextCtrl(statbox_profs, -1, size=(self.tc_width*0.69, -1), style=wx.TE_RIGHT)
        ]
        for tc in self.tclist_vieweroffs:
            if isinstance(tc, wx.TextCtrl):
                tc.SetValue("0")
        szr_stlist = [(item, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
                      for item in self.stlist_vieweroffs]
        szr_tclist = [(item, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
                      for item in self.tclist_vieweroffs]
        sizer_viewer_off.Add(st_vwroffs, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        for st, tc in zip(szr_stlist, szr_tclist):
            sizer_viewer_off.Add(st[0], st[1], st[2], st[3])
            sizer_viewer_off.Add(tc[0], tc[1], tc[2], tc[3])

        self.button_help_centrald = wx.BitmapButton(statbox_profs, bitmap=self.help_bmp)
        self.button_help_centrald.Bind(wx.EVT_BUTTON, self.onHelpCentralDisp)
        sizer_viewer_off.AddStretchSpacer()
        sizer_viewer_off.Add(self.button_help_centrald, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Add remaining options to persp profile sizer
        self.sizer_prof_opts.Add(self.cb_dispsys_def, 0, wx.ALL, 5)
        self.sizer_prof_opts.Add(sizer_centr_disp, 0, wx.LEFT, 5)
        self.sizer_prof_opts.Add(sizer_viewer_off, 0, wx.LEFT|wx.EXPAND, 5)

    def create_display_opts(self, num_disps):
        """Create sizer for display perspective options."""
        self.sizer_disp_opts = wx.StaticBoxSizer(wx.HORIZONTAL, self,
                                                 "Display perspective configuration")
        statbox_disp_opts = self.sizer_disp_opts.GetStaticBox()
        cols = 8
        gap = 5
        self.grid = wx.FlexGridSizer(cols, gap, gap)

        # header
        hd_id = wx.StaticText(statbox_disp_opts, -1, "Display")
        hd_sax = wx.StaticText(statbox_disp_opts, -1, "Swivel axis")
        hd_san = wx.StaticText(statbox_disp_opts, -1, "Swivel angle")
        hd_sol = wx.StaticText(statbox_disp_opts, -1, "Sw. ax. lat. off.")
        hd_sod = wx.StaticText(statbox_disp_opts, -1, "Sw. ax. dep. off.")
        hd_tan = wx.StaticText(statbox_disp_opts, -1, "Tilt angle")
        hd_tov = wx.StaticText(statbox_disp_opts, -1, "Ti. ax. ver. off.")
        hd_tod = wx.StaticText(statbox_disp_opts, -1, "Ti. ax. dep. off.")
        self.grid.Add(hd_id, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(hd_sax, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(hd_san, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(hd_sol, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(hd_sod, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(hd_tan, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(hd_tov, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.grid.Add(hd_tod, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)

        # Fill grid rows
        self.grid_rows = []
        for i in range(num_disps):
            row = self.display_opt_widget_row(i)
            self.grid_rows.append(row)
            sizer_row = [(item, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 1)
                         for item in row]
            self.grid.AddMany(sizer_row)

        # Build sizer
        self.sizer_disp_opts.Add(self.grid, 0, wx.ALL|wx.EXPAND, 5)

        # help
        self.button_help_data = wx.BitmapButton(statbox_disp_opts, bitmap=self.help_bmp)
        self.button_help_data.Bind(wx.EVT_BUTTON, self.onHelpData)
        self.sizer_disp_opts.AddStretchSpacer()
        self.sizer_disp_opts.Add(self.button_help_data, 0,
                                 wx.ALIGN_TOP|wx.RIGHT, 5)


    def display_opt_widget_row(self, row_id):
        """Return a display option widget row."""
        statbox_disp_opts = self.sizer_disp_opts.GetStaticBox()
        row_id = wx.StaticText(statbox_disp_opts, -1, str(row_id))
        row_sax = wx.Choice(statbox_disp_opts, -1, name="SwivelAxisChoice",
                            size=(self.tc_width*0.7, -1),
                            choices=["No swivel", "Left", "Right"])
        row_san = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_sol = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_sod = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_tan = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_tov = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width*0.69, -1),
                              style=wx.TE_RIGHT)
        row_tod = wx.TextCtrl(statbox_disp_opts, -1, size=(self.tc_width*0.69, -1),
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

        self.button_align_test = wx.Button(self, label="Align test")
        self.button_test_pick = wx.Button(self, label="Pick image")
        self.button_test_imag = wx.Button(self, label="Test image")
        self.button_ok = wx.Button(self, label="OK")
        self.button_cancel = wx.Button(self, label="Close")

        self.button_align_test.Bind(wx.EVT_BUTTON, self.onAlignTest)
        self.button_test_pick.Bind(wx.EVT_BUTTON, self.onChooseTestImage)
        self.button_test_imag.Bind(wx.EVT_BUTTON, self.onTestWallpaper)
        self.button_ok.Bind(wx.EVT_BUTTON, self.onOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self.sizer_buttons.Add(self.button_align_test, 0, wx.CENTER|wx.ALL, 5)
        sline = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
        self.sizer_buttons.Add(sline, 0, wx.EXPAND|wx.ALL, 5)
        self.tc_testimage = wx.TextCtrl(self, -1, size=(self.tc_width, -1))
        self.sizer_buttons.Add(self.tc_testimage, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_test_pick, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_test_imag, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.AddStretchSpacer()
        self.sizer_buttons.Add(self.button_ok, 0, wx.CENTER|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_cancel, 0, wx.CENTER|wx.ALL, 5)


    def populate_fields(self, persp_name):
        """Populate config fields from DisplaySystem perspective dict."""
        persd = self.persp_dict[persp_name]
        self.cb_master.SetValue(self.display_sys.use_perspective)
        self.tc_name.SetValue(persp_name)
        self.cb_dispsys_def.SetValue(persp_name == self.display_sys.default_perspective)
        self.choice_centr_disp.SetSelection(persd["central_disp"])
        px_per_mm = self.display_sys.max_ppi() / 25.4
        for tc, offs in zip(self.tclist_vieweroffs, persd["viewer_pos"]):
            tc.SetValue(str(offs / px_per_mm))
        self.populate_grid(persd["swivels"], persd["tilts"], px_per_mm)

    def populate_grid(self, swivels, tilts, px_per_mm):
        """Fill data grid from lists."""
        for row, sw, ti in zip(self.grid_rows, swivels, tilts):
            row[0].SetLabel(str(self.grid_rows.index(row)))
            row[1].SetSelection(sw[0])
            row[2].SetValue(str(sw[1]))
            row[3].SetValue(str(round(sw[2] / px_per_mm, 1)))
            row[4].SetValue(str(round(sw[3] / px_per_mm, 1)))
            row[5].SetValue(str(ti[0]))
            row[6].SetValue(str(round(ti[1] / px_per_mm, 1)))
            row[7].SetValue(str(round(ti[2] / px_per_mm, 1)))

    def collect_data_column(self, column):
        """Collect data from display data grid, returns a column as a list.

        Column ids are
            0   display id
            1   swivel axis
            2   swivel angle
            3   swivel lat offset
            4   swivel dep offset
            5   tilt angle
            6   tilt vert offset
            7   tilt dep offset
        """
        data = []

        for row in self.grid_rows:
            if column == 0:
                datum = row[column].GetSelection()
                try:
                    data.append(int(datum))
                except ValueError:
                    pass
            elif column == 1:
                datum = row[column].GetSelection()
                try:
                    data.append(int(datum))
                except ValueError:
                    pass
            else:
                datum = row[column].GetLineText(0)
                try:
                    data.append(float(datum))
                except ValueError:
                    pass
        return data

    def update_choiceprofile(self):
        """Reload profile list into the choice box."""
        self.profnames = list(self.persp_dict.keys())
        self.profnames.append("Create a new profile")
        self.choice_profiles.SetItems(self.profnames)

    def check_for_large_image_size(self, persp_name):
        """Compute how large an image the current perspective
        settings would produce as an intermediate step."""
        if self.frame.cb_offsets.GetValue():
            offsets = []
            for tc in self.frame.tc_list_offsets:
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
        crops = self.display_sys.get_ppi_norm_crops(offsets)
        persp_data = self.display_sys.get_persp_data(persp_name)
        if persp_data:
            proj_plane_crops, persp_coeffs = persp.get_backprojected_display_system(crops,
                                                                                    persp_data)
            # Canvas containing back-projected displays
            canv = wpproc.compute_working_canvas(proj_plane_crops)
        max_size = 12000
        if canv[0] > max_size or canv[1] > max_size:
            return (True, canv)
        return (False, canv)

    #
    # Button methods
    #
    def checkCbmaster(self, event=None):
        """Save master checkbox state into display system."""
        master = self.cb_master.GetValue()
        if master != self.display_sys.use_perspective:
            self.display_sys.use_perspective = master
            self.display_sys.save_system()

    def onSelect(self, event):
        """Acts once a profile is picked in the dropdown menu."""
        event_object = event.GetEventObject()
        if event_object.GetName() == "ProfileChoice":
            item = event.GetSelection()
            item_str = event.GetString()
            if item_str == "Create a new profile":
                self.onCreateNewProfile(event)
            else:
                self.populate_fields(item_str)
        else:
            pass

    def onSave(self, evt=None):
        """Save perspective config to file and update display system state."""
        persp_name = self.tc_name.GetLineText(0)
        if not persp_name:
            msg = "Profile name is required."
            show_message_dialog(msg)
            return 0
        toggle = self.cb_master.GetValue()
        is_ds_def = self.cb_dispsys_def.GetValue()
        centr_disp = int(self.choice_centr_disp.GetSelection())
        px_per_mm = self.display_sys.max_ppi() / 25.4
        try:
            # covert lenghts to ppi norm res
            viewer_offset = [
                px_per_mm * float(tc.GetLineText(0)) for tc in self.tclist_vieweroffs
            ]
        except ValueError:
            msg = "Viewer offsets should be lenghts in millimeters, separate decimals with a point."
            show_message_dialog(msg)
            return 0
        if viewer_offset[2] <= 0:
            msg = "Viewer distance must be entered and positive."
            show_message_dialog(msg)
            return 0
        viewer_data = (centr_disp, viewer_offset)
        swivels = []
        sw_axii = self.collect_data_column(1)
        sw_angl = self.collect_data_column(2)
        sw_lato = self.collect_data_column(3)
        sw_depo = self.collect_data_column(4)
        for ax, an, lo, do in zip(sw_axii, sw_angl, sw_lato, sw_depo):
            swivels.append(
                (ax, an, px_per_mm * lo, px_per_mm * do)
            )
        tilts = []
        ti_angl = self.collect_data_column(5)
        ti_vero = self.collect_data_column(6)
        ti_depo = self.collect_data_column(7)
        for an, vo, do in zip(ti_angl, ti_vero, ti_depo):
            tilts.append(
                (an, px_per_mm * vo, px_per_mm * do)
            )

        # update and save data
        # check for large images
        if self.warn_large_img:
            self.display_sys.update_perspectives(
                "temp", toggle, is_ds_def, viewer_data, swivels, tilts
            )
            too_large, canvas = self.check_for_large_image_size("temp")
            if too_large:
                msg = ("These perspective settings will produce large intermediate images "
                       + "which might use a large amount of system memory during processing. "
                       + "Take care not to set the perspective so that you would see arbitrarily "
                       + "far into the projected image as this will produce unboundedly large "
                       + "images and will cause problems, even a system crash."
                       + "\n\n"
                       + "Intermediate resolution with these settings is {}x{}".format(canvas[0], canvas[1])
                       + "\n\n"
                       + "Do you want to continue?\n"
                       + "\n"
                       + "This warning may be disabled from settings.")
                res = show_message_dialog(msg, "Info", style="YES_NO")
                if not res:
                    # Stop saving, remove temp
                    self.persp_dict.pop("temp", None)
                    return 0
                else:
                    # Continue and write profile
                    self.persp_dict.pop("temp", None)
                    self.display_sys.update_perspectives(
                        persp_name, toggle, is_ds_def, viewer_data, swivels, tilts
                    )
            else:
                # No large images, temp not needed
                self.persp_dict.pop("temp", None)
                self.display_sys.update_perspectives(
                    persp_name, toggle, is_ds_def, viewer_data, swivels, tilts
                )
        else:
            self.display_sys.update_perspectives(
                persp_name, toggle, is_ds_def, viewer_data, swivels, tilts
            )
        self.display_sys.save_perspectives()

        # update dialog profile list
        self.update_choiceprofile()
        self.choice_profiles.SetSelection(
            self.choice_profiles.FindString(persp_name)
        )
        return 1

    def onDeleteProfile(self, evt):
        """Delete selected perspective profile."""
        persp_name = self.choice_profiles.GetString(self.choice_profiles.GetSelection())
        if self.display_sys.default_perspective == persp_name:
            self.display_sys.default_perspective = None
            self.display_sys.save_system()
        self.persp_dict.pop(persp_name, None)
        self.display_sys.save_perspectives()
        # update dialog profile list
        self.update_choiceprofile()
        self.onCreateNewProfile(None)


    def onCreateNewProfile(self, evt):
        """Reset profile settings options to neutral state."""
        self.cb_master.SetValue(self.display_sys.use_perspective)
        self.choice_profiles.SetSelection(
            self.choice_profiles.FindString("Create a new profile")
        )
        self.tc_name.SetValue("")
        self.cb_dispsys_def.SetValue(False)
        self.choice_centr_disp.SetSelection(0)
        for tc in self.tclist_vieweroffs:
            tc.SetValue(str(0))
        swivels = wpproc.NUM_DISPLAYS*[(0, 0.0, 0.0, 0.0)]
        tilts = wpproc.NUM_DISPLAYS*[(0.0, 0.0, 0.0)]
        self.populate_grid(swivels, tilts, 1)


    def onOk(self, event):
        """Apply/save perspective settings and close dialog."""
        # self.checkCbmaster()
        if self.tc_name.GetValue():
            self.onSave()
        self.EndModal(wx.ID_OK)

    def onCancel(self, event):
        """Closes perspective config, throwing away unsaved contents."""
        self.Destroy()

    def onAlignTest(self, event=None, image=None):
        """Sets a test image wallpaper using the current perspectve config."""
        use_persp = self.cb_master.GetValue()
        if not use_persp:
            msg = "Perspective corrections are disabled. Enable them to test?"
            res = show_message_dialog(msg, style="YES_NO")
            if res:
                self.cb_master.SetValue(True)
                self.checkCbmaster() # update & save display_sys
            else:
                # Don't enable, stop testing.
                msg = "Perspective corrections are disabled, abort test."
                res = show_message_dialog(msg)
                return 0

        if image:
            testimage = [os.path.realpath(image)]
        else:
            testimage = [os.path.join(PATH, "superpaper/resources/test.png")]
        if not os.path.isfile(testimage[0]):
            msg = "Test image not found in {}.".format(testimage)
            show_message_dialog(msg, "Error")
            return 0

        # Use the settings currently written out in the fields!
        inches = [dsp.diagonal_size()[1] for dsp in self.display_sys.disp_list]

        offsets = []
        for off_tc in self.frame.tc_list_offsets:
            off = off_tc.GetLineText(0).split(",")
            try:
                offsets.append([int(off[0]), int(off[1])])
            except (IndexError, ValueError):
                show_message_dialog(
                    "Offsets must be integer pairs separated with a comma!\n"
                    "Problematic offset is {}".format(off)
                    )
                return 0
        flat_offsets = []
        for off in offsets:
            for pix in off:
                flat_offsets.append(pix)

        busy = wx.BusyCursor()

        # Save entered perspective values and get its name
        save_succ = self.onSave()
        if save_succ == 0:
            # Save failed or canceled, abort test.
            del busy
            return 0
        perspective = self.choice_profiles.GetString(
            self.choice_profiles.GetSelection()
        )

        wx.Yield()
        # Use the simplified CLI profile class
        wpproc.refresh_display_data()
        profile = CLIProfileData(testimage, advanced=True,
            perspective=perspective, spangroups=None, offsets=flat_offsets)
        thrd = change_wallpaper_job(profile, force=True)
        while thrd.is_alive():
            time.sleep(0.5)
        del busy
        return 1

    def onChooseTestImage(self, event):
        """Open a file dialog to choose a test image."""
        with wx.FileDialog(self, "Choose a test image",
                           wildcard=("Image files (*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tiff;*.webp)"
                                     "|*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tiff;*.webp"),
                           defaultDir=self.frame.defdir,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            self.test_image = file_dialog.GetPath()
            self.tc_testimage.SetValue(
                os.path.basename(self.test_image)
            )
        return

    def onTestWallpaper(self, event):
        """Test the current perspective options by triggering a new wallpaper
        from the active wallpaper profile, if any."""
        if self.test_image:
            self.onAlignTest(image=self.test_image)
        else:
            msg = "Choose a test image first."#.format(testimage)
            show_message_dialog(msg, "Error")
            return 0
        return 1

    def onHelpPerspective(self, evt):
        """Popup perspectives main help."""
        text = ("Perspective corrections were created to fix the\n"
                "wallpaper misalignment that arises when your diplays\n"
                "are not in a common plane, like they would be on the\n"
                "wall. Straight lines are cut into pieces when displays\n"
                "are both tilted and turned respective to each other.\n"
                "These corrections work by undoing the perspective changes\n"
                "caused by the rotation of the displays.\n"
                "\n"
                "In this dialog you may configure perspective setting\n"
                "profiles, and test their effects with the tools in the\n"
                "lower left corner."
                )
        # use_per = self.cb_master.GetValue()
        # persname = self.choice_profiles.GetString(self.choice_profiles.GetSelection())
        pop = HelpPopup(self, text,
                        show_image_quality=False,
                        # use_perspective=use_per,
                        # persp_name=persname
                        )
        btn = evt.GetEventObject()
        pos = btn.ClientToScreen((0, 0))
        sz = btn.GetSize()
        pop.Position(pos, (0, sz[1]))
        pop.Popup()

    def onHelpPersProfile(self, evt):
        """Popup perspective profile help."""
        text = ("Perspective corrections do not work equally well\n"
                "with different kinds of images so you can create\n"
                "separate profiles, such as 'tilts_only' or 'swivel+tilt'")
        pop = HelpPopup(self, text)
        btn = evt.GetEventObject()
        pos = btn.ClientToScreen((0, 0))
        sz = btn.GetSize()
        pop.Position(pos, (0, sz[1]))
        pop.Popup()

    def onHelpCentralDisp(self, evt):
        """Popup central display & viewer position help."""
        text = ("To compute the perspective transforms the (rough)\n"
                "position of your eyes relative to your displays\n"
                "needs to be known. This is entered by selecting\n"
                "one display as the central display and entering\n"
                "distance offsets relative to that display's center.\n"
                "\n"
                "Distance must be entered and non-zero, horizontal\n"
                "and vertical offsets are optional. Lenghts are\n"
                "in millimeters."
                )
        pop = HelpPopup(self, text)
        btn = evt.GetEventObject()
        pos = btn.ClientToScreen((0, 0))
        sz = btn.GetSize()
        pop.Position(pos, (0, sz[1]))
        pop.Popup()

    def onHelpData(self, evt):
        """Popup central display & viewer position help."""
        text = ("Here you enter the display rotation (tilt and swivel)\n"
                "parameters. Use these parameters to tell how your displays\n"
                "are rotated relative to the setup where they would be in a\n"
                "common plane.\n"
                "The parameters are:\n"
                "     - swivel axis: left or right edge of the display\n"
                "     - swivel angle in degrees\n"
                "     - swivel axis lateral offset from display edge [mm]\n"
                "     - swivel axis depth offset from display edge [mm]\n"
                "     - tilt angle in degrees\n"
                "     - tilt axis vertical offset from horizontal midline [mm]\n"
                "     - tilt axis depth offset from display surface [mm]",
                "Signs of angles are determined by the right hand rule:\n"
                "Grab the rotation axis with your right hand fist and extend\n"
                "your thumb in the direction of the axis: up for swivels and\n"
                "left for tilts. Now the direction of your curled fingers will\n"
                "tell the direction the display will rotate with a positive angle\n"
                "and the rotation is reversed for a negative angle.",
                "The axis offsets are completely optional. The most important\n"
                "one is the tilt axis DEPTH offset since the actual axis\n"
                "of the tilt is the joint in the display mount behind the panel.\n"
                "Without this depth offset the tilt is performed around the display\n"
                "horizontal midline which is on the display surface."
                )
        pop = HelpPopup(self, text)
        btn = evt.GetEventObject()
        pos = btn.ClientToScreen((0, 0))
        sz = btn.GetSize()
        pop.Position(pos, (0, sz[1]))
        pop.Popup()




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
        self.sizer_grid_settings = wx.GridSizer(6, 2, 5, 5)
        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        pnl = self
        st_logging = wx.StaticText(pnl, -1, "Logging")
        st_usehotkeys = wx.StaticText(pnl, -1, "Use hotkeys")
        st_warn_large = wx.StaticText(pnl, -1, "Large image warning")
        st_hk_next = wx.StaticText(pnl, -1, "Hotkey: Next wallpaper")
        st_hk_pause = wx.StaticText(pnl, -1, "Hotkey: Pause slideshow")
        st_setcmd = wx.StaticText(pnl, -1, "Custom command")
        self.cb_logging = wx.CheckBox(pnl, -1, "")
        self.cb_usehotkeys = wx.CheckBox(pnl, -1, "")
        self.cb_warn_large = wx.CheckBox(pnl, -1, "")
        self.tc_hk_next = wx.TextCtrl(pnl, -1, size=(200, -1))
        self.tc_hk_pause = wx.TextCtrl(pnl, -1, size=(200, -1))
        self.tc_setcmd = wx.TextCtrl(pnl, -1, size=(200, -1))

        self.sizer_grid_settings.AddMany(
            [
                (st_logging, 0, wx.ALIGN_RIGHT),
                (self.cb_logging, 0, wx.ALIGN_LEFT),
                (st_usehotkeys, 0, wx.ALIGN_RIGHT),
                (self.cb_usehotkeys, 0, wx.ALIGN_LEFT),
                (st_warn_large, 0, wx.ALIGN_RIGHT),
                (self.cb_warn_large, 0, wx.ALIGN_LEFT),
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
        self.sizer_buttons.AddStretchSpacer()
        self.sizer_buttons.Add(self.button_save, 0, wx.ALL, 5)
        self.sizer_buttons.Add(self.button_close, 0, wx.ALL, 5)
        self.sizer_main.Add(self.sizer_grid_settings, 0, wx.CENTER|wx.EXPAND|wx.ALL, 5)
        self.sizer_main.Add(self.sizer_buttons, 0, wx.EXPAND)
        self.SetSizer(self.sizer_main)
        self.sizer_main.Fit(parent)

    def update_fields(self):
        """Updates dialog field contents."""
        g_settings = GeneralSettingsData()
        self.cb_logging.SetValue(g_settings.logging)
        self.cb_usehotkeys.SetValue(g_settings.use_hotkeys)
        self.cb_warn_large.SetValue(g_settings.warn_large_img)
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
        current_settings.warn_large_img = self.cb_warn_large.GetValue()
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
    def __init__(self, parent=None):
        wx.Frame.__init__(self, parent=parent, title="Superpaper Help")
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        help_panel = HelpPanel(self)
        self.frame_sizer.Add(help_panel, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(self.frame_sizer)
        self.SetIcon(wx.Icon(TRAY_ICON, wx.BITMAP_TYPE_PNG))
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

        # st_show_at_start = wx.StaticText(self, -1, "Show this help at start")
        self.cb_show_at_start = wx.CheckBox(self, -1, "Show this help at start")
        self.cb_show_at_start.SetValue(show_help)
        self.button_close = wx.Button(self, label="Close")
        self.button_close.Bind(wx.EVT_BUTTON, self.onClose)
        self.sizer_buttons.AddStretchSpacer()
        # self.sizer_buttons.Add(st_show_at_start, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self.sizer_buttons.Add(self.cb_show_at_start, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self.sizer_buttons.Add(self.button_close, 0, wx.CENTER|wx.ALL, 5)

        help_str = """
How to use Superpaper:

In the Wallpaper Configuration you can adjust all your wallpaper settings.  Other  application  wide
settings  can be  changed in the  Settings menu.  Both  are  accessible from the  system tray menu.

IMPORTANT NOTE: For the wallpapers to be set correctly, you must set in your OS the background
fitting option to 'Span'.

Description of Wallpaper Configuration 'advanced span' options:
    In advanced span mode PPI, bezel and perspective corrections are applied to the wallpaper. The
    following settings are used to configure this:

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

    - Display rotations and viewer position
            Perspective corrections use the position of the viewer and the 3D alignment of the displays to
            adjust the shown image. Details on how to configure this are in the helps of the perspective
            configuration dialog.

Tips:
    - Superpaper running in the background is controlled from the Tray Icon/Applet.
    - To start Superpaper in the background, disable the 'Show this help at start' checkbox.
    - You can use the given example profiles as templates: just change the name and whatever else,
      save, and its a new profile.
    - 'Align Test' feature allows you to test your alignment settings.
"""
        # st_help = wx.StaticText(self, -1, help_str)
        st_help = wx.TextCtrl(self, -1, help_str, size=(700, 400),
                              style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.sizer_helpcontent.Add(st_help, 1, wx.EXPAND|wx.CENTER|wx.ALL, 5)

        self.sizer_main.Add(self.sizer_helpcontent, 1, wx.CENTER|wx.EXPAND)
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
                 show_image_quality=False,
                 use_perspective=False,
                 persp_name=None,
                 style=wx.BORDER_DEFAULT):
        wx.PopupTransientWindow.__init__(self, parent, style)
        self.mainframe = parent.frame
        self.display_sys = None
            # self.mainframe = parent.parent # persp dialog
        if show_image_quality:
            self.display_sys = self.mainframe.display_sys
            self.advanced_on = self.mainframe.show_advanced_settings
            self.show_image_quality = not self.mainframe.use_multi_image
            self.use_perspective = use_perspective
            self.persp_name = persp_name
        else:
            self.advanced_on = False
            self.show_image_quality = False
            self.use_perspective = False
            self.persp_name = None
        pnl = wx.Panel(self)
        # pnl.SetBackgroundColour("CADET BLUE")

        stlist = []
        if isinstance(text, str):
            st = wx.StaticText(pnl, -1, text)
            stlist.append(st)
        else:
            for textstr in text:
                st = wx.StaticText(pnl, -1, textstr)
                stlist.append(st)
        sizer = wx.BoxSizer(wx.VERTICAL)
        for st in stlist:
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
            if self.mainframe.cb_offsets.GetValue():
                offsets = []
                for tc in self.mainframe.tc_list_offsets:
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
            crops = self.display_sys.get_ppi_norm_crops(offsets)
            persp_data = None
            if self.use_perspective:
                persp_data = self.display_sys.get_persp_data(self.persp_name)
            if persp_data:
                proj_plane_crops, persp_coeffs = persp.get_backprojected_display_system(crops,
                                                                                        persp_data)
                # Canvas containing back-projected displays
                canv = wpproc.compute_working_canvas(proj_plane_crops)
            else:
                canv = wpproc.compute_working_canvas(crops)
        else:
            canv = wpproc.compute_canvas(
                wpproc.RESOLUTION_ARRAY,
                wpproc.DISPLAY_OFFSET_ARRAY
            )
        res_str = "{}x{}".format(canv[0], canv[1])
        fin = senten.format(res_str)
        return fin
