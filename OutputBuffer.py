import sys

class OutputBuffer:
	def __init__(self, autoStart = True):
		self.old = None
		if autoStart:
			self.start()

	def write(self, data):
		self.data += data

	def clear(self):
		self.data = ''

	def start(self):
		self.old = sys.stdout
		sys.stdout = self
		self.clear()

	def done(self):
		sys.stdout = self.old
		return self.data
