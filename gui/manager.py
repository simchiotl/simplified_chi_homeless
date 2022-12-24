from schomeless.utils import Singleton, Registerable, EnumExtension

__all__ = [
    'GuiManager'
]


class _GuiManagerMeta(Singleton, Registerable):
    pass


class WindowOperations(EnumExtension):
    CLOSE = 0
    HIDE = 1
    NONE = 2

    @staticmethod
    def deal(frame, opt):
        if opt == WindowOperations.CLOSE:
            frame.Destroy()
        elif opt == WindowOperations.HIDE:
            frame.Show(False)


class GuiManager(metaclass=_GuiManagerMeta):

    def __init__(self):
        self.frames = {}
        self.current = None

    def enter_frame(self, name, how_last=WindowOperations.HIDE):
        """

        Args:
            name (str):
            how_last (WindowOperations, optional): how to deal with the last frame

        Returns:

        """
        if self.current is not None:
            WindowOperations.deal(self.current, how_last)
        if name not in self.frames:
            self.current = GuiManager[name](None)
        else:
            self.current = self.frames[name]
        self.current.Show(True)
