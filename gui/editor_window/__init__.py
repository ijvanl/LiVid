import tkinter as tk
import tkinter.ttk as ttk
import os, sys
import math

from enum import Enum

from mapping import *
from gui.aux import *

from model import LiVidModelController

from .editor import *

def try_int(x):
	try: return int(x)
	except: return None


class LiVidEditorWindowFrame(tk.Frame):
	def __init__(self, master, model: LiVidModelController):
		super().__init__(master)
		self.model = model

		self.build_gui()
		#self.on_patch_selected(None)
	
	def build_gui(self):
		self.editor = PatchTextEditor(self)
		self.editor.grid(column=0, row=0, sticky=tk.N + tk.S + tk.E + tk.W)

		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)

	def on_tab_open(self):
		pass

	def on_modified(self):
		if self.model.get_current_patch() is not None:
			self.model.get_current_patch().text = self.editor.get_text()
			self.model.get_current_patch().update_code()

	def before_patch_selected(self, event):
		if self.model.get_current_patch() is not None:
			self.model.get_current_patch().text = self.editor.get_text()
			self.model.get_current_patch().update_code()

	def after_patch_selected(self, event):
		if self.model.get_current_patch() is None:
			self.editor.open_text("")
			self.editor.text.config(state=tk.DISABLED)
		else:
			self.editor.text.config(state=tk.NORMAL)
			self.editor.open_text(self.model.get_current_patch().text)
			self.model.get_current_patch().update_code()