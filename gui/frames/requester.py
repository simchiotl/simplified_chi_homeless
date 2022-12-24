# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import logging
import os.path
from dataclasses import dataclass

import wx
import wx.xrc

from gui.manager import GuiManager
from schomeless.utils import DataClassExtension, Registerable
from schomeless.requester import BookRequester

__all__ = [
    'RequesterFrame'
]

logger = logging.getLogger('BOOK REQUESTER')


###########################################################################
## Class RequesterFrame
###########################################################################

@dataclass
class BookProps(DataClassExtension):
    filepath: str
    name: str = ''
    author: str = ''
    start_chapter: int = 1
    preface: str = ''


class ApiCollector(metaclass=Registerable):

    @staticmethod
    def create_api(frame):
        pass

    @staticmethod
    def create_request(frame):
        pass



ApiSettingsCollector.register('JJWXC')


def jjwxc_collector(frame):


@GuiManager.register('REQUESTER')
class RequesterFrame(wx.Frame):

    def __init__(self, parent):
        self.init_ui(parent)

    def init_ui(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Book Requester - Simplified Chinese Homeless",
                          pos=wx.DefaultPosition, size=wx.Size(663, 610),
                          style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        requester_column1 = wx.BoxSizer(wx.VERTICAL)

        self.requester_toolbar = wx.ToolBar(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                            wx.TB_HORIZONTAL | wx.TB_TEXT)
        self.cookie_manager = self.requester_toolbar.AddTool(wx.ID_ANY, u"Cookies",
                                                             wx.Bitmap(u"../resources/pics/cookie.png",
                                                                       wx.BITMAP_TYPE_ANY), wx.NullBitmap,
                                                             wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None)

        self.requester_toolbar.Realize()

        requester_column1.Add(self.requester_toolbar, 0, wx.EXPAND, 5)

        self.common_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        common_sizer = wx.StaticBoxSizer(wx.StaticBox(self.common_panel, wx.ID_ANY, u"Book properties"), wx.VERTICAL)

        common_column1 = wx.BoxSizer(wx.VERTICAL)

        common_row1 = wx.BoxSizer(wx.HORIZONTAL)

        self.common_text_name = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY, u"Name:", wx.DefaultPosition,
                                              wx.DefaultSize, 0)
        self.common_text_name.Wrap(-1)

        common_row1.Add(self.common_text_name, 0, wx.ALL, 5)

        self.common_edit_name = wx.TextCtrl(common_sizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                            wx.Size(200, -1), 0)
        common_row1.Add(self.common_edit_name, 2, wx.ALL, 5)

        self.common_text_author = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY, u"Author:", wx.DefaultPosition,
                                                wx.DefaultSize, 0)
        self.common_text_author.Wrap(-1)

        common_row1.Add(self.common_text_author, 0, wx.ALL, 5)

        self.common_edit_author = wx.TextCtrl(common_sizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString,
                                              wx.DefaultPosition, wx.DefaultSize, 0)
        common_row1.Add(self.common_edit_author, 1, wx.ALL | wx.EXPAND, 5)

        common_column1.Add(common_row1, 1, wx.EXPAND, 5)

        common_row2 = wx.BoxSizer(wx.HORIZONTAL)

        self.common_text_dirname = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY, u"Save to", wx.DefaultPosition,
                                                 wx.DefaultSize, 0)
        self.common_text_dirname.Wrap(-1)

        common_row2.Add(self.common_text_dirname, 0, wx.ALL, 5)

        self.common_edit_dirname = wx.DirPickerCtrl(common_sizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString,
                                                    u"Select a folder", wx.DefaultPosition, wx.DefaultSize,
                                                    wx.DIRP_SMALL)
        common_row2.Add(self.common_edit_dirname, 1, wx.ALL, 5)

        self.common_text_filename = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY, u"Filename Format",
                                                  wx.DefaultPosition, wx.DefaultSize, 0)
        self.common_text_filename.Wrap(-1)

        common_row2.Add(self.common_text_filename, 0, wx.ALL, 5)

        common_filename_column = wx.BoxSizer(wx.VERTICAL)

        self.common_edit_filename = wx.TextCtrl(common_sizer.GetStaticBox(), wx.ID_ANY, u"【{author}】{name}",
                                                wx.DefaultPosition, wx.Size(50, -1), 0)
        common_filename_column.Add(self.common_edit_filename, 0, wx.ALL | wx.EXPAND, 5)

        self.common_text_filename_info = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY,
                                                       u"{author}: author, {name}: book name", wx.DefaultPosition,
                                                       wx.DefaultSize, 0)
        self.common_text_filename_info.Wrap(-1)

        self.common_text_filename_info.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        common_filename_column.Add(self.common_text_filename_info, 0, wx.ALL, 5)

        common_row2.Add(common_filename_column, 3, 0, 5)

        common_column1.Add(common_row2, 0, wx.EXPAND, 5)

        common_row4 = wx.BoxSizer(wx.HORIZONTAL)

        self.common_text_filepath_label = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY, u"Filepath:",
                                                        wx.DefaultPosition, wx.DefaultSize, 0)
        self.common_text_filepath_label.Wrap(-1)

        common_row4.Add(self.common_text_filepath_label, 0, wx.ALL, 5)

        self.common_text_filepath = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY, u"【】.txt", wx.DefaultPosition,
                                                  wx.DefaultSize, 0)
        self.common_text_filepath.Wrap(-1)

        common_row4.Add(self.common_text_filepath, 1, wx.ALL, 5)

        common_column1.Add(common_row4, 1, wx.EXPAND, 5)

        common_row3 = wx.BoxSizer(wx.HORIZONTAL)

        self.common_text_start = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY, u"Chapter index starts at",
                                               wx.DefaultPosition, wx.DefaultSize, 0)
        self.common_text_start.Wrap(-1)

        common_row3.Add(self.common_text_start, 0, wx.ALL, 5)

        self.common_edit_start = wx.TextCtrl(common_sizer.GetStaticBox(), wx.ID_ANY, u"1", wx.DefaultPosition,
                                             wx.Size(50, -1), wx.TE_CENTER)
        common_row3.Add(self.common_edit_start, 0, wx.ALL, 5)

        common_column1.Add(common_row3, 1, wx.EXPAND, 5)

        common_sizer.Add(common_column1, 1, wx.EXPAND, 5)

        self.common_text_preface = wx.StaticText(common_sizer.GetStaticBox(), wx.ID_ANY,
                                                 u"Preface (content before first chapter):", wx.DefaultPosition,
                                                 wx.DefaultSize, 0)
        self.common_text_preface.Wrap(-1)

        common_sizer.Add(self.common_text_preface, 0, wx.ALL, 5)

        self.common_edit_preface = wx.TextCtrl(common_sizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString,
                                               wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE)
        common_sizer.Add(self.common_edit_preface, 0, wx.ALL | wx.EXPAND, 5)

        self.common_panel.SetSizer(common_sizer)
        self.common_panel.Layout()
        common_sizer.Fit(self.common_panel)
        requester_column1.Add(self.common_panel, 1, wx.ALL | wx.EXPAND, 5)

        self.settings_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        setting_row = wx.BoxSizer(wx.HORIZONTAL)

        request_typeChoices = [u"From catalogue", u"Chapter by chapter"]
        self.request_type = wx.RadioBox(self.settings_panel, wx.ID_ANY, u"Request Type", wx.DefaultPosition,
                                        wx.DefaultSize, request_typeChoices, 1, wx.RA_SPECIFY_COLS)
        self.request_type.SetSelection(0)
        setting_row.Add(self.request_type, 0, wx.ALL, 5)

        self.api_panel = wx.Notebook(self.settings_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.jjwxc = wx.Panel(self.api_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        jjwxc_column = wx.BoxSizer(wx.VERTICAL)

        self.jjwxc_text_url = wx.StaticText(self.jjwxc, wx.ID_ANY, u"URL:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.jjwxc_text_url.Wrap(-1)

        jjwxc_column.Add(self.jjwxc_text_url, 0, wx.ALL, 5)

        self.jjwxc_edit_url = wx.TextCtrl(self.jjwxc, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, -1), 0)
        jjwxc_column.Add(self.jjwxc_edit_url, 0, wx.ALL | wx.EXPAND, 5)

        self.jjwxc_helper = wx.StaticText(self.jjwxc, wx.ID_ANY,
                                          u"The URL of the book, e.g. https://www.jjwxc.net/onebook.php?novelid=xxxxxx",
                                          wx.DefaultPosition, wx.DefaultSize, 0)
        self.jjwxc_helper.Wrap(-1)

        self.jjwxc_helper.SetFont(
            wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        jjwxc_column.Add(self.jjwxc_helper, 0, wx.ALL, 5)

        self.jjwxc.SetSizer(jjwxc_column)
        self.jjwxc.Layout()
        jjwxc_column.Fit(self.jjwxc)
        self.api_panel.AddPage(self.jjwxc, u"JJWXC", True)
        self.lofter = wx.Panel(self.api_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        lofter_column = wx.BoxSizer(wx.VERTICAL)

        lofter_sourceChoices = [u"Collection", u"Blog", u"Post"]
        self.lofter_source = wx.RadioBox(self.lofter, wx.ID_ANY, u"Source", wx.DefaultPosition, wx.DefaultSize,
                                         lofter_sourceChoices, 1, wx.RA_SPECIFY_ROWS)
        self.lofter_source.SetSelection(0)
        lofter_column.Add(self.lofter_source, 0, wx.ALL | wx.EXPAND, 5)

        self.lofter_text_url = wx.StaticText(self.lofter, wx.ID_ANY, u"URL:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lofter_text_url.Wrap(-1)

        lofter_column.Add(self.lofter_text_url, 0, wx.ALL, 5)

        self.lofter_edit_url = wx.TextCtrl(self.lofter, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, -1),
                                           wx.TE_AUTO_URL)
        lofter_column.Add(self.lofter_edit_url, 0, wx.ALL | wx.EXPAND, 5)

        self.lofter_helper = wx.StaticText(self.lofter, wx.ID_ANY,
                                           u"The URL of the collection, e.g. https://www.lofter.com/front/blog/collection/share?collectionId=xxxx",
                                           wx.DefaultPosition, wx.DefaultSize, 0)
        self.lofter_helper.Wrap(200)

        self.lofter_helper.SetFont(
            wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        lofter_column.Add(self.lofter_helper, 0, wx.ALL, 5)

        self.lofter.SetSizer(lofter_column)
        self.lofter.Layout()
        lofter_column.Fit(self.lofter)
        self.api_panel.AddPage(self.lofter, u"Lofter", False)

        setting_row.Add(self.api_panel, 1, wx.EXPAND, 5)

        self.settings_panel.SetSizer(setting_row)
        self.settings_panel.Layout()
        setting_row.Fit(self.settings_panel)
        requester_column1.Add(self.settings_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.btn_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(-1, 50), wx.TAB_TRAVERSAL)
        button_row = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_download = wx.Button(self.btn_panel, wx.ID_ANY, u"Download", wx.DefaultPosition, wx.Size(-1, -1), 0)

        self.btn_download.SetDefault()
        button_row.Add(self.btn_download, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.btn_panel.SetSizer(button_row)
        self.btn_panel.Layout()
        requester_column1.Add(self.btn_panel, 1, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.SetSizer(requester_column1)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.common_edit_name.Bind(wx.EVT_TEXT, self.update_filename)
        self.common_edit_author.Bind(wx.EVT_TEXT, self.update_filename)
        self.common_edit_dirname.Bind(wx.EVT_DIRPICKER_CHANGED, self.update_filename)
        self.common_edit_filename.Bind(wx.EVT_TEXT, self.update_filename)
        self.request_type.Bind(wx.EVT_RADIOBOX, self.on_request_type_changed)
        self.api_panel.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_api_changed)
        self.lofter_source.Bind(wx.EVT_RADIOBOX, self.on_lofter_source_changed)
        self.btn_download.Bind(wx.EVT_BUTTON, self.start_download)

    def __del__(self):
        pass

    # data collection
    def collect_filepath(self):
        info = {k: getattr(self, f"common_edit_{k}").GetValue() for k in ['name', 'author']}
        dirname = self.common_edit_dirname.GetPath()
        filename_format = self.common_edit_filename.GetValue()
        filepath = os.path.join(dirname, filename_format.format(**info) + '.txt')
        return filepath

    def collect_book_properties(self):
        try:
            start = self.common_edit_start.GetValue()
            assert start.isdigit(), 'The chapter starting index must be integer!'
            return BookProps(
                filepath=self.collect_filepath(),
                name=self.common_edit_name.GetValue(),
                author=self.common_edit_author.GetValue(),
                start_chapter=int(start),
                preface=self.common_edit_preface.GetValue()
            )
        except Exception as e:
            wx.MessageBox(str(e), "Validation Error", wx.OK, self)

    def collect_requester(self):
        requester_names = ['ASYNC', 'ITER']
        api_names = ['JJWXC', 'LOFTER']
        api = ApiSettingsCollector[api_names[self.api_panel.GetSelection()]](self)
        requester = BookRequester[requester_names[self.request_type.GetSelection()]](api, add_enter=False)
        return requester

    # Virtual event handlers, override them in your derived class
    def update_filename(self, event):
        self.common_text_filepath.SetLabel(self.collect_filepath())

    def start_download(self, event):
        book_props = self.collect_book_properties()
        logger.debug(book_props)
        requester = self.collect_requester()
