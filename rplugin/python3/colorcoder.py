#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import neovim
import colorsys
import collections
from zlib import crc32


class VimBatcher:

    def __init__(self, vim):
        self.vim = vim

    def __enter__(self):
        self.cmds = []
        return self

    def command(self, cmd):
        self.cmds.append(cmd)

    def __exit__(self, *args):
        if self.cmds:
            self.vim.command(' | '.join(self.cmds))


SYNTAX_KEYWORD_RESERVED = set([
    'contains', 'oneline', 'fold', 'display',
    'extend', 'concealends', 'conceal', 'cchar',
    'contained', 'containedin', 'nextgroup', 'transparent',
    'skipwhite', 'skipnl', 'skipempty',
])


@neovim.plugin
class Colorcoder:

    def __init__(self, vim):
        self.vim = vim
        self.pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')

    @neovim.command('ColorcoderSetup')
    def setup(self):

        def _getvar(name, default):
            return self.vim.api.get_var(name) \
                    if self.vim.funcs.exists(name) else default

        lightness = _getvar('colorcoder_lightness', 0.6)
        saturation = _getvar('colorcoder_saturation', 0.4)

        with VimBatcher(self.vim) as batcher:
            for h in range(256):
                r, g, b = colorsys.hls_to_rgb(h / 256.0, lightness, saturation)
                color = '#{:02x}{:02x}{:02x}' \
                    .format(int(r * 256), int(g * 256), int(b * 256))
                batcher.command('hi! def colorcoder_{} guifg={}'
                                .format(h, color))

    def _update(self, content, force):
        buf = self.vim.current.buffer
        disabled = buf.api.get_var('colorcoder_disable') \
            if self.vim.funcs.exists('b:colorcoder_disable') \
            else False
        cache = set(buf.api.get_var('colorcoder_cache')) \
            if self.vim.funcs.exists('b:colorcoder_cache') \
            else set()

        if cache and (force or disabled):
            # clear syntax
            with VimBatcher(self.vim) as batcher:
                for h in range(256):
                    batcher.command('syn clear colorcoder_{}'.format(h))
            cache = set()

        if not disabled:
            words = re.findall(self.pattern, content)
            words_group = collections.defaultdict(lambda: [])
            words_reserved = []

            if not cache:
                # do not highlight keywords
                cache |= set(self.vim.call('syntaxcomplete#OmniSyntaxList'))

            for word in words:
                if word in cache:
                    continue
                idx = crc32(word.encode()) % 256
                if word.lower() in SYNTAX_KEYWORD_RESERVED:
                    words_reserved.append((idx, word))
                else:
                    words_group[idx].append(word)
                cache.add(word)
            with VimBatcher(self.vim) as batcher:
                # use "syn match" for reserved syntax options (they cannot use "syn keyword")
                # use "syn keyword" for every others (we assume "syn keyword" is faster)
                for idx, wlist in words_group.items():
                    batcher.command('syn keyword colorcoder_{} {}'
                                    .format(idx, ' '.join(wlist)))
                for idx, word in words_reserved:
                    batcher.command('syn match colorcoder_{} /{}/'
                                    .format(idx, word))

        buf.api.set_var('colorcoder_cache', list(cache))

    @neovim.command('ColorcoderUpdate', bang=True)
    def update_full(self, bang):
        buf = self.vim.current.buffer
        return self._update('\n'.join(buf.api.get_lines(0, -1, False)), bang)

    @neovim.command('ColorcoderUpdateLine')
    def update_line(self):
        return self._update(self.vim.current.line, False)
