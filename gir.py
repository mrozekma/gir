from collections import OrderedDict
import curses
import git
import os
import shutil
import sys
import tempfile

from Color import color
from OutputBuffer import OutputBuffer
from ScrollWindow import ScrollWindow
from WindowWrapper import WindowWrapper

MAX_COMMITS = 20
MAX_DETAIL_LENGTH = 500

def title(str):
	sys.__stdout__.write("\033]0;%s\007" % str)

def main(win, filename):
	title('gir')
	win = WindowWrapper(win)
	curses.curs_set(0) # Hide cursor
	height, width = win.getmaxyx()

	commands = OrderedDict()
	commands['pick'] = {'color': color.white, 'key': ord('p')}
	commands['reword'] = {'color': color.black_yellow, 'key': ord('r')}
	commands['edit'] = {'color': color.black_green, 'key': ord('e')}
	commands['squash'] = {'color': color.white_blue, 'key': ord('s')}
	commands['fixup'] = {'color': color.white_magenta, 'key': ord('f')}
	# commands['exec'] = {'color': color.white_red, 'key': ord('x')}, # Exec isn't on a commit line, it'll have to be handled separately (also don't have a way to prompt for the command yet)
	commands['del'] = {'color': color.grey, 'key': curses.KEY_DC}

	repo = git.Repo(os.path.dirname(os.path.dirname(filename)))

	with open(os.path.join(repo.git_dir, 'rebase-merge', 'onto')) as f:
		onto = f.read().strip()
	onto = repo.commit(onto)

	# Parse the file; don't load commit objects yet
	commits = []
	with open(filename) as f:
		for line in f:
			if line.strip() == '' or line[0] == '#':
				continue
			parts = line.split(' ', 2)
			if len(parts) != 3:
				raise RuntimeError("Malformed line: %s" % line)
			command, shahash, _ = parts
			if command not in commands:
				raise RuntimeError("Malformed line (bad command): %s" % line)
			commits.append((command, shahash))

	# Load all the commit objects at once and update 'commits'
	# I'm not positive this will get them all, so if necessary load missing objects individually
	objects = {commit.hexsha[:7]: commit for commit in repo.iter_commits(commits[-1][1], max_count = len(commits) + 1)}
	commits = list((command, objects[shahash] if shahash in objects else repo.commit(shahash)) for command, shahash in commits)

	def commandDraw(win, row, data):
		command, commit = data
		clr = commands[command]['color']
		win.fillline(row, clr)
		win.addstr(row, 2, commit.hexsha[:7], clr)
		win.addstr(row, 11, command, color.bold(clr))
		win.addstr(row, 18, commit.summary, clr)
	def commandLen(data):
		command, commit = data
		return 18 + len(commit.summary)
	def detailDraw(win, row, data):
		# This is formatted to mimic 'tig' output
		attr = \
			color.white_red_bold if row > MAX_DETAIL_LENGTH else \
			color.cyan if data.startswith('Author:') else \
			color.magenta if data.startswith('Commit:') else \
			color.yellow if data.startswith('AuthorDate:') or data.startswith('CommitDate:') or data.startswith('Date:') else \
			color.yellow_bold if data.startswith('diff --git') else \
			color.red_bold if data.startswith('-') else \
			color.green_bold if data.startswith('+') else \
			color.normal()
		win.addstr(row, 0, data, attr)

	commandWin = ScrollWindow(commits, commandDraw, commandLen, 1, 1, width - 2, min(len(commits), MAX_COMMITS, height - 3), True)
	detailWin = None
	focusedWin = commandWin
	win.noutrefresh()
	while True:
		if width < 10 or height < 10:
			raise RuntimeError("Window is too small")
		win.boundedBorder(0, 0, commandWin.targetHeight + 1, width - 1, 'Commits', color.white if focusedWin == commandWin else color.grey)
		dualPane = (height > MAX_COMMITS + 5)

		if dualPane:
			_, commit = commandWin.getSelectedData()
			if detailWin is None or detailWin.commit != commit:
				if detailWin is not None:
					del detailWin
				details = repo.git.show('--no-color', '--format=medium', commit.hexsha).split('\n')
				if details[0].startswith('commit '): # Already part of the title
					details.pop(0)
				if len(details) > MAX_DETAIL_LENGTH:
					details = details[:MAX_DETAIL_LENGTH] + ['', '(rest of commit truncated)']
				detailWin = ScrollWindow(details, detailDraw, len, min(len(commits), MAX_COMMITS) + 3, 1, width - 2, height - commandWin.targetHeight - 5)
				detailWin.commit = commit
			win.boundedBorder(commandWin.targetHeight + 2, 0, height - 2, width - 1, commit.hexsha, color.white if focusedWin == detailWin else color.grey)

		win.refresh() # Draw now so stuff before the right edge doesn't get overwritten later
		commandWin.draw()
		if dualPane:
			detailWin.draw()
		if commandWin.canScrollUp(literally = True):
			command, commit = commandWin.getFirstData()
			win.addch(1, 1, curses.ACS_UARROW, commands[command]['color'])
		if commandWin.canScrollDown(literally = True):
			command, commit = commandWin.getLastData()
			win.addch(commandWin.targetHeight, 1, curses.ACS_DARROW, commands[command]['color'])
		command, commit = commandWin.getSelectedData()
		win.addch(commandWin.selection - commandWin.curRow + 1, 1, curses.ACS_RARROW, commands[command]['color'])

		# Keypress
		try:
			c = win.getch()
		except KeyboardInterrupt:
			return done(filename, [])
		if c == curses.KEY_RESIZE:
			win.clear()
			height, width = win.getmaxyx()
			commandWin.resize(width - 2, min(len(commits), MAX_COMMITS, height - 3))
			if detailWin is not None:
				detailWin.resize(width - 2, height - commandWin.targetHeight - 5)
			focusedWin = commandWin
		elif c in (curses.KEY_UP, ord('k')) and focusedWin.canScrollUp():
			focusedWin.scrollUp()
		elif c in (curses.KEY_DOWN, ord('j')) and focusedWin.canScrollDown():
			focusedWin.scrollDown()
		elif c in (curses.KEY_LEFT, ord('h')) and focusedWin.canScrollLeft():
			focusedWin.scrollLeft()
		elif c in (curses.KEY_RIGHT, ord('l')) and focusedWin.canScrollRight():
			focusedWin.scrollRight()
		elif c == 336 and dualPane: # Shift+Up
			focusedWin = commandWin
		elif c == 337 and dualPane: # Shift+Down
			focusedWin = detailWin
		elif c in (curses.KEY_PPAGE, ord('K')):
			if focusedWin.canScrollUp(True):
				focusedWin.scrollUp(focusedWin.targetHeight, True)
			elif focusedWin.canScrollUp():
				focusedWin.scrollUp(focusedWin.targetHeight)
		elif c in (curses.KEY_NPAGE, ord('J')):
			if focusedWin.canScrollDown(True):
				focusedWin.scrollDown(focusedWin.targetHeight, True)
			elif focusedWin.canScrollDown():
				focusedWin.scrollDown(focusedWin.targetHeight)
		elif c == ord('H') and focusedWin.canScrollLeft():
			focusedWin.scrollLeft(focusedWin.targetWidth)
		elif c == ord('L') and focusedWin.canScrollRight():
			focusedWin.scrollRight(focusedWin.targetWidth)
		elif c == curses.KEY_HOME:
			if focusedWin.canScrollLeft():
				focusedWin.scrollLeft(focusedWin.width)
			elif focusedWin.canScrollUp():
				focusedWin.scrollUp(focusedWin.height)
		elif c == curses.KEY_END and focusedWin.canScrollDown():
			focusedWin.scrollDown(focusedWin.height)
		elif c == ord('q'): # Abort
			return done(filename, [])
		elif c == 27: # Escape...maybe
			win.nodelay(True)
			c = win.getch()
			win.nodelay(False)
			if c == curses.ERR: # Actually Escape
				return done(filename, [])
			else: # Alt + (whatever 'c' is now)
				pass
		elif c == 10: # Enter
			return done(filename, commits)
		elif c == curses.KEY_F1:
			help(win, commands)
		elif c in (command['key'] for command in commands.values()):
			for name, command in commands.iteritems():
				if c == command['key']:
					command, commit = commandWin.getSelectedData()
					commandWin.changeSelection((name, commit))
					break

def help(win, commands):
	#TODO Deal with the window being too small
	#TODO Deal with getch() returning RESIZE (the main loop won't see it)
	def writeline(text = None, attr = color.normal()):
		if text:
			win.addstr(text, attr)
		y, x = win.getyx()
		win.move(y + 1, 1)
	def section(title):
		writeline()
		writeline("%s%s" % (title, ' ' * max(0, 40 - len(title))), color.white_underline)
		writeline()
	def key(k, name, attr = color.normal()):
		win.addstr("%-15s  " % k, color.white_bold)
		writeline(name, attr)
	win.clear()
	section('Navigation')
	key('k, Up', 'Scroll up')
	key('j, Down', 'Scroll down')
	key('h, Left', 'Scroll left')
	key('l, Right', 'Scroll right')
	key('S-k, Page Up', 'Scroll up (page)')
	key('S-j, Page Down', 'Scroll down (page)')
	key('S-h', 'Scroll left (page)')
	key('S-l', 'Scroll right (page)')
	key('Home', 'Scroll top') # Technically left, then top, but whatever
	key('End', 'Scroll bottom')
	section('Windows')
	key('S-Up', 'Focus command pane')
	key('S-Down', 'Focus commit pane')
	key('F1', 'Show help pane')
	section('Commands')
	for command, info in commands.iteritems():
		# Hack
		k = 'Del' if info['key'] == curses.KEY_DC else chr(info['key'])
		key(k, "%-6s" % command.title(), info['color'])
	section('Done')
	key('q, Esc, C-c', 'Cancel rebase')
	key('Enter', 'Execute rebase')

	writeline()
	writeline("%-40s" % 'Press any key to close', color.reverse())
	try:
		win.getch()
	except KeyboardInterrupt:
		pass
	finally:
		win.clear()

def done(filename, commits):
	fd, tempname = tempfile.mkstemp(text = True)
	try:
		for command, commit in commits:
			if command == 'del':
				continue
			os.write(fd, "%s %s\n" % (command, commit.hexsha))
	finally:
		os.close(fd)
	shutil.move(tempname, filename)

if len(sys.argv) != 2:
	print "Expected a single filename"
	exit(1)

ob = OutputBuffer()
try:
	curses.wrapper(main, sys.argv[1])
finally:
	print ob.done()
	title('')
