"""Error etc. info dialog."""

import wx

def show_message_dialog(message, msg_type="Info", parent=None):
    """General purpose info dialog in GUI mode."""
    # Type can be 'Info', 'Error', 'Question', 'Exclamation'
    dial = wx.MessageDialog(parent, message, msg_type, wx.OK|wx.STAY_ON_TOP|wx.CENTRE)
    dial.ShowModal()
