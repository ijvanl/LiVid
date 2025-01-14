import cv2, numpy as np, colorsys
from PIL import Image, ImageSequence, ImageFilter, ImageOps, ImageChops
from dotmap import DotMap
import sys, os, math
import postprocess as pp
import inspect

ASSUMED_FRAME_RATE = 60

def zoom_at(img, x, y, zoom):
	w, h = img.size
	zoom2 = zoom * 2
	img = img.crop(
		(x - w / zoom2, y - h / zoom2, 
		x + w / zoom2, y + h / zoom2)
	)
	return img.resize((w, h))

def color_field(h, s, v):
	return Image.new(
		"RGB", (640, 480),
		color=tuple([int(c * 255) for c in colorsys.hsv_to_rgb(h / 360, s, v)])
	)

def load_texture_from_abspath(fn):
	"""Highly inflexible - use with extreme caution. `load_local_texture(fn)` preferred."""
	with Image.open(fn) as im:
		return ImageSequence.all_frames(im, lambda x: x.resize((640, 480)).convert("RGB"))

def load_local_texture(fn):
	"""Given a file path local to the source .py or .vvpb file, load an image file for use with `PPTextureFunction`."""
	caller_path = inspect.stack()[1].filename
	cpath = os.path.dirname(os.path.abspath(caller_path))
	return load_texture_from_abspath(os.path.join(cpath, fn))


class PPTextureFunction(pp.PPFunction):
	"""Subclass of `PPFunction` with utilities for loading and using image files as textures, especially animated GIFs."""
	def __init__(self, use_streams=[pp.PP_DEPTH], textures=[]):
		super().__init__(use_streams=use_streams)
		self.textures = textures
	
	def get_texture_frame(self, tex_index, f=0):
		"""Get frame `f` of texture `tex_index`."""
		return self.textures[tex_index][f]

	def get_texture(self, tex_index, fps=60):
		"""Get nth frame of texture `tex_index` (given a frame rate of `fps`)."""
		tick = math.floor(self.tick() / (ASSUMED_FRAME_RATE / fps)) % len(self.textures[tex_index])
		return self.textures[tex_index][tick]