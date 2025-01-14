import lidar
import cv2, numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops

from postprocess import *
import pp_builtins

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

import threading
import sys, os, subprocess
import base64
import pickle
import json
from ast import literal_eval
import mido

LIVID_VERSION = "0.0.1"
CURRENT_YEAR = "2025"

class VideoPPInfo:
	def __init__(self, pp_type, value_dict={}):
		self.pp_type = pp_type
		self.value_dict = value_dict
	
	def default():
		return VideoPPInfo("PPDepth", value_dict={ "contrast": 1.0 })

	def save(self):
		return literal_eval(str(self.__dict__))

	def load(self, d: dict):
		self.pp_type = d["pp_type"]
		self.value_dict = d["value_dict"]

def load_pp_info(d: dict):
	pp = VideoPPInfo.default()
	pp.load(d)
	return pp

###

PP_SAVE_SLOT_COUNT = 64

MIDI_RESCAN_INTERVAL_MS = 1000

SCALE_W = 300

class LiVidApp:
	def __init__(self, device):
		self.device = device
		self.device.postprocess_function = self.postprocess_fn

		self.pp_suites_imported = []
		self.pp_suites_imported_text = [] # for use in pickling

		self.pp_save_slots = [VideoPPInfo.default() for i in range(PP_SAVE_SLOT_COUNT)]
		self.current_pp_save = 0
		self.pp_save_changed = False
		self.pp_revert = VideoPPInfo.default()

		self.zoom_x = 320
		self.zoom_y = 240
		self.zoom_amount = 1

		self.use_midi_device = False

		self.allow_midi_input = None
		self.midi_channel = 0
		self.midi_port = None

		self.live_mode = False
		self.keyboard_trigger_bank = 0

		self.last_pp_type = ""
		self.pp_func_cache = None

		self.current_sliders = {}

	def callback(self):
		self.gui.quit()

	### FILE FUNCTIONS

	def save_patch_bank_to_file(self):
		with filedialog.asksaveasfile(mode='w+', defaultextension=".vvpb", initialfile="New Patch Bank.vvpb") as f:
			patches = [p.save() for p in self.pp_save_slots]
			scripts = [(n, base64.b64encode(s).decode("utf-8")) for (n, s) in self.pp_suites_imported_text]

			save = {
				"version": LIVID_VERSION,
				"imported_scripts": scripts,
				"patches": patches,
				"last_save": self.current_pp_save
			}

			f.write(json.dumps(save))

	def save_single_patch_to_file(self):
		with filedialog.asksaveasfile(mode='w+', defaultextension=".vvp", initialfile="New Patch.vvp") as f:
			patch = self.pp_save_slots[self.current_pp_save].save()
			scripts = [(n, base64.b64encode(s).decode("utf-8")) for (n, s) in self.pp_suites_imported_text]

			save = {
				"version": LIVID_VERSION,
				"imported_scripts": scripts,
				"patch": patch,
			}

			f.write(json.dumps(save))

	def load_patch_bank_from_file(self):
		with filedialog.askopenfile(mode="r", defaultextension=".vvpb") as f:
			load = json.load(f)
			for script in load["imported_scripts"]:
				(name, text) = (script[0], base64.b64decode(script[1]))
				self.import_new_pp_func_from_text(text, f.name)
				# so __file__ == the .vvpb file (for asset reasons)

			patches = [load_pp_info(p) for p in load["patches"]]
			
			self.pp_save_slots = patches
			self.switch_patch(load["last_save"])

	def load_single_patch_from_file(self):
		with filedialog.askopenfile(mode="r", defaultextension=".vvp") as f:
			load = json.load(f)
			for script in load["imported_scripts"]:
				(name, text) = (script[0], base64.b64decode(script[1]))
				self.import_new_pp_func_from_text(text, f.name)
				# so __file__ == the .vvp file (for asset reasons)
			
			self.pp_save_slots[self.current_pp_save] = load_pp_info(load["patch"])
			self.build_sliders()
			self.update_save_labels()

	def create_new_script_from_template(self):
		tf = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.py"), "r")
		template = tf.read()
		tf.close()

		f = filedialog.asksaveasfile(mode="w", defaultextension=".py", initialfile="new_script.py")
		fname = f.name
		f.write(template)
		f.close()

		open_file(fname)

	def import_new_pp_func(self):
		with filedialog.askopenfile("rb", defaultextension=".py") as source_file:
			source_text = source_file.read()
			self.import_new_pp_func_from_text(source_text, source_file.name)

	def import_new_pp_func_from_text(self, source_text, name):
		code = compile(source_text, name, "exec")
		file_globals = { "__file__": name }
		exec(code, file_globals)
		self.pp_suites_imported.extend(file_globals["__PP_FUNCTIONS_SUITE__"])
		self.pp_suites_imported_text.append((name, source_text))
		self.update_pp_rolodex()

	def find_pp_func_in_imported(self, fname):
		pp = pp_builtins.__PP_FUNCTIONS_SUITE__ + self.pp_suites_imported
		for s in pp:
			if s.__class__.__name__ == fname:
				return s
		return None

	def get_all_pp_func_names(self):
		pp = pp_builtins.__PP_FUNCTIONS_SUITE__ + self.pp_suites_imported
		return [s.__class__.__name__ for s in pp]

	### PATCH FUNCTIONS

	def switch_patch(self, to):
		self.current_pp_save = to
		self.pp_save_changed = False
		self.pp_revert.load(self.pp_save_slots[self.current_pp_save].save())
		self.build_sliders()
		self.update_save_labels()

	def fix_patch_changes(self):
		self.switch_patch(self.current_pp_save)
		self.update_save_labels()

	def revert_patch_changes(self):
		self.pp_save_changed = False
		self.pp_save_slots[self.current_pp_save].load(self.pp_revert.save())
		self.build_sliders()
		self.update_save_labels()

	def new_value_dict(self, old_dict, new_dict):
		for k in new_dict:
			if not k in old_dict:
				old_dict[k] = new_dict[k][2] # default value
		print(old_dict)

	def change_pp_type_from_rolodex(self, value):
		print(value)
		self.pp_save_slots[self.current_pp_save].pp_type = value
		self.new_value_dict(
			self.pp_save_slots[self.current_pp_save].value_dict,
			self.find_pp_func_in_imported(value).values()
		)
		self.pp_save_changed = True
		self.build_sliders()
		self.update_save_labels()

	def chg_var(self, var, x, label):
		self.pp_save_slots[self.current_pp_save].__dict__[var] = float(x)
		label["text"] = f"{float(x):8.2f}"
		self.pp_save_changed = True
		self.update_save_labels()

	def chg_var_self(self, var, x, label):
		self.__dict__[var] = float(x)
		label["text"] = f"{float(x):8.2f}"

	### GUI FUNCTIONS

	def build_sliders(self):
		root = self.slider_frame
		
		print("build_sliders")

		for s in self.current_sliders.values():
			s["name_label"].destroy()
			s["slider"].destroy()
			s["value_label"].destroy()
		self.current_sliders.clear()

		grid_row = 0 # start here, shall we

		for (k, v) in self.find_pp_func_in_imported(self.pp_save_slots[self.current_pp_save].pp_type).values().items():
			(name, minval, defval, maxval) = v
			tkval = tk.DoubleVar(self.gui)
			name_label = ttk.Label(root, text=name)
			name_label.grid(column=0, row=grid_row, sticky="w")
			slider = ttk.Scale(
				root, from_=minval, to=maxval, length=SCALE_W, variable=tkval,
				command=lambda x: self.update_slider_values()
			)
			slider.grid(column=1, row=grid_row, padx=10)
			value_label = ttk.Label(root, text="", font=("Courier", 13))
			value_label.grid(column=2, row=grid_row, sticky="e")

			grid_row += 1

			self.current_sliders[k] = {
				"tkval": tkval,
				"name_label": name_label,
				"slider": slider,
				"value_label": value_label
			}
		
		self.update_sliders()
		print("build_sliders complete")

	def update_sliders(self):
		self.pp_type_rolodex_value.set(self.pp_save_slots[self.current_pp_save].pp_type)
		for (k, v) in self.current_sliders.items():
			v["tkval"].set(self.pp_save_slots[self.current_pp_save].value_dict[k])
			v["value_label"]["text"] = f"{float(v["tkval"].get()):8.2f}"

	def update_slider_values(self):
		for (k, v) in self.current_sliders.items():
			self.pp_save_slots[self.current_pp_save].value_dict[k] = v["tkval"].get()
		self.update_sliders()

	def update_pp_rolodex(self):
		self.pp_type_rolodex["menu"].delete(0, "end")
		for opt in self.get_all_pp_func_names():
			self.pp_type_rolodex["menu"].add_command(
				label=opt, command=tk._setit(self.pp_type_rolodex_value, opt, self.change_pp_type_from_rolodex)
			)

	def update_save_labels(self):
		if self.pp_save_changed:
			self.save_label_midi["text"] = f"Patch {self.current_pp_save + 1} of {PP_SAVE_SLOT_COUNT} (unsaved)"
			self.save_label_midi["bg"] = "#DDAA00"
		else:
			self.save_label_midi["text"] = f"Patch {self.current_pp_save + 1} of {PP_SAVE_SLOT_COUNT} (saved)"
			self.save_label_midi["bg"] = "#00FFDD"

		for i, s in enumerate(self.save_labels_kb):
			s["text"] = str((i + 1) + (self.keyboard_trigger_bank * 8))
			if self.current_pp_save == (self.keyboard_trigger_bank * 8 + i):
				if self.pp_save_changed: s["bg"] = "#DDAA00"
				else: s["bg"] = "#00FFDD"
			else: s["bg"] = "#00AA00"

	def update_live_mode(self):
		self.live_mode = not self.live_mode

		if self.live_mode == True:
			self.optfrm.grid_forget()
			self.live_mode_enabled_label.grid(column=0, row=4, pady=125)
			self.allow_midi_input.set(1)
			self.live_mode_button["text"] = "Exit live mode"
		else:
			self.live_mode_enabled_label.grid_forget()
			self.optfrm.grid(column=0, row=4, pady=10)
			self.allow_midi_input.set(0)
			self.live_mode_button["text"] = "Enter live mode"
		
		print(self.live_mode)

	def set_info_label(self):
		midi_info = "MIDI device connected." if self.use_midi_device else "No MIDI device connected." 

		self.info_label["text"] = f"{midi_info}"

	### EVENTS/MIDI

	def key_handler(self, event):
		print(event.char, event.keysym, event.keycode)
		if self.allow_midi_input.get() != 1:
			try:
				ic = int(event.char)
				if ic > 0 and ic <= PP_SAVE_SLOT_COUNT:
					self.switch_patch((ic - 1) + (self.keyboard_trigger_bank * 8))
			except ValueError:
				if event.char == "-" and self.keyboard_trigger_bank > 0:
					self.keyboard_trigger_bank -= 1
					self.update_save_labels()
				elif event.char == "=" and self.keyboard_trigger_bank < (PP_SAVE_SLOT_COUNT / 8 - 1):
					self.keyboard_trigger_bank += 1
					self.update_save_labels()

	def handle_midi_events(self):
		if self.midi_port is not None:
			for msg in self.midi_port.iter_pending():
				if self.allow_midi_input.get() == 1:
					if msg.type == "note_on" and msg.note < PP_SAVE_SLOT_COUNT:
						self.switch_patch(msg.note)
		
		self.gui.after(10, self.handle_midi_events)

	def midi_rescan(self):
		try:
			self.midi_port = mido.open_input()
			self.use_midi_device = True
			self.allow_midi_button["state"] = "normal"
			self.live_mode_button["state"] = "normal"
		except OSError:
			self.gui.after(MIDI_RESCAN_INTERVAL_MS, self.midi_rescan)
			self.allow_midi_button["state"] = "disabled"
			self.live_mode_button["state"] = "disabled"
		self.set_info_label()

	### IMPORTANT STUFF

	def postprocess_fn(self, rgb, depth, confidence, intrinsic_matrix):
		pp_type = self.pp_save_slots[self.current_pp_save].pp_type
		if pp_type != self.last_pp_type:
			print("new pp_type into cache")
			self.pp_func_cache = self.find_pp_func_in_imported(pp_type).postprocess_raw

		self.last_pp_type = pp_type

		return self.pp_func_cache(
			rgb, depth, intrinsic_matrix,
			self.pp_save_slots[self.current_pp_save].value_dict, self.zoom_x, self.zoom_y, self.zoom_amount
		)

	def run(self):
		self.gui = tk.Tk()

		self.gui.title('LiVid')

		self.waiting_frame = ttk.Frame(self.gui, padding=50)
		tk.Label(
			self.waiting_frame,
			text="Waiting for connection to iPhone.",
			font=("System", 25, "bold")
		).pack()
		tk.Label(
			self.waiting_frame,
			text="Open the Record3D app on iPhone, then follow the instructions for USB Streaming Mode.",
			font=("System", 15)
		).pack()

		self.waiting_frame.grid()

		waiting = True

		while waiting:
			try:
				self.device.connect_to_device(dev_idx=0)
				self.device.start() # start device thread
				self.waiting_frame.grid_forget()
				waiting = False
			except:
				self.gui.update_idletasks()
				self.gui.update()

		# create control variables here (dumb)
		self.allow_midi_input = tk.IntVar()
		self.live_mode = tk.IntVar()
		self.pp_type_rolodex_value = tk.StringVar() # for the ttk.Combobox used to choose postprocessing type

		# create menu
		self.gui.option_add('*tearOff', tk.FALSE)

		self.menubar = tk.Menu(self.gui)
		self.gui.config(menu=self.menubar)
		
		self.file_menu = tk.Menu(self.menubar)

		self.file_menu.add_command(
			label='Open Patch Bank...',
			command=self.load_patch_bank_from_file,
			accelerator='Command+O',
		)
		self.file_menu.add_command(
			label='Load Single Patch from File...',
			command=self.load_single_patch_from_file,
			accelerator='Command+Shift+O',
		)
		self.file_menu.add_separator()
		self.file_menu.add_command(
			label='Export All Patches as Bank...',
			command=self.save_patch_bank_to_file,
			accelerator='Command+S',
		)
		self.file_menu.add_command(
			label='Export Current Patch...',
			command=self.save_single_patch_to_file,
			accelerator='Command+E',
		)

		self.scripts_menu = tk.Menu(self.menubar)

		self.scripts_menu.add_command(
			label='Load Post-Processor Function from External Script',
			command=self.import_new_pp_func,
			accelerator='Command+E',
		)
		self.scripts_menu.add_separator()
		self.scripts_menu.add_command(
			label='New Script from Template',
			command=self.create_new_script_from_template,
			accelerator='Command+Shift+N',
		)

		self.menubar.add_cascade(
			label="File",
			menu=self.file_menu
		)

		self.menubar.add_cascade(
			label="Scripts",
			menu=self.scripts_menu
		)

		frm = ttk.Frame(self.gui, padding=10)
		frm.pack(fill=tk.BOTH, expand=True)

		self.info_label = ttk.Label(frm, text=f"hello", font=("System", 11), foreground="grey")
		self.info_label.grid(column=0, row=2)

		ttk.Separator(frm, orient="horizontal").grid(column=0, row=3, sticky="ew", pady=10)

		###

		self.optfrm = ttk.Frame(frm)
		self.optfrm.grid(column=0, row=4, pady=10)

		pp_type_frm = ttk.Frame(self.optfrm)
		ttk.Label(pp_type_frm, text=f"Post-processor function:").pack(side=tk.LEFT, padx=3)
		self.pp_type_rolodex = ttk.OptionMenu(
			pp_type_frm, self.pp_type_rolodex_value, "PPDepth", command=self.change_pp_type_from_rolodex
		)
		self.pp_type_rolodex.pack(side=tk.LEFT, padx=0)

		pp_type_frm.grid(column=0, row=0, pady=5, columnspan=3)

		self.slider_frame = ttk.Frame(self.optfrm)
		self.slider_frame.grid(column=0, row=1, columnspan=3)

		ttk.Separator(self.slider_frame, orient="horizontal").grid(column=0, row=100, sticky="ew", pady=10, columnspan=3)

		ttk.Label(self.slider_frame, text="Zoom X position").grid(column=0, row=101, sticky="w")
		self.zoom_x_slider = ttk.Scale(self.slider_frame, from_=0, to=640, length=SCALE_W, value=320, command=lambda x: self.chg_var_self("zoom_x", x, self.zoom_x_label))
		self.zoom_x_slider.grid(column=1, row=101, padx=10)
		self.zoom_x_label = ttk.Label(self.slider_frame, text="", font=("Courier", 13))
		self.zoom_x_label.grid(column=2, row=101, sticky="e")

		ttk.Label(self.slider_frame, text="Zoom Y position").grid(column=0, row=102, sticky="w")
		self.zoom_y_slider = ttk.Scale(self.slider_frame, from_=0, to=480, length=SCALE_W, value=240, command=lambda x: self.chg_var_self("zoom_y", x, self.zoom_y_label))
		self.zoom_y_slider.grid(column=1, row=102, padx=10)
		self.zoom_y_label = ttk.Label(self.slider_frame, text="", font=("Courier", 13))
		self.zoom_y_label.grid(column=2, row=102, sticky="e")

		ttk.Label(self.slider_frame, text="Zoom amount").grid(column=0, row=103, sticky="w")
		self.zoom_amt_slider = ttk.Scale(self.slider_frame, from_=0.5, to=3, length=SCALE_W, value=1, command=lambda x: self.chg_var_self("zoom_amount", x, self.zoom_amt_label))
		self.zoom_amt_slider.grid(column=1, row=103, padx=10)
		self.zoom_amt_label = ttk.Label(self.slider_frame, text="", font=("Courier", 13))
		self.zoom_amt_label.grid(column=2, row=103, sticky="e")

		###

		self.live_mode_enabled_label = ttk.Label(
			frm, text="Live mode enabled. Exit live mode to edit patch.",
			font=("System", 15, "bold")
		)

		ttk.Separator(frm, orient="horizontal").grid(column=0, row=5, sticky="ew", pady=10)

		save_tab_control = ttk.Notebook(frm)
		save_tab_control.grid(column=0, row=6, sticky="ew")

		savefrm_kb = ttk.Frame(save_tab_control)
		save_tab_control.add(savefrm_kb, text="View 8 patches")

		self.save_labels_kb = [tk.Label(savefrm_kb, text=str(i), width=5, height=3, padx=10, pady=10) for i in range(1, 9)]
		for i, s in enumerate(self.save_labels_kb):
			s.grid(column=i, row=0, padx=10, pady=10)
		
		savefrm_kb.columnconfigure(tuple(range(8)), weight=1)

		savefrm_midi = ttk.Frame(save_tab_control)
		save_tab_control.add(savefrm_midi, text="Current patch")

		self.save_label_midi = tk.Label(savefrm_midi, text="", width=20, height=3, padx=10, pady=10)
		self.save_label_midi.pack(padx=10, pady=10)
		
		save_patch_btn_frm = ttk.Frame(frm)
		save_patch_btn_frm.grid(column=0, row=7)

		ttk.Button(
			save_patch_btn_frm, text="Save patch", command=self.fix_patch_changes
		).grid(column=0, row=0, padx=5)
		ttk.Button(
			save_patch_btn_frm, text="Revert patch changes", command=self.revert_patch_changes
		).grid(column=1, row=0, padx=5)

		"""
		save_file_btn_frm = ttk.Frame(frm)
		save_file_btn_frm.grid(column=0, row=8)

		ttk.Button(
			save_file_btn_frm, text="Save patch bank to file", command=self.save_patch_bank_to_file
		).grid(column=0, row=0, padx=5)
		ttk.Button(
			save_file_btn_frm, text="Load patch bank from file", command=self.load_patch_bank_from_file
		).grid(column=1, row=0, padx=5)
		"""

		self.allow_midi_button = ttk.Checkbutton(
			frm, text="Use MIDI input to switch patches", variable=self.allow_midi_input
		)
		self.allow_midi_button.grid(column=0, row=9, pady=5)

		ttk.Separator(frm, orient="horizontal").grid(column=0, row=10, sticky="ew", pady=10)

		self.live_mode_button = ttk.Button(
			frm, text="Enter live mode", command=self.update_live_mode
		)
		self.live_mode_button.grid(column=0, row=11, pady=15)

		ttk.Separator(frm, orient="horizontal").grid(column=0, row=12, sticky="ew", pady=10)

		ttk.Label(frm,
			text=f"LiVid v{LIVID_VERSION}. Copyright (c) {CURRENT_YEAR} Ishtar van Looy.",
			font=("System", 11),
			foreground="grey"
		).grid(column=0, row=13)

		self.set_info_label()

		self.midi_rescan()

		self.gui.bind("<Key>", self.key_handler)

		print(self.get_all_pp_func_names())

		self.switch_patch(0)

		self.gui.columnconfigure(tuple(range(1)), weight=1)
		self.gui.rowconfigure((tuple(range(1))), weight=1)

		#self.gui.minsize(100, 700)

		frm.columnconfigure((tuple(range(1))), weight=1)
		frm.rowconfigure(tuple(range(20)), weight=1)

		self.optfrm.columnconfigure((1), weight=1)

		self.update_pp_rolodex()

		#self.build_sliders()

		self.gui.after(50, lambda: self.device.display_stream_frame(self.gui))
		self.gui.after(50, self.handle_midi_events)
		self.gui.mainloop()

def open_file(filename):
	if sys.platform == "win32":
		os.startfile(filename)
	else:
		opener = "open" if sys.platform == "darwin" else "xdg-open"
		subprocess.call([opener, filename])

#########

"""
if __name__ == '__main__':
	import_postprocess_suite_from_file(os.environ["FILEPATH"])
"""

if __name__ == '__main__':
	dev = lidar.LidarDevice()
	app = LiVidApp(dev)

	app.run()

	"""if os.environ.get("GUIONLY") is not None:
		app = LiVidApp()
		dev = lidar.FakeLidarDevice()
		dev.start()
		app.run(dev)
	else:"""
