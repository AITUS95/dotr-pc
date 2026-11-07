#!/usr/bin/env bash
export WINEPREFIX=$HOME/decomp/wineprefix WINEDEBUG=-all WINEDLLOVERRIDES="d3dcompiler_47=n"
exec wine "$HOME/decomp/fxcshim/fxc.exe" "$@"
