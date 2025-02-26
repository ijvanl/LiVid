from gui import *
from model import *
from video import *

import tkinter as tk

class LiVidApp:
	def __init__(self):
		self.backend = VideoRenderer()
		self.mc = LiVidModelController(self.backend)

		self.tk = tk.Tk()
		self.tk.withdraw()

		self.mc.tk = self.tk

		self.gui = main_window.LiVidMainWindow(self.tk, self.mc)

		self.tk.mainloop()