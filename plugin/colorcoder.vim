function! s:load_au_buflocal()
    if exists('b:colorcoder_au_loaded') && b:colorcoder_au_loaded == 1
        return
    endif
    autocmd BufReadPost <buffer=abuf> :ColorcoderUpdate!
    autocmd TextChanged <buffer=abuf> :ColorcoderUpdate
    autocmd TextChangedI <buffer=abuf> :ColorcoderUpdateLine
    let b:colorcoder_au_loaded = 1
    ColorcoderUpdate!
endfunction

augroup colorcoder_au
    autocmd!
    autocmd VimEnter * :ColorcoderSetup
    if exists('g:colorcoder_enable_filetypes')
        execute 'autocmd Filetype ' .
                    \ join(g:colorcoder_enable_filetypes, ',') .
                    \ ' call s:load_au_buflocal()'
    endif
augroup end
