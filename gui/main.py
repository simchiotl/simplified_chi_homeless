import os

from wx import App

from gui.manager import GuiManager
from schomeless.utils import LogTool

LOG_LEVEL = os.environ.get('SCHOMELESS_LOG_LEVEL', 'DEBUG')
LogTool.config_logger(LOG_LEVEL)

try:
    exec('import gui.frames')
    exec('del gui.frames')
except AttributeError:
    pass

app = App()
GuiManager().enter_frame('MAIN')
app.MainLoop()
