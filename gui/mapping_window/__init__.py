import tkinter as tk
import tkinter.ttk as ttk
import os, sys
import math

from enum import Enum

from mapping import *
from gui.aux import *

from .mapping_list import *

from model import LiVidModelController


def try_int(x):
	try: return int(x)
	except: return None


class LiVidMappingWindowFrame(tk.Frame):
	def __init__(self, master, mc: LiVidModelController):
		super().__init__(master)
		self.mc = mc

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

		self.mapping_list = MappingListbox(self.main_frame, self.mc)
		self.mapping_list.pack()

	def on_tab_open(self):
		if self.mc.get_current_patch() is not None:
			self.mc.get_current_patch().update_code()
		self.mapping_list.update_from_patch()

	def before_patch_selected(self, event):
		pass

	def after_patch_selected(self, event):
		if self.mc.current_patch_name is None:
			self.main_frame.grid_remove()
			self.alt_frame.grid()
		else:
			self.alt_frame.grid_remove()
			self.main_frame.grid()
			self.patch_name_label["text"] = self.mc.current_patch_name
			if self.mc.get_current_patch() is not None:
				self.mc.get_current_patch().update_code()
			self.mapping_list.update_from_patch()