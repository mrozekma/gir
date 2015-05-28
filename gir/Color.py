import curses

# black, blue, cyan, green, magenta, red, white, yellow

class Color:
	def __init__(self):
		self.m = {}
		self.ctr = 1

	# Names are of the form fg[_bg][_attr]
	def __getattr__(self, name):
		if name in self.m:
			return self.m[name]

		flags = 0
		while '_' in name:
			if name.endswith('_bold') or name.endswith('_bd'):
				flags |= curses.A_BOLD
			elif name.endswith('_reverse') or name.endswith('_rv'):
				flags |= curses.A_REVERSE
			elif name.endswith('_underline') or name.endswith('_ul'):
				flags |= curses.A_UNDERLINE
			else:
				break
			name = name[:name.rfind('_')]

		if flags: # Recursively get the no-attribute version so it will be the one cached with an index
			return getattr(self, name) | flags
		else: # This request has no attributes; assign it an index
			if name in ('grey', 'gray'): # Special case
				return self.black_black_bold
			parts = name.split('_', 1)
			fg = Color.resolveName(parts[0])
			bg = Color.resolveName(parts[1] if len(parts) > 1 else 'black') # Supposedly -1 means terminal default, but it doesn't work for me
			if self.ctr > curses.COLOR_PAIRS:
				raise RuntimeError("Can't allocate more than %d colors" % curses.COLOR_PAIRS)
			curses.init_pair(self.ctr, fg, bg)
			rtn = curses.color_pair(self.ctr)
			self.m[name] = rtn
			self.ctr += 1
			return rtn

	def normal(self, c = 0): return c | curses.A_NORMAL
	def nm(self, c = 0): return c | curses.A_NORMAL
	def bold(self, c = 0): return c | curses.A_BOLD
	def bd(self, c = 0): return c | curses.A_BOLD
	def reverse(self, c = 0): return c | curses.A_REVERSE
	def rv(self, c = 0): return c | curses.A_REVERSE
	def underline(self, c = 0): return c | curses.A_UNDERLINE
	def ul(self, c = 0): return c | curses.A_UNDERLINE

	@staticmethod
	def resolveName(name):
		cname = "COLOR_%s" % name.upper()
		if not hasattr(curses, cname):
			raise ValueError("Unrecognized curses color name: %s" % name)
		return getattr(curses, cname)

color = Color()
