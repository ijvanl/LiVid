import tkinter as tk
import tkinter.ttk as ttk
import os, sys
import math

from enum import Enum

from mapping import *
from gui.aux import *

from . import *
from .rung import *


class MappingListbox(ttk.Frame):
	def __init__(self, master, model):
		super().__init__(master)
		self.model = model
		#mappings = self.model.get_current_patch()["mappings"]
		self.iid_counter = 0

		self.build_gui()
	
	def get_iid(self):
		self.iid_counter += 1
		return self.iid_counter
	
	def add_new_mapping(self):
		self.model.get_current_patch().mappings.append(Mapping.default())
		self.update_from_patch()
	
	def remove_mapping(self, i):
		self.model.get_current_patch().mappings.pop(i)
		self.update_from_patch()

	def build_gui(self):
		self.list_frame = ttk.Frame(self)
		self.list_frame.grid(column=0, row=0)
		self.list_frame.columnconfigure(0, weight=1)

		ttk.Separator(self).grid(column=0, row=1, sticky=tk.E + tk.W)

		self.mapping_bar = ttk.Frame(self)
		self.mapping_bar.grid(column=0, row=2)
		self.mapping_bar.columnconfigure(0, weight=1)

		RoledButton(self.mapping_bar, role="add", command=self.add_new_mapping).grid(column=1, row=0)


	def update_from_patch(self):
		patch = self.model.get_current_patch()

		for child in self.list_frame.winfo_children():
			child.grid_remove()
			child.destroy()
			del child

		if patch is not None:
			for (i, mapping) in enumerate(patch.mappings):
				element_frame = ttk.Frame(self.list_frame)
				element_frame.columnconfigure(0, weight=1)

				mapping_rung = MappingRung(element_frame, self.model, mapping.midi_event, mapping.value_mapping)
				mapping_rung.grid(column=0, row=0)
				RoledButton(
					element_frame, role="remove",
					command=lambda j=i, *_: self.remove_mapping(j)
				).grid(column=1, row=0)

				element_frame.grid(column=0, row=i, pady=5)
		
		if len(self.list_frame.grid_slaves()) == 0:
			ttk.Frame(self.list_frame).grid()

		self.update_idletasks()
