import os, sys
import video

import logging

tf = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.py.txt"), "r")
TEMPLATE_STRING = tf.read()
tf.close()

class Patch:
	def __init__(self, mc, name, text, mappings):
		self.mc = mc
		self.name = name
		self.text = text
		self.mappings = mappings
		self.patch_struct = None
		self.error = None

		self.update_code()

	def update_code(self):
		code = compile(self.text, self.name, "exec")
		file_globals = dict(self.mc.script_world, **{ "__file__": self.name })
		exec(code, file_globals)
		self.patch_struct = file_globals["__PP_CLASS__"]

	def values(self):
		if self.patch_struct is None:
			self.update_code()
		if self.error is not None:
			return None
		return self.patch_struct.values()

class LiVidModelController:
	def __init__(self, backend: video.VideoRenderer):
		self.logger = logging.getLogger(__name__)

		self.backend = backend
		self.backend.set_mc(self)
		self.backend.start()
		self.script_world = {}
		self.patch_triggers = {}
		self.patches = {}
		self.current_patch_name = None
		self.tk = None
	
	def add_patch(self, name):
		self.patches[name] = Patch(self, name, str(TEMPLATE_STRING), [])
	
	def get_current_patch(self):
		if self.current_patch_name is not None:
			return self.patches[self.current_patch_name]
		else: return None

	def remove_patch(self, name):
		self.patches.pop(name)