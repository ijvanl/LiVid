import tkinter as tk
import tkinter.ttk as ttk
import os, sys
import math

from enum import Enum

from mapping import *
from gui.aux import *

from model import LiVidModel


class LiVidPatchWindowFrame(tk.Frame):
	def __init__(self, master, model: LiVidModel):
		super().__init__(master)
		self.main_window = master
		self.model = model

		self.build_gui()
		#self.on_patch_selected(None)
	
	def build_gui(self):
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)

		self.main_frame = ttk.Frame(self, padding=20)
		self.main_frame.grid(column=0, row=0)
		self.main_frame.columnconfigure(0, weight=1)
		self.main_frame.rowconfigure(0, weight=1)

		self.alt_frame = ttk.Frame(self, width=10, height=10)
		self.alt_frame.grid(column=0, row=0, sticky=tk.N + tk.S + tk.E + tk.W)
		self.alt_frame.grid_remove()

		self.patch_name = tk.StringVar(self, "Patch")

		def _patch_name_change(*_):
			if self.model.current_patch_name is not None and self.patch_name.get() != self.model.current_patch_name:
				new_name = self.patch_name.get()
				old_name = str(self.model.current_patch_name)

				if len(new_name) > 0 and not (new_name in self.model.patches):
					self.model.patches[old_name].name = new_name
					self.model.patches[new_name] = self.model.patches.pop(old_name)
					self.main_window.update_patch_listbox(new_index=new_name)
					self.model.current_patch_name = new_name
				elif new_name in self.model.patches:
					self.model.patches[old_name].name = f"{new_name} 1"
					self.model.patches[f"{new_name} 1"] = self.model.patches.pop(old_name)
					self.main_window.update_patch_listbox(new_index=f"{new_name} 1")
					self.model.current_patch_name = f"{new_name} 1"

		self.patch_name.trace_add("write", _patch_name_change)

		self.patch_name_display = ttk.Entry(
			self.main_frame,
			textvariable=self.patch_name,
			style="TLabel",
			font=("System", 19, "bold")
		)
		self.patch_name_display.grid(column=0, row=0)

	def update_data(self):
		if self.model.get_current_patch() is not None:
			self.alt_frame.grid_remove()
			self.main_frame.grid()
			
			self.patch_name.set(self.model.current_patch_name)
		else:
			self.main_frame.grid_remove()
			self.alt_frame.grid()


	def on_tab_open(self):
		self.update_data()

	def before_patch_selected(self, event):
		pass

	def after_patch_selected(self, event):
		self.update_data()