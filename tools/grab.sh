#!/bin/sh
# grab FILE START END : print joined table rows from text dump
sed -n "$2,$3p" "$1" | cut -c1-240 | tr '\n' '~' | sed 's/ | ~/ | /g; s/~ | / | /g' | tr '~' '\n'
