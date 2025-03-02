import numpy as np
from record3d import Record3DStream
import cv2
from multiprocessing import Process, Event
import logging

TIME_DELAY_MS = 10

FRAME_TIMEOUT = 0.5

class BackendDevice(Process):
	"""
	Brings in data and sends it to postprocessor.
	States:
	- (device=None, presenting_session=None):	scans for connected devices
	- (device=<any>, presenting_session=None):	maintains connection (pulls and discards frames from stack etc)
	- (device=<any>, presenting_session=<any>):	pulls and processes frames and sends to display
	- (device=None, presenting_session=<any>):	sets presenting_session = None; raises error
	"""
	def __init__(self):
		super().__init__()
		#Thread.__init__(self)
		self.postprocess_function = None
		#self.connected_to_device_flag = False
		self.device = None
		self.presenting_session = None
		self.session_end_flag = None
		self.session_requires_end = False
	
	def set_postprocess_function(self, fn):
		self.postprocess_function = fn
	
	def start_session(self):
		pass

	def end_session(self, flag=None):
		self.session_end_flag = flag
		self.session_requires_end = True
	
	def end_session_from_thread(self):
		pass

	def scan_for_device(self):
		pass

	def process_data_frame(self):
		pass

	def standby(self):
		pass

	def is_presenting(self):
		return (False, self.session_end_flag)

	def main_loop_step(self):
		if self.device is None:
			if self.presenting_session is not None:
				self.presenting_session = None
				raise RuntimeError("cannot present without device")
			else:
				self.scan_for_device()
		elif self.presenting_session is not None:
			if self.session_requires_end:
				self.session_requires_end = False
				self.end_session_from_thread()
			else:
				self.process_data_frame()
		else:
			self.standby()
	
	def run(self):
		while True:
			self.main_loop_step()


class LidarBackendDevice(BackendDevice):
	def __init__(self, use_device_id=0, logger=None):
		super().__init__()
		
		self.use_device_id = use_device_id

		#self.data_arrive_event = Event()
		self.display_ready_event = Event()
		
		self.DEVICE_TYPE__TRUEDEPTH = 0
		self.DEVICE_TYPE__LIDAR = 1
		
		self.image = None

		self.logger = logger

	def scan_for_device(self):
		self.logger.info("scanning for devices")
		devices = Record3DStream.get_connected_devices()
		self.logger.info("{} device(s) found".format(len(devices)))
		for dev in devices:
			self.logger.info("\tID: {}\n\tUDID: {}\n".format(dev.product_id, dev.udid))

		if len(devices) > self.use_device_id:
			self.device = devices[self.use_device_id]
		#else: raise RuntimeError("cannot connect to device #{}".format(self.use_device_id))
	
	def start_session(self):
		if self.device is not None and self.presenting_session is None:
			self.logger.info("starting session")
			#self.scan_for_device() # reset device
			self.presenting_session = Record3DStream()
			self.presenting_session.on_new_frame = self.process_data_frame
			self.presenting_session.on_stream_stopped = self.on_stream_stopped
			self.logger.info("connecting")
			self.presenting_session.connect(self.device) # Initiate connection and start capturing
			#self.session_end_flag = None

	def end_session_from_thread(self):
		if self.device is not None and self.presenting_session is not None:
			self.presenting_session.disconnect()
			self.logger.info("disconnected")
			del self.presenting_session
			self.presenting_session = None

	def on_stream_stopped(self):
		self.logger.info("stream stopped")
		self.end_session(flag="stopped")
	
	def is_presenting(self):
		if self.presenting_session is not None: return (True, None)
		else: return (False, self.session_end_flag)

	# called from device thread (ooh!)
	def process_data_frame(self):
		depth = self.presenting_session.get_depth_frame()
		rgb = self.presenting_session.get_rgb_frame()
		#confidence = self.presenting_session.get_confidence_frame()

		stream = self.postprocess_function(rgb, depth, None, None)

		#stream_bgr = cv2.cvtColor(stream, cv2.COLOR_RGB2BGR)
		#self.image = stream_bgr
		self.image = stream

		self.display_ready_event.set() # frame is ready to display
	
	# call from main thread — blocks until ready
	def get_image(self):
		success = self.display_ready_event.wait(timeout=FRAME_TIMEOUT)
		if success:
			self.display_ready_event.clear()
			return self.image
		elif self.session_end_flag is not None: # if already ended, don't bother
			return None
		else:
			self.end_session(flag="timeout while processing")
			return None