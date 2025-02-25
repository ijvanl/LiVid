import tkinter as tk
import tkinter.ttk as ttk
import aux as aux, editor
import os, sys
import math

from enum import Enum

from mapping import *
from aux import *

from __init__ import LiVidModelStub
from .mapping_list import *


def try_int(x):
	try: return int(x)
	except: return None


class LiVidMappingWindowFrame(tk.Frame):
	def __init__(self, master, model):
		super().__init__(master)
		self.model = model

		self.build_gui()
		#self.on_patch_selected(None)
	
	def build_gui(self):
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)

		self.main_frame = ttk.Frame(self)
		self.main_frame.grid(column=0, row=0, sticky=tk.N + tk.S + tk.E + tk.W)
		self.main_frame.columnconfigure(0, weight=1)
		self.main_frame.rowconfigure(0, weight=1)

		self.alt_frame = ttk.Frame(self, width=10, height=10)
		self.alt_frame.grid(column=0, row=0, sticky=tk.N + tk.S + tk.E + tk.W)
		self.alt_frame.grid_remove()

		self.patch_name_label = ttk.Label(self.main_frame, text="Patch Name")
		self.patch_name_label.pack(pady=20)

		self.mapping_list = MappingListbox(self.main_frame, self.model)
		self.mapping_list.pack()

	def on_tab_open(self):
		self.mapping_list.update_from_patch()

	def before_patch_selected(self, event):
		pass

	def after_patch_selected(self, event):
		if self.model.current_patch_name is None:
			self.main_frame.grid_remove()
			self.alt_frame.grid()
		else:
			self.alt_frame.grid_remove()
			self.main_frame.grid()
			self.patch_name_label["text"] = self.model.current_patch_name
			self.mapping_list.update_from_patch()