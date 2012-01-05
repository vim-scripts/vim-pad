" File:			pad.vim
" Description:	Quick-notetaking for vim.
" Author:		Felipe Morales
" Version:		0.6

if (exists("g:loaded_pad") && g:loaded_pad) || &cp
    finish
endif
let g:loaded_pad = 1

" Default Settings:
"
if !exists('g:pad_dir')
	if filewritable(expand("~/notes")) == 2
		let g:pad_dir = "~/notes"
	else
		let g:pad_dir = ""
	endif
else
	if filewritable(expand(eval("g:pad_dir"))) != 2
		let g:pad_dir = ""
	endif
endif
if !exists('g:pad_format')
	let g:pad_format = "markdown"
endif
if !exists('g:pad_window_height')
	let g:pad_window_height = 5
endif
if !exists('g:pad_search_backend')
	let g:pad_search_backend = "grep"
endif
if !exists('g:pad_search_ignorecase')
	let g:pad_search_ignorecase = 1
endif
if !exists('g:pad_read_nchars_from_files')
	let g:pad_read_nchars_from_files = 200
endif
if !exists('g:pad_highlighting_variant')
	let g:pad_highlighting_variant = 0
endif
if !exists('g:pad_use_default_mappings')
	let g:pad_use_default_mappings = 1
endif

" Commands:
"
" Creates a new note
command! OpenPad exec 'py pad.pad_open()'
" Shows a list of the existing notes
command! -nargs=? ListPads exec "py pad.list_pads('<args>')"

" Key Mappings:
"
noremap <silent> <unique> <Plug>ListPads <esc>:ListPads<CR>
inoremap <silent> <unique> <Plug>ListPads <esc>:ListPads<CR>
noremap <silent> <unique>  <Plug>OpenPad <esc>:OpenPad<CR>
inoremap <silent> <unique> <Plug>OpenPad <esc>:OpenPad<CR>
noremap <silent> <unique> <Plug>SearchPads :py pad.search_pads()<cr>

" You can set custom bindings by re-mapping the previous ones.
" For example, you can add the following to your vimrc:
" 
"     nmap ,pl <Plug>ListPads
"
" If you want disable the default_mappings, set
" g:pad_use_default_mappings to 0

function s:CreateMapping(key, action, modename)
  let mode = a:modename == "normal" ? "nmap" : "imap"

  try
    execute mode . " <unique> " . a:key . " <Plug>" . a:action
  catch /E227/
    echom "[vim-pad] " . a:key . " in " . a:modename . " mode is already mapped."
  endtry
endfunction

if g:pad_use_default_mappings == 1
	if has("gui_running")
    call s:CreateMapping("<C-esc>", "ListPads", "normal")
    call s:CreateMapping("<C-esc>", "ListPads", "insert")
    call s:CreateMapping("<S-esc>", "OpenPad", "normal")
    call s:CreateMapping("<S-esc>", "OpenPad", "insert")
	else " the previous mappings don't work in the terminal
    call s:CreateMapping("<leader><esc>", "ListPads", "normal")
    call s:CreateMapping("<leader><esc>", "ListPads", "insert")
    call s:CreateMapping("<leader>n", "OpenPad", "normal")
    call s:CreateMapping("<leader>n", "OpenPad", "insert")
	endif

  call s:CreateMapping("<leader>s", "SearchPads", "normal")
endif

" To update the date when files are modified
execute "au! BufEnter" printf("%s*", g:pad_dir) ":let b:pad_modified = 0"
execute "au! BufWritePre" printf("%s*", g:pad_dir) ":let b:pad_modified = eval(&modified)"
execute "au! BufLeave" printf("%s*", g:pad_dir) ":py pad.pad_update()"

" Load the plugin code proper
pyfile <sfile>:p:h/pad.py
" the python object pad represents the plugin state
python pad=Pad()
