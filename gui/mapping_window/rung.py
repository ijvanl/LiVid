import tkinter as tk
import tkinter.ttk as ttk
import aux as aux, editor
import os, sys
import math

from enum import Enum

from mapping import MidiEvent, ValueMapping, EVENT_TYPES
from aux import *

from __init__ import LiVidModelStub

def try_int(x):
	try: return int(x)
	except: return None

class MIDIEventDisplay(ttk.Frame):
	def __init__(self, master, midi_event: MidiEvent):
		super().__init__(master)
		self.midi_event = midi_event

		self.tk_event_type = tk.StringVar(self)
		self.tk_values = [tk.StringVar(self) for i in range(3)]

		self.tk_event_type.set(self.midi_event.event_type)
		for (i, v) in enumerate(self.tk_values):
			v.set(self.midi_event.values[i] if self.midi_event.values[i] is not None else "")

		self.build_gui()

	def build_gui(self):
		value_names = [tk.StringVar(self) for i in range(3)]
		values_are_disabled = [tk.BooleanVar(self) for i in range(3)]

		def _event_type_trace(*_):
			self.midi_event.event_type = self.tk_event_type.get()
			for i in range(3):
				value_names[i].set(MidiEvent.value_names(self.tk_event_type.get())[i])
				values_are_disabled[i].set((MidiEvent.value_names(self.tk_event_type.get())[i] != ""))

		self.tk_event_type.trace_add("write", _event_type_trace)

		def _value_trace(i):
			if self.tk_values[i].get() == "":
				self.midi_event.values[i] = None
			else:
				t = try_int(self.tk_values[i].get())
				self.midi_event.values[i] = t

		for i in range(3):
			self.tk_values[i].trace_add("write", lambda *_, j=i: _value_trace(j))

		ttk.Combobox(self,
			values=EVENT_TYPES,
			state="readonly",
			textvariable=self.tk_event_type,
			width=17
		).grid(row=0, column=0)
		for i in range(3):
			EntryWithPlaceholder(
				self,
				textvariable=self.tk_values[i],
				plvariable=value_names[i],
				enabled=values_are_disabled[i],
				width=10
			).grid(row=0, column=i+1)
		
		# run trace functions
		self.tk_event_type.set(self.tk_event_type.get())
		for i in range(3):
			self.tk_values[i].set(self.tk_values[i].get())


class MappingDisplay(ttk.Frame):
	def __init__(self, master, model, midi_event: MidiEvent, value_mapping: ValueMapping):
		super().__init__(master)
		self.model = model
		self.midi_event = midi_event
		self.value_mapping = value_mapping

		self.build_gui()
	
	def build_gui(self):
		patch_values = list(self.model.get_current_patch()["values"].keys())

		(tk_lhs, tk_rhs) = (tk.StringVar(self), tk.StringVar(self))

		tk_lhs.set(self.value_mapping.lhs_value if self.value_mapping.lhs_value is not None else "")
		tk_rhs.set(self.value_mapping.rhs_value if self.value_mapping.rhs_value is not None else "")

		def _value_trace(*_):
			self.value_mapping.lhs_value = tk_lhs.get()
			self.value_mapping.rhs_value = tk_rhs.get()
		
		tk_lhs.trace_add("write", _value_trace)
		tk_rhs.trace_add("write", _value_trace)

		ttk.Label(self, text=ROLE_SYMBOLS["then"]).grid(column=1, row=0)
		ttk.Label(self, text="value").grid(column=2, row=0)

		self.lhs_combobox = ttk.Combobox(self, state="readonly", values=patch_values, textvariable=tk_lhs)
		self.lhs_combobox.grid(column=3, row=0)

		ttk.Label(self, text=ROLE_SYMBOLS["equals"]).grid(column=4, row=0)

		def _rhs_fill(*_):
			self.rhs_combobox["values"] = self.midi_event.my_value_names()

		self.rhs_combobox = ttk.Combobox(self, textvariable=tk_rhs, postcommand=_rhs_fill)
		self.rhs_combobox.grid(column=5, row=0)


class MappingRung(ttk.Frame):
	def __init__(self, master, model, midi_event: MidiEvent, value_mapping: ValueMapping):
		super().__init__(master)
		self.model = model
		self.midi_event = midi_event
		self.value_mapping = value_mapping

		self.build_gui()
	
	def build_gui(self):
		self.midi_display = MIDIEventDisplay(self, self.midi_event)
		self.value_display = MappingDisplay(self, self.model, self.midi_event, self.value_mapping)
		self.midi_display.grid(row=0, column=0)
		self.value_display.grid(row=1, column=0)