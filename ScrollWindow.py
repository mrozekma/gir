import curses

from WindowWrapper import WindowWrapper

class ScrollWindow:
	def __init__(self, data, drawFn, lenFn, targetRow, targetCol, targetWidth, targetHeight, selectable = False):
		self.data = data
		self.drawFn = drawFn
		self.targetRow = targetRow
		self.targetCol = targetCol
		self.targetWidth = targetWidth
		self.targetHeight = targetHeight
		self.selection = 0 if selectable else None

		self.height = len(data)
		self.width = max(lenFn(row) for row in data)
		if selectable:
			self.width += 2
		if self.height < self.targetHeight:
			self.targetHeight = self.height
		if self.width < self.targetWidth:
			self.targetWidth = self.width

		# I can't figure out why height + 1 is necessary here; the pad is the right height without it, but writing the last line causes an ERR
		self.win = WindowWrapper(curses.newpad(self.height + 1, self.width))
		self.curRow = 0
		self.curCol = 0
		self.rendered = -1 # All rows through this one have been drawn to self.win

	def getFirstData(self):
		return self.data[self.curRow]

	def getLastData(self):
		return self.data[self.curRow + self.targetHeight - 1]

	def getSelectedData(self):
		if self.selection is None:
			raise ValueError("Can't get selected data on an unselectable window")
		return self.data[self.selection]

	def draw(self):
		first, last = self.curRow, self.curRow + self.targetHeight - 1
		if self.rendered < last:
			self.growRender(last)
		self.win.refresh(self.curRow, self.curCol, self.targetRow, self.targetCol, self.targetRow + self.targetHeight - 1, self.targetCol + self.targetWidth - 1)

	def growRender(self, to):
		"""Draw all undrawn rows through 'to' to 'self.win'"""
		for i in range(self.rendered + 1, to + 1):
			self.forceRender(i)
		self.rendered = to

	def forceRender(self, i):
		"""Draw row 'i' to 'self.win', even if already drawn. Used by growRender() but also directly if 'data[i]' has changed"""
		self.drawFn(self.win, i, self.data[i])

	# When talking about "scrolling" vertically in a selectable window, it's actually moving the selection
	# The window will scroll if the selection moves off the edge
	# The methods take a 'literally' flag if you actually want to do scrolling, not just moving the selection

	def canScrollUp(self, literally = False):
		if self.selection is None or literally:
			return self.curRow > 0
		else:
			return self.selection > 0

	def scrollUp(self, amt = 1, literally = False):
		if self.selection is None or literally: # Normal windows
			if self.curRow > 0:
				self.curRow = max(0, self.curRow - amt)
			if self.selection is not None and self.selection > self.curRow + self.targetHeight - 1:
				self.selection = self.curRow + self.targetHeight - 1
		elif self.selection > 0: # Selectable windows
			self.selection = max(0, self.selection - amt)
			if self.selection < self.curRow:
				self.curRow = self.selection

	def canScrollDown(self, literally = False):
		if self.selection is None or literally:
			return self.curRow + self.targetHeight < self.height
		else:
			return self.selection < self.height

	def scrollDown(self, amt = 1, literally = False):
		if self.selection is None or literally: # Normal windows
			if self.curRow + self.targetHeight < self.height:
				self.curRow = min(self.height - self.targetHeight, self.curRow + amt)
			if self.selection is not None and self.selection < self.curRow:
				self.selection = self.curRow
		elif self.selection + 1 < self.height: # Selectable windows
			self.selection = min(self.height - 1, self.selection + amt)
			if self.selection > self.curRow + self.targetHeight - 1:
				self.curRow = self.selection - self.targetHeight + 1

	def canScrollLeft(self):
		return self.curCol > 0

	def scrollLeft(self, amt = 1):
		if self.curCol > 0:
			self.curCol = max(0, self.curCol - amt)

	def canScrollRight(self):
		return self.curCol + self.targetWidth < self.width

	def scrollRight(self, amt = 1):
		if self.curCol + self.targetWidth < self.width:
			self.curCol = min(self.width - self.targetWidth, self.curCol + amt)
