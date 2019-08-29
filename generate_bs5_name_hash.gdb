# Broken Sword 5 name hash extractor
# sandor.balazsi@gmail.com
#
# usage: gdb --batch --command=generate_bs5_name_hash.gdb --args ./x86_64/BS5_x86_64
# You have to play the whole game to extract all the hashes... ;-)
#
# Broken Sword 5 - The Serpent's Curse v1.11 Linux x64
# Binary: x86_64/BS5_x86_64, file size: 2699176
# MD5 sum: ab12720b680f28b051f7875563502d1e

# set logging
set logging off
set logging file bs5_name_hash.txt

# src/datamanager.cpp: virtual u8* ArchiveFileStdio::getFileByName(const char*)
set breakpoint pending on
break *0x43d510
commands 1
  silent
  set logging on
  printf "%u %s\n", $rdx, $rsi
  set logging off
  continue
end

# start the game
start

