import cv2, numpy as np, colorsys
from PIL import Image, ImageSequence, ImageFilter, ImageOps, ImageChops
from dotmap import DotMap
import sys, os

PP_RGB = "rgb"
PP_DEPTH = "depth"

_PP_LAST_IMAGE = None
_PP_LAST_IMAGE_SET = False

class PatchClass:
	def __init__(self, use_streams=[PP_DEPTH]):
		self._pp_use_streams = use_streams
		self._pp_rgb_frame = None
		self._pp_rgb_frame_zoomed = None
		self._pp_depth_frame = None
		self._pp_intrinsic_matrix = None
		self._pp_zoom = None
		self._pp_frame_tick = 0
	
	def values(self):
		return {}
	
	def postprocess(self, values):
		return self.depth(1.0)

	def postprocess_raw(self, rgb, depth, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		global _PP_LAST_IMAGE, _PP_LAST_IMAGE_SET

		self._pp_frame_tick += 1

		self._pp_zoom = (zoom_x, zoom_y, zoom_amount)
		self._pp_intrinsic_matrix = intrinsic_matrix

		if PP_RGB in self._pp_use_streams:
			screen = np.swapaxes(rgb, 0, 1)
			self._pp_rgb_frame = Image.fromarray(screen).convert("RGB").resize((640, 480), resample=2)
			self._pp_rgb_frame = self._pp_rgb_frame.transpose(Image.FLIP_LEFT_RIGHT)
			self._pp_rgb_frame_zoomed = _zoom_at(self._pp_rgb_frame, zoom_x, zoom_y, zoom_amount)
		
		if PP_DEPTH in self._pp_use_streams:
			self._pp_depth_frame = np.swapaxes(depth, 0, 1)
		
		image = self.postprocess(DotMap(pp))

		if _PP_LAST_IMAGE_SET == False:
			_PP_LAST_IMAGE = image
		_PP_LAST_IMAGE_SET = False
		return np.array(image)

	def tick(self):
		return self._pp_frame_tick

	def rgb(self, zoom=True):
		return (self._pp_rgb_frame_zoomed if zoom else self._pp_rgb_frame)

	def depth(self, contrast: float, zoom=True):
		if not PP_DEPTH in self._pp_use_streams: return None
		screen = np.clip(self._pp_depth_frame * contrast, 0.0, 1.0)
		screen_img = Image.fromarray(screen * 255).convert("RGB").resize((640, 480), resample=2)
		screen_img = screen_img.transpose(Image.FLIP_LEFT_RIGHT)
		return (_zoom_at(screen_img, *self._pp_zoom) if zoom else screen_img)
	
	def depth_bound(self, lower: float, upper: float, contrast: float, zoom=True):
		screen = self._pp_depth_frame

		screen = np.clip((1.0 - abs((screen - lower) / (upper - lower))) * contrast, 0.0, 1.0)

		screen_img = Image.fromarray(screen * 255).convert("RGB").resize((640, 480), resample=2)

		screen_img = screen_img.transpose(Image.FLIP_LEFT_RIGHT)
		return (_zoom_at(screen_img, *self._pp_zoom) if zoom else screen_img)
	
	def last_image(self, set=None):
		global _PP_LAST_IMAGE, _PP_LAST_IMAGE_SET
		if set is None:
			if _PP_LAST_IMAGE is not None:
				return _PP_LAST_IMAGE
			else:
				return Image.fromarray(np.zeros((640, 480))).convert("RGB")
		else:
			last = _PP_LAST_IMAGE
			_PP_LAST_IMAGE = set
			_PP_LAST_IMAGE_SET = True
			return last

def _zoom_at(img, x, y, zoom):
	w, h = img.size
	zoom2 = zoom * 2
	img = img.crop(
		(x - w / zoom2, y - h / zoom2, 
		x + w / zoom2, y + h / zoom2)
	)
	return img.resize((w, h))

def patch(cls):
	"""Class decorator for patch postprocessor classes"""
	import inspect
	inspect.stack()[1][0].f_globals["__PP_CLASS__"] = cls()
	return cls
