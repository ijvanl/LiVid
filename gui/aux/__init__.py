import tkinter as tk
import tkinter.ttk as ttk
import sys

class ScrollListbox(ttk.Frame):
	def __init__(self, master):
		super().__init__(master)
		self.yScroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
		self.yScroll.grid(row=0, column=1, sticky=tk.N + tk.S)

		self.listbox = ttk.Treeview(self,
			yscrollcommand=self.yScroll.set,
			show="tree"
		)
		self.listbox.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
		self.yScroll['command'] = self.listbox.yview

		sep = ttk.Separator(self, orient="horizontal")
		sep.grid(row=1, column=0, columnspan=2, sticky=tk.E + tk.W)

		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

	def set_update_callback(self, cb):
		self.listbox.bind("<<TreeviewSelect>>", cb)

	def insert(self, index, id, **kw):
		self.listbox.insert("", index, id, **kw)

	def clear(self):
		self.listbox.delete(*self.listbox.get_children())


class EntryWithPlaceholder(tk.Entry):
	def __init__(self, master, *args, textvariable=None, plvariable=None, enabled=None, plcolor='grey', **kwargs):
		super().__init__(master, *args, textvariable=textvariable, **kwargs)

		self.kept_textvariable = textvariable
		self.placeholder = plvariable
		self.placeholder_color = plcolor
		self.default_fg_color = self['fg']

		self.enabled_variable = enabled

		self.bind("<FocusIn>", self.foc_in)
		self.bind("<FocusOut>", self.foc_out)

		self.enabled_variable.trace_add(
			"write", lambda *_: self.set_enabled()
		)

		self.foc_out()

	def set_enabled(self, *_):
		self["state"] = "normal" if self.enabled_variable.get() else "disabled"

	def put_placeholder(self):
		self["textvariable"] = self.placeholder
		self['fg'] = self.placeholder_color

	def foc_in(self, *_):
		if self['fg'] == self.placeholder_color:
			self.kept_textvariable.set("")
			self["textvariable"] = self.kept_textvariable
			self['fg'] = self.default_fg_color

	def foc_out(self, *_):
		if not self.get():
			self.put_placeholder()


ROLE_SYMBOLS = {
	"add": "+",
	"remove": "-",
	"previous": "<",
	"next": ">",
	"run": "Run",
	"preview": "Preview",
	"play": "Play",
	"pause": "Pause",
	"stop": "Stop",
	"then": "=>",
	"equals": "=",
}
if sys.platform == "darwin":
	ROLE_SYMBOLS = {
		"add": u'\U0010017c',
		"remove": u'\U0010017d',
		"previous": u'\U00100189',
		"next": u'\U0010018a',
		"run": u'\U00100284',
		"preview": u'\U00100283',
		"play": u'\U00100284',
		"pause": u'\U00100286',
		"stop": u'\U001006f7',
		"then": u'\U00100135',
		"equals": u'\U00100180',
	}

class RoledButton(ttk.Button):
	def __init__(self, *args, role="add", **kwargs):
		#super().__init__(*args, text=ROLE_SYMBOLS[role], width=2, style="HelpButton", **kwargs)
		super().__init__(*args, text=ROLE_SYMBOLS[role], width=2, **kwargs)

	def __setattr__(self, name, value):
		if name == "role": self["text"] = ROLE_SYMBOLS[value]
		else: super().__setattr__(name, value)


class CustomListbox(ttk.Frame):
	def __init__(self, master, create_callback=None):
		super().__init__(master)
		self.model = {}
		self.current_elements = {}
		self.create_callback = create_callback
		self.item_id_counter = 0

		self.build_gui()
	
	def build_gui(self):
		self.list_frame = ttk.Frame(self, style="TFrame", width=100)
		#self.list_frame = ttk.Frame(self, style="Treeview")
		self.list_frame.grid(column=0, row=0, sticky=tk.N + tk.S + tk.E + tk.W)
		
		self.list_frame.columnconfigure(0, weight=1)

		ttk.Separator(self).grid(column=0, row=1, sticky=tk.E + tk.W)
		
		self.bar_frame = ttk.Frame(self, padding=(5, 0))
		self.bar_frame.grid(column=0, row=2, sticky=tk.E + tk.W, ipady=2)

		#self.remove_button = RoledButton(self.bar_frame, role="remove")
		#self.remove_button.grid(column=100, row=0, padx=(5, 0))

		self.add_button = RoledButton(self.bar_frame, role="add", command=self.new_element)
		self.add_button.grid(column=101, row=0, padx=(5, 0))

		self.bar_frame.columnconfigure(99, weight=1)

		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
	
	def get_new_id(self):
		self.item_id_counter += 1
		return self.item_id_counter

	def get_list(self):
		return list(self.model.values())

	def replace_from_current_model(self):
		self.current_elements.clear()

		for (iid, v) in self.model.items():
			element_frame = ttk.Frame(self.list_frame, style="TFrame")

			(_, element) = self.create_callback(element_frame, from_model=v)
			element.grid(column=0, row=0, ipadx=5, pady=2, sticky=tk.E + tk.W)

			remove_button = RoledButton(element_frame, role="remove", command=lambda i=iid: self.remove_element(i))
			remove_button.grid(column=1, row=0, padx=5, pady=2, sticky=tk.E + tk.W)

			element_frame.columnconfigure(0, weight=1)

			self.current_elements[iid] = element_frame

		self.update_elements()


	def replace_from_new_model(self, new_model):
		self.model.clear()
		for s in new_model:
			self.model[self.get_new_id()] = s

		self.replace_from_current_model()

	def new_element(self):
		iid = self.get_new_id()

		element_frame = ttk.Frame(self.list_frame, style="TFrame")

		(model_item, element) = self.create_callback(element_frame, from_model=None)
		element.grid(column=0, row=0, ipadx=5, pady=2, sticky=tk.E + tk.W)

		remove_button = RoledButton(element_frame, role="remove", command=lambda i=iid: self.remove_element(i))
		remove_button.grid(column=1, row=0, padx=5, pady=2, sticky=tk.E + tk.W)

		#ttk.Separator(element_frame).grid(column=0, row=1, columnspan=2, sticky=tk.E + tk.W)

		element_frame.columnconfigure(0, weight=1)

		self.model[iid] = model_item
		self.current_elements[iid] = element_frame
		self.update_elements()
	
	def remove_element(self, iid):
		del self.current_elements[iid]
		del self.model[iid]
		self.update_elements()
	
	def update_elements(self):
		for child in self.list_frame.winfo_children():
			child.grid_forget()
			#child.update_idletasks()

		for (i, element) in enumerate(self.current_elements.values()):
			element.grid(column=0, row=i, sticky=tk.E + tk.W)
			#child.update_idletasks()
		
		if len(self.list_frame.grid_slaves()) == 0:
			ttk.Frame(self.list_frame, width=10, height=10, relief="raised").grid(column=0, row=0)

		self.update_idletasks()


if __name__ == "__main__":
	root = tk.Tk()
	p = tk.StringVar(root, "placeholder!")
	t = tk.StringVar(root, "")
	e = EntryWithPlaceholder(root, textvariable=t, plvariable=p)
	l = tk.Label(root, textvariable=t)
	e.grid(row=0, column=0)
	l.grid(row=1, column=0)
	tk.Entry(root, textvariable=p).grid(row=2, column=0)
	tk.Button(root, text="Okay!", command=lambda *_: print("Hi!")).grid(row=3, column=0)
	root.mainloop()