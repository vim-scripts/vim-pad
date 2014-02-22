# vim: set fdm=marker fdc=2 :
# coding=utf-8

# imports {{{1
import vim
import re
from glob import glob
from os import walk
from os.path import join, getmtime, isfile, isdir, exists
from subprocess import Popen, PIPE
from padlib.utils import get_save_dir
from padlib.pad import PadInfo
from padlib.timestamps import natural_timestamp

# globals (caches) {{{1
cached_data = []
cached_timestamps = []
cached_filenames = []


def open_pad(path=None, first_line=""):  # {{{1
    """Creates or opens a note.

    path: a valid path for a note.

    first_line: a string to insert to a new note, if given.
    """
    # we require self.save_dir_set to be set to a valid path
    if get_save_dir() == "":
        vim.command('let tmp = confirm("IMPORTANT:\n'
                'Please set g:pad_dir to a valid path in your vimrc.",'
                ' "OK", 1, "Error")')
        return

    # if no path is provided, we create one using the current time
    if not path:
        path = join(get_save_dir(),
                    PadInfo([first_line]).id + vim.eval("g:pad_default_file_extension"))
    path = path.replace(" ", "\ ")

    if bool(int(vim.eval("g:pad_open_in_split"))):
        if vim.eval('g:pad_position["pads"]') == 'right':
            vim.command("silent! rightbelow"
                    + str(vim.eval("g:pad_window_width")) + "vsplit " + path)
        else:
            vim.command("silent! botright"
                    + str(vim.eval("g:pad_window_height")) + "split " + path)
    else:
        vim.command("silent! edit " + path)

    # we don't keep the buffer when we hide it
    vim.command("set bufhidden=wipe")

    # set the filetype to our default
    if vim.eval('&filetype') in ('', 'conf'):
        vim.command("set filetype=" + vim.eval("g:pad_default_format"))

    # map the local commands
    if bool(int(vim.eval('has("gui_running")'))):
        vim.command("noremap <silent> <buffer> <localleader><delete> :call pad#DeleteThis()<cr>")
    else:
        vim.command("noremap <silent> <buffer> <localleader>dd :call pad#DeleteThis()<cr>")

    vim.command("noremap <silent> <buffer> <localleader>+m :call pad#AddModeline()<cr>")
    vim.command("noremap <silent> <buffer> <localleader>+f :call pad#MoveToFolder()<cr>")
    vim.command("noremap <silent> <buffer> <localleader>-f :call pad#MoveToSaveDir()<cr>")
    vim.command("noremap <silent> <buffer> <localleader>+a :call pad#Archive()<cr>")
    vim.command("noremap <silent> <buffer> <localleader>-a :call pad#Unarchive()<cr>")

    # insert the text in first_line to the buffer, if provided
    if first_line:
        vim.current.buffer.append(first_line, 0)
        vim.command("normal! j")


def listdir_recursive_nohidden(path, archive):  # {{{1
    matches = []
    for root, dirnames, filenames in walk(path, topdown=True):
        for dirname in dirnames:
            if dirname.startswith('.'):
                dirnames.remove(dirname)
            if archive != "!":
                if dirname == "archive":
                    dirnames.remove(dirname)
        matches += [join(root, f) for f in filenames if not f.startswith('.')]
    return matches


def get_filelist(query=None, archive=None):  # {{{1
    """ __get_filelist(query) -> list_of_notes

    Returns a list of notes. If no query is provided, all the valid filenames
    in self.save_dir are returned in a list, otherwise, return the results of
    grep or ack search for query in self.save_dir.
    """
    if not query or query == "":
        files = listdir_recursive_nohidden(get_save_dir(), archive)
    else:
        search_backend = vim.eval("g:pad_search_backend")
        if search_backend == "grep":
            # we use Perl mode for grep (-P), because it is really fast
            command = ["grep", "-P", "-n", "-r", query, get_save_dir() + "/"]
            if archive != "!":
                command.append("--exclude-dir=archive")
        elif search_backend == "ack":
            if vim.eval("executable('ack')") == "1":
                ack_path = "ack"
            else:
                ack_path = "/usr/bin/vendor_perl/ack"
            command = [ack_path, query, get_save_dir() + "/", "--type=text"]
            if archive != "!":
                command.append("--ignore-dir=archive")

        if bool(int(vim.eval("g:pad_search_ignorecase"))):
            command.append("-i")
        command.append("--max-count=1")

        files = [line.split(":")[0]
                for line in Popen(command, stdout=PIPE, stderr=PIPE).
                            communicate()[0].split("\n") if line != '']

        if bool(int(vim.eval("g:pad_query_dirnames"))):
            matching_dirs = filter(isdir, glob(join(get_save_dir(), "*"+ query+"*")))
            for mdir in matching_dirs:
                files.extend(filter(lambda x: x not in files, listdir_recursive_nohidden(mdir, archive)))

    return files

def fill_list(files, queried=False, custom_order=False): # {{{1
    """ Writes the list of notes to the __pad__ buffer.

    files: a list of files to process.

    queried: whether files is the result of a query or not.

    custom_order: whether we should keep the order of the list given (implies queried=True).

    Keeps a cache so we only read the notes when the files have been modified.
    """
    global cached_filenames, cached_timestamps, cached_data

    # we won't want to touch the cache
    if custom_order:
        queried = True

    files = filter(exists, [join(get_save_dir(), f) for f in files])

    timestamps = [getmtime(join(get_save_dir(), f)) for f in files]

    # we will have a new list only on the following cases
    if queried or files != cached_filenames or timestamps != cached_timestamps:
        lines = []
        if not custom_order:
            files = reversed(sorted(files, key=lambda i: getmtime(join(get_save_dir(), i))))
        for pad in files:
            pad_path = join(get_save_dir(), pad)
            if isfile(pad_path):
                with open(join(get_save_dir(), pad)) as pad_file:
                    info = PadInfo(pad_file)
                    if info.isEmpty:
                        if bool(int(vim.eval("g:pad_show_dir"))):
                            tail = info.folder + u'\u2e25 '.encode('utf-8') + "[EMPTY]"
                        else:
                            tail = "[EMPTY]"
                    else:
                        if bool(int(vim.eval("g:pad_show_dir"))):
                            tail = info.folder + u'\u2e25 '.encode('utf-8') + u'\u21b2'.encode('utf-8').join((info.summary, info.body))
                        else:
                            tail = u'\u21b2'.encode('utf-8').join((info.summary, info.body))
                    lines.append(pad + " @ " + tail)
            else:
                pass

        # we only update the cache if we are not queried, to preserve the global cache
        if not queried:
            cached_data = lines
            cached_timestamps = timestamps
            cached_filenames = files

    # update natural timestamps
    def add_natural_timestamp(matchobj):
        id_string = matchobj.group("id")
        mtime = str(int(getmtime(join(get_save_dir(), matchobj.group("id")))*1000000))
        return id_string + " @ " + natural_timestamp(mtime).ljust(19) + " │"

    if not queried: # we use the cache
        lines = [re.sub("(?P<id>^.*?) @", add_natural_timestamp, line) for line in cached_data]
    else: # we use the new values in lines
        lines = [re.sub("(?P<id>^.*?) @", add_natural_timestamp, line) for line in lines]

    # we now show the list
    del vim.current.buffer[:] # clear the buffer
    vim.current.buffer.append(list(lines))
    vim.command("normal! dd")

def display(query, archive): # {{{1
    """ Shows a list of notes.

    query: a string representing a regex search. Can be "".

    Builds a list of files for query and then processes it to show the list in the pad format.
    """
    if get_save_dir() == "":
        vim.command('let tmp = confirm("IMPORTANT:\n'\
                'Please set g:pad_dir to a valid path in your vimrc.", "OK", 1, "Error")')
        return
    pad_files = get_filelist(query, archive)
    if len(pad_files) > 0:
        if vim.eval("bufexists('__pad__')") == "1":
            vim.command("bw __pad__")
        if vim.eval('g:pad_position["list"]') == "right":
            vim.command("silent! rightbelow " + str(vim.eval('g:pad_window_width')) + "vnew __pad__")
        else:
            vim.command("silent! botright " + str(vim.eval("g:pad_window_height")) + "new __pad__")
        fill_list(pad_files, query != "")
        vim.command("set filetype=pad")
        vim.command("setlocal nomodifiable")
    else:
        print "no pads"

def search_pads(): # {{{1
    """ Aks for a query and lists the matching notes.
    """
    if get_save_dir() == "":
        vim.command('let tmp = confirm("IMPORTANT:\n'\
                'Please set g:pad_dir to a valid path in your vimrc.", "OK", 1, "Error")')
        return
    query = vim.eval('input(">>> ")')
    display(query, "")
    vim.command("redraw!")

def global_incremental_search():  # {{{1
    """ Provides incremental search in normal mode without opening the list.
    """
    query = ""
    should_create_on_enter = False

    vim.command("echohl None")
    vim.command('echo ">> "')
    while True:
        raw_char = vim.eval("getchar()")
        if raw_char in ("13", "27"):
            if raw_char == "13":
                if should_create_on_enter:
                    open_pad(first_line=query)
                    vim.command("echohl None")
                else:
                    display(query, True)
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
        pad_files = get_filelist(query)
        if pad_files != []:
            info = ""
            vim.command("echohl None")
            should_create_on_enter = False
        else:  # we will create a new pad
            info = "[NEW] "
            vim.command("echohl WarningMsg")
            should_create_on_enter = True
        vim.command("redraw")
        vim.command('echo ">> ' + info + query + '"')

