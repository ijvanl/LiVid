import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as mbox
from gui import aux
import os, sys

from model import LiVidModelController
from gui.patch_window import LiVidPatchWindowFrame
from gui.editor_window import LiVidEditorWindowFrame
from gui.mapping_window import LiVidMappingWindowFrame


class LiVidMainWindow(tk.Toplevel):
	def __init__(self, master, mc: LiVidModelController):
		super().__init__(master)
		self.mc = mc

		style = ttk.Style()
		style.configure("Tab.TLabel", font=("System", 10))
		style.map("Tab.TLabel",
			font=[("disabled", ("System", 10, "bold"))],
			foreground=[("disabled", "systemLabelColor")]
		)

		self.current_tab = "Editor"
		self.tabs = {
			"Patch": LiVidPatchWindowFrame(self, mc),
			"Editor": LiVidEditorWindowFrame(self, mc),
			"Mappings": LiVidMappingWindowFrame(self, mc),
		}
		self.tab_buttons = {}
		
		self.build_gui()
		self.geometry('1200x800')

		self.on_patch_selected(None)


	def build_gui(self):
		self.title('LiVid')

		self.tab_bar = ttk.Frame(self)
		self.tab_bar.grid(column=0, row=0, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W)

		for name in self.tabs.keys():
			self.create_tab_button(name)
	
		ttk.Separator(self.tab_bar).grid(column=0, row=1, columnspan=10, sticky=tk.E + tk.W)
		self.tab_bar.columnconfigure(len(self.tab_buttons), weight=1)

		self.play_button = aux.RoledButton(self.tab_bar, role="play", command=self.play)
		self.play_button.grid(column=len(self.tab_buttons) + 1, row=0, padx=5)

		self.patch_listbox = aux.ScrollListbox(self)
		self.patch_listbox.set_update_callback(self.on_patch_selected)
		self.patch_listbox.grid(column=0, row=1, sticky=tk.N + tk.S + tk.E + tk.W)

		patch_list_bar = ttk.Frame(self)
		patch_list_bar.grid(column=0, row=2, sticky=tk.E + tk.W, ipady=2)

		self.add_patch_button = aux.RoledButton(patch_list_bar, role="add", command=self.add_patch)
		self.add_patch_button.grid(column=2, row=0, padx=5)

		self.remove_patch_button = aux.RoledButton(patch_list_bar, role="remove", command=self.remove_current_patch)
		self.remove_patch_button.grid(column=1, row=0, padx=(5, 0))

		patch_list_bar.columnconfigure(0, weight=1)

		for tab in self.tabs.values():
			tab.grid(column=1, row=1, rowspan=2, sticky=tk.N + tk.S + tk.E + tk.W)
			tab.grid_remove()

		self.columnconfigure(1, weight=1)
		self.rowconfigure(1, weight=1)

	def play(self):
		try:
			self.mc.backend.start_displaying()
		except RuntimeError:
			mbox.showwarning(
				None, "No device connected!",
				detail="Try connecting a compatible device, checking your connection, or adjusting your project settings."
			)
	
	def backend_checkup(self):
		self.mc.backend.device.is_presenting

	def on_patch_selected(self, event):
		for tab in self.tabs.values():
			tab.before_patch_selected(event)
		
		selection = self.patch_listbox.listbox.selection()
		self.mc.current_patch_name = selection[0] if (selection is not None) and len(selection) == 1 else None

		for tab in self.tabs.values():
			tab.after_patch_selected(event)

	def add_patch(self):
		print("add patch")
		patch_name = f"Patch #{len(self.mc.patches)}"
		self.mc.add_patch(patch_name)
		self.update_patch_listbox(patch_name)

	def remove_current_patch(self):
		print("remove current patch")
		if self.mc.current_patch_name is not None:
			self.mc.remove_patch(self.mc.current_patch_name)
			self.mc.current_patch_name = None
			self.update_patch_listbox(())

	def update_patch_listbox(self, new_index=None):
		if new_index == None:
			new_index = self.mc.current_patch_name if self.mc.current_patch_name is not None else self.patch_listbox.listbox.selection()
		
		self.patch_listbox.clear()
		for k in self.mc.patches.keys():
			self.patch_listbox.insert("end", k, text=k)
		
		self.patch_listbox.listbox.selection_set(new_index)

	def create_tab_button(self, name):
		self.tab_buttons[name] = ttk.Button(
			self.tab_bar, text=f"{name}  ",
			command=lambda: self.switch_tabs(name),
			style="Tab.TLabel"
		)
		self.tab_buttons[name].grid(column=len(self.tab_buttons) - 1, row=0, padx=(5, 0), pady=5)
	
	def switch_tabs(self, tab):
		self.tabs[self.current_tab].grid_remove()
		self.tabs[tab].grid()
		self.tabs[tab].on_tab_open()
		self.tabs[tab].update()
		
		for button in self.tab_buttons.values(): button.config(state="normal")
		
		self.tab_buttons[tab].config(state="disabled")
		
		self.current_tab = tab
		self.update_idletasks()


if __name__ == "__main__":
	root = tk.Tk()
	model = LiVidModelController()
	t = LiVidMainWindow(root, model)
	#t.pack(expand=True, fill=tk.BOTH)
	root.mainloop()