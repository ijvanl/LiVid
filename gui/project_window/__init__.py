import tkinter as tk
import tkinter.ttk as ttk
import os, sys
import math

from enum import Enum

from mapping import *
from gui.aux import *
from gui.editor_window.editor import *

from model import LiVidModelController


class LiVidProjectWindowFrame(tk.Frame):
	def __init__(self, master, mc: LiVidModelController):
		super().__init__(master)
		self.main_window = master
		self.mc = mc

		self.build_gui()
		#self.on_patch_selected(None)
	
	def build_gui(self):
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)

		self.main_frame = ttk.Frame(self, padding=20)
		self.main_frame.grid(column=0, row=0)
		self.main_frame.columnconfigure(0, weight=1)
		self.main_frame.rowconfigure(0, weight=1)

		self.project_name_display = ttk.Label(
			self.main_frame,
			text="Project",
			font=("System", 19, "bold")
		)
		self.project_name_display.grid(column=0, row=0)

	def update_data(self):
		pass

	def on_tab_open(self):
		self.update_data()

	def before_patch_selected(self, event):
		pass

	def after_patch_selected(self, event):
		self.update_data()