from schomeless.utils import Singleton, Registerable

__all__ = [
    'GuiManager'
]


class _GuiManagerMeta(Singleton, Registerable):
    pass


class GuiManager(metaclass=_GuiManagerMeta):

    def __init__(self):
        self.frames = {}
        self.current = None

    def enter_frame(self, name):
        if self.current is not None:
            self.current.Show(False)
        if name not in self.frames:
            self.current = GuiManager[name](None)
        else:
            self.current = self.frames[name]
        self.current.Show(True)
