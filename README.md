![](/../doc-imgs/gir.png)

gir is a curses interface for editing **g**it **i**nteractive **r**ebase todo lists.

## Setup

You must tell git to use gir as your editor, but only when editing rebase todo lists. gir comes with a [shell script](/editor) to handle this. If you set `editor` as your git editor, it will send rebase todo lists to gir, and all other files to the editor specified by `$EDITOR`:

    git config --global core.editor /path/to/gir/editor

