import numpy as np
from record3d import Record3DStream
import cv2
from threading import Event

from device import *

class VideoRenderer:
	def __init__(self, model):
		self.model = model
		self.device = None
	
	def start_video(self):
		