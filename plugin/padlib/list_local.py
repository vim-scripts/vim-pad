# vim: set fdm=marker fdc=2 :
# coding=utf-8

# imports {{{1
import vim
import re
from os import remove, mkdir
from os.path import join, basename, exists
from shutil import move
from padlib.handler import open_pad, get_filelist, fill_list
from padlib.utils import get_save_dir, make_sure_dir_is_empty


def get_selected_path():  # {{{1
    return join(get_save_dir(), vim.current.line.split(" @")[0])


def edit_pad():  # {{{1
    """ Opens the currently selected note in the __pad__ buffer.
    """
    path = get_selected_path()
    vim.command("bd")
    open_pad(path=path)


def delete_pad():  # {{{1
    """ Deletes the currently selected note in the __pad__ buffer.
    """
    confirm = vim.eval('input("really delete? (y/n): ")')
    if confirm in ("y", "Y"):
        path = get_selected_path()
        remove(path)
        make_sure_dir_is_empty(path)
        vim.command("ListPads")
        vim.command("redraw!")


def move_to_folder(path=None):  # {{{1
    """ Moves the selected pad to a subfolder of g:pad_dir
    """
    selected_path = get_selected_path()
    if path is None:
        path = vim.eval('input("move to: ")')
    if not exists(join(get_save_dir(), path)):
        mkdir(join(get_save_dir(), path))
    move(selected_path, join(get_save_dir(), path, basename(selected_path)))
    make_sure_dir_is_empty(path)
    vim.command("ListPads")
    if path is None:
        vim.command("redraw!")


def move_to_savedir():  # {{{1
    """ Moves a note to g:pad_dir
    """
    move_to_folder("")


def archive_pad():  # {{{1
    """ Archives the currently selected note
    """
    move_to_folder("archive")


def unarchive_pad():  # {{{1
    """ Unarchives the currently selected note
    """
    move_to_savedir()


def incremental_search():  # {{{1
    """ Provides incremental search within the __pad__ buffer.
    """
    query = ""
    should_create_on_enter = False

    vim.command("echohl None")
    vim.command('echo ">> "')
    while True:
        raw_char = vim.eval("getchar()")
        if raw_char in ("13", "27"):
            if raw_char == "13" and should_create_on_enter:
                vim.command("bw")
                open_pad(first_line=query)
                vim.command("echohl None")
            vim.command("redraw!")
            break
        else:
            try:   # if we can convert to an int, we have a regular key
                int(raw_char)   # we bring up an error on nr2char
                last_char = vim.eval("nr2char(" + raw_char + ")")
                query = query + last_char
            except:  # if we don't, we have some special key
                keycode = unicode(raw_char, errors="ignore")
                if keycode == "kb":  # backspace
                    query = query[:-len(last_char)]
        vim.command("setlocal modifiable")
        pad_files = get_filelist(query)
        if pad_files != []:
            fill_list(pad_files, query != "")
            vim.command("setlocal nomodifiable")
            info = ""
            vim.command("echohl None")
            should_create_on_enter = False
        else:  # we will create a new pad
            del vim.current.buffer[:]
            info = "[NEW] "
            vim.command("echohl WarningMsg")
            should_create_on_enter = True
        vim.command("redraw")
        vim.command('echo ">> ' + info + query + '"')
# }}}1
# sort types {{{1
SORT_TYPES = {
        "1": "title",
        "2": "tags",
        "3": "date"
        }


def sort(key="1"):  # {{{1

    if key not in SORT_TYPES:
        return

    key = SORT_TYPES[key]
    if key == "date":
        vim.command("ListPads")
        return

    tuples = []
    if key == "tags":
        view_files = [line.split()[0] for line in vim.current.buffer]
        for pad_id in view_files:
            with open(pad_id) as fi:
                tags = sorted([tag.lower().replace("@", "")
                                for tag in re.findall("@\w*", fi.read(200))])
            tuples.append((pad_id, tags))
        tuples = sorted(tuples, key=lambda f: f[1])
        tuples = filter(lambda i: i[1] != [], tuples) + \
                 filter(lambda i: i[1] == [], tuples)
    elif key == "title":
        l = 1
        for line in vim.current.buffer:
            pad_id = line.split()[0]
            title = vim.eval('''split(split(substitute(getline(''' + str(l) + '''), '↲','\n', "g"), '\n')[0], ' │ ')[1]''')
            tuples.append((pad_id, title))
            l += 1
        tuples = sorted(tuples, key=lambda f: f[1])

    vim.command("setlocal modifiable")
    fill_list([f[0] for f in tuples], custom_order=True)
    vim.command("setlocal nomodifiable")
