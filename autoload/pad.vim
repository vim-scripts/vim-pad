" vim: set fdm=marker fdc=2 :

" Pad Information:  {{{1
 
" Gets the title of the currently selected pad
function! pad#GetPadTitle()
	if getline('.') != ""
		try
			let retval = split(split(substitute(getline('.'), '↲','\n', "g"), '\n')[0], '\%u2e25 ')[1]
		catch /E684/
			let retval "EMPTY"
		endtry
		return retval
	endif
	return ""
endfunction

" Gets the human readable date of the currently selected pad
function! pad#GetPadHumanDate()
	if getline('.') != ""
		return split(split(getline('.'), ' │')[0], '@')[1]
	endif
	return ""
endfunction

" Gets the id of the currently selected pad
function! pad#GetPadId()
	if getline('.') != ""
		return split(getline('.'))[0]
	endif
	return ""
endfunction

" Operations: {{{1
if has("python")

" Global {{{2

function! pad#OpenPad(title)
	execute "python padlib.handler.open_pad(first_line='".a:title."')"
endfunction

function! pad#ListPads(query, archive)
	execute "python padlib.handler.display('".a:query."', '".a:archive."')"
endfunction

function! pad#SearchPads()
	python padlib.handler.search_pads()
endfunction

" Pad local {{{2

function! pad#UpdatePad()
	python padlib.pad_local.update()
endfunction

function! pad#DeleteThis()
	python padlib.pad_local.delete()
endfunction

function! pad#AddModeline()
	python padlib.pad_local.add_modeline()
endfunction

function! pad#MoveToFolder()
	python padlib.pad_local.move_to_folder()
endfunction

function! pad#MoveToSaveDir()
	python padlib.pad_local.move_to_savedir()
endfunction

function! pad#Archive()
	python padlib.pad_local.archive()
endfunction

function! pad#Unarchive()
	python padlib.pad_local.unarchive()
endfunction

" List local {{{2

function! pad#EditPad()
	python padlib.list_local.edit_pad()
endfunction

function! pad#DeletePad()
	python padlib.list_local.delete_pad()
endfunction

function! pad#MovePad()
	python padlib.list_local.move_to_folder()
endfunction

function! pad#MovePadToSaveDir()
	python padlib.list_local.move_to_savedir()
endfunction

function! pad#ArchivePad()
	python padlib.list_local.archive_pad()
endfunction

function! pad#UnarchivePad()
	python padlib.list_local.unarchive_pad()
endfunction

function! pad#IncrementalSearch()
	python padlib.list_local.incremental_search()
endfunction

function! pad#Sort()
	let s:sort_type = input("[pad] sort list by (title=1, tags=2, date=3): ", "1")
	if s:sort_type != ""
		execute "python padlib.list_local.sort('".s:sort_type."')"
	endif
	redraw!
endfunction

endif
