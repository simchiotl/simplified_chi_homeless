# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

from gui.manager import GuiManager

__all__ = [
    'MainFrame'
]


###########################################################################
## Class MainFrame
###########################################################################

@GuiManager.register('MAIN')
class MainFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Simplified Chinese Homeless", pos=wx.DefaultPosition,
                          size=wx.Size(500, 300), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        main_grid = wx.GridSizer(2, 2, 0, 0)

        self.btn_requester = wx.Button(self, wx.ID_ANY, u"Requester", wx.DefaultPosition, wx.Size(160, -1), 0)
        self.btn_requester.SetLabelMarkup(u"Requester")
        self.btn_requester.SetBitmap(wx.Bitmap(u"../resources/pics/download.png", wx.BITMAP_TYPE_ANY))
        main_grid.Add(self.btn_requester, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.btn_editor = wx.Button(self, wx.ID_ANY, u"Editor", wx.DefaultPosition, wx.Size(160, -1), 0)
        self.btn_editor.SetLabelMarkup(u"Editor")
        self.btn_editor.SetBitmap(wx.Bitmap(u"../resources/pics/editor.png", wx.BITMAP_TYPE_ANY))
        main_grid.Add(self.btn_editor, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizer(main_grid)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.btn_requester.Bind(wx.EVT_BUTTON, self.to_requester)
        self.btn_editor.Bind(wx.EVT_BUTTON, self.to_editor)

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def to_requester(self, event):
        GuiManager().enter_frame('REQUESTER')

    def to_editor(self, event):
        event.Skip()
