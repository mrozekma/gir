![](/../doc-imgs/doc-imgs/gir.png?raw=true)

gir is a curses interface for editing **g**it **i**nteractive **r**ebase todo lists. Everyone wants it:

> < mrozekma> somebody should really write a program specifically for interacting with the git rebase file. make it trivial to change the flag on each file, see more info about each commit, etc.  
> < mrozekma> somebody do this  
> < necroyeti> ... or just use vim?

## Setup

You must tell git to use gir as your editor, but only when editing rebase todo lists. gir comes with a shell script to handle this. If you set [`editor`](/editor) as your git editor, it will send rebase todo lists to gir, and all other files to `$EDITOR`:

    git config --global core.editor /path/to/gir/editor

## How to use

gir is divided into two sections. The **command pane** shows the rebase todo list and is essentially the same view you would get from your text editor2. The **detail pane** (if your window is large enough) shows a diff of the currently selected commit for context:

![](/../doc-imgs/doc-imgs/before.png?raw=true)
![](/../doc-imgs/doc-imgs/after.png?raw=true)

### Hotkeys

This list of hotkeys is accessible within gir by pressing <kbd>F1</kbd>.

#### Navigation
* <kbd>k</kbd>, <kbd>Up</kbd> &mdash; Scroll up
* <kbd>j</kbd>, <kbd>Down</kbd> &mdash; Scroll down
* <kbd>h</kbd>, <kbd>Left</kbd> &mdash; Scroll left
* <kbd>l</kbd>, <kbd>Right</kbd> &mdash; Scroll right
* <kbd>Shift</kbd>+<kbd>k</kbd>, <kbd>Page Up</kbd> &mdash; Scroll up (page)
* <kbd>Shift</kbd>+<kbd>j</kbd>, <kbd>Page Down</kbd> &mdash; Scroll down (page)
* <kbd>Shift</kbd>+<kbd>h</kbd> &mdash; Scroll left (page)
* <kbd>Shift</kbd>+<kbd>l</kbd> &mdash; Scroll right (page)
* <kbd>Home</kbd> &mdash; Scroll top
* <kbd>End</kbd> &mdash; Scroll bottom

#### Windows
* <kbd>Shift</kbd>+<kbd>Up</kbd> &mdash; Focus command pane
* <kbd>Shift</kbd>+<kbd>Down</kbd> &mdash; Focus commit pane
* <kbd>F1</kbd> &mdash; Show help pane

#### Commands
These hotkeys will change the currently selected command.
* <kbd>p</kbd> &mdash; Pick
* <kbd>r</kbd> &mdash; Reword
* <kbd>e</kbd> &mdash; Edit
* <kbd>s</kbd> &mdash; Squash
* <kbd>f</kbd> &mdash; Fixup
* <kbd>Del</kbd> &mdash; Del (delete the current commit)

#### Done
* <kbd>q</kbd>, <kbd>Esc</kbd>, <kbd>Ctrl</kbd>+<kbd>c</kbd> &mdash; Cancel rebase
* <kbd>Enter</kbd> &mdash; Execute rebase
