import numpy as np
from record3d import Record3DStream
import cv2
from threading import Event

from .device import *

class VideoRenderer:
	"""
	Handles all "live" aspects of patch (rendering, MIDI switching, etc)
	"""
	def __init__(self):
		self.mc = None
		self.device = LidarBackendDevice()
		self.device.set_postprocess_function(self.postprocess_function)
		self.last_patch_name = None
		self.patch_struct_cache = None
		self.device.start()
	
	def postprocess_function(self, rgb, depth, confidence, intrinsic_matrix):
		patch_name = self.mc.current_patch_name

		if patch_name != self.last_patch_name:
			print("new patch struct into cache")
			self.patch_struct_cache = self.mc.get_current_patch().patch_struct

		self.last_patch_name = patch_name

		return self.patch_struct_cache.postprocess_raw(
			rgb, depth, intrinsic_matrix,
			self.patch_struct_cache.values(), 320, 240, 1 #self.zoom_x, self.zoom_y, self.zoom_amount
		)
	
	def start_displaying(self):
		if self.device.device is not None:
			self.device.start_session()
			self.display_step() # called from main thread, for gui reasons
		else:
			raise RuntimeError("device not connected")

	def display_step(self):
		image = self.device.get_image()
		if image is not None:
			cv2.imshow('Stream', image)
			self.mc.tk.after(TIME_DELAY_MS, self.display_step) # reschedule only if image is not none