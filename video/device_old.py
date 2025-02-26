import numpy as np
from record3d import Record3DStream
import cv2
from threading import Thread, Event

TIME_DELAY_MS = 10

FRAME_TIMEOUT = 0.5

class LidarDevice(Thread):
	def __init__(self, postprocess_function=None):
		Thread.__init__(self)

		self.device = None
		self.arriveEvent = Event()
		self.displayEvent = Event()
		self.session = None
		self.DEVICE_TYPE__TRUEDEPTH = 0
		self.DEVICE_TYPE__LIDAR = 1
		self.postprocess_function = postprocess_function
		self.image = None
		self.continue_running = True

	def connect_to_device(self, dev_idx):
		print('Searching for devices')
		devs = Record3DStream.get_connected_devices()
		print('{} device(s) found'.format(len(devs)))
		for dev in devs:
			print('\tID: {}\n\tUDID: {}\n'.format(dev.product_id, dev.udid))

		if len(devs) <= dev_idx:
			raise RuntimeError('Cannot connect to device #{}, try different index.'.format(dev_idx))

		self.device = devs[dev_idx]

	def start_session(self):
		if self.device is not None:
			self.session = Record3DStream()
			self.session.on_new_frame = self.on_new_frame
			self.session.on_stream_stopped = self.on_stream_stopped
			self.session.connect(self.device) # Initiate connection and start capturing

	def on_new_frame(self):
		"""This method is called from non-main thread, therefore cannot be used for presenting UI."""
		self.arriveEvent.set()  # Notify the main thread to stop waiting and process new frame.

	def on_stream_stopped(self):
		print('Stream stopped')
		self.continue_running = False
		cv2.destroyAllWindows()

	def get_intrinsic_mat_from_coeffs(self, coeffs):
		return np.array([[coeffs.fx,         0, coeffs.tx],
						[        0, coeffs.fy, coeffs.ty],
						[        0,         0,         1]])

	# call from mainloop
	def display_stream_frame(self, gui):
		no_timeout = self.displayEvent.wait(timeout=FRAME_TIMEOUT)  # Wait for new frame to arrive
		if no_timeout:
			cv2.imshow('Stream', self.image)
			self.displayEvent.clear()
			gui.after(TIME_DELAY_MS, lambda: self.display_stream_frame(gui))
		else:
			print("timeout on display_stream_frame")
			self.on_stream_stopped()

	def process_stream_frame(self):
		no_timeout = self.arriveEvent.wait(timeout=FRAME_TIMEOUT) # Wait for new frame to arrive

		if no_timeout:
			# Copy the newly arrived RGBD frame
			depth = self.session.get_depth_frame()
			rgb = self.session.get_rgb_frame()
			confidence = None #self.session.get_confidence_frame()
			intrinsic_mat = None #self.get_intrinsic_mat_from_coeffs(self.session.get_intrinsic_mat())
			#camera_pose = self.session.get_camera_pose()  # Quaternion + world position (accessible via camera_pose.[qx|qy|qz|qw|tx|ty|tz])

			#print(intrinsic_mat)

			# You can now e.g. create point cloud by projecting the depth map using the intrinsic matrix.

			# Postprocess it
			stream = self.postprocess_function(rgb, depth, confidence, intrinsic_mat)

			# Show postprocessed stream
			stream_bgr = cv2.cvtColor(stream, cv2.COLOR_RGB2BGR)
			self.image = stream_bgr

			# Show the RGBD Stream
			#cv2.imshow('RGB', rgb)
			#cv2.imshow('Depth', depth * 0.2)

			#if confidence.shape[0] > 0 and confidence.shape[1] > 0:
				#cv2.imshow('Confidence', confidence * 100)

			#cv2.waitKey(1)

			self.arriveEvent.clear()
			self.displayEvent.set()
		else:
			self.on_stream_stopped()

	def run(self):
		while self.continue_running:
			#print("run!")
			self.process_stream_frame()