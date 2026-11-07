# i18n (WIP): Italian text for the US build

Research scripts (not part of the game build yet). The US executable keeps its text as a message table
(`D_002D19D0`, 3073 entries), a blob of u16 glyph codes (`StringBlob`) and 22x22 4bpp glyph images (`gSzMsgImage`).
The European disc keeps the same three blocks in `MSG/MSG_<lang>.DAT` (MWo3 files, data from file offset 0x100,
4111 messages, glyph images behind the blob). Word format is the same in both: bit 13 half width, bit 14 macro
(next word = message id), bit 15 end of message.

- `parse_msgs.py`: reads the messages of both versions.
- `align.py`, `align2.py`: align US messages with the EU English ones (ids 0..~1575 line up at a small constant
  offset: UI texts and card names; the card descriptions do not line up).
- `glyphs.py`, `rendermsg.py`: render glyph sheets / messages to PNG for inspection.

Paths in the scripts point at files extracted from the two discs (`iso/SLUS_205.15`, `eu/MSG_*.DAT`).

## Using it

`build_pack.py <SLUS_205.15> <MSG_E.DAT> <MSG_I.DAT> it_pack.bin` (files taken from the US and European discs) writes
the pack; put `it_pack.bin` next to `DotR.exe` and `lang=it` in `DotR-PC.ini`. `runtime/textpack.c` then answers
`SzMsg_LoadFont_Pipe` (rule in `gen/rules.json`) with the Italian stream of the messages the pack holds; every other
message stays English. Italian messages are written without macros so they stand apart from the English texts.
Currently the UI texts and card names that pair up with the European English text (about 690 messages).

## Menu pictures

The US title menu labels are pictures in `DATA/TEXETC.MRG` (RH2 items: 8-bit pictures uploaded to the GS as
64x32 PSMCT32 pages and read back as PSMT8; `texrender.py` decodes and re-encodes them losslessly).
`build_etc.py US_TEXETC.MRG it_TEXETC.MRG` redraws the labels in Italian (the strings of the European build:
NUOVA PARTITA, CONTINUA, DUELLO PERSONALIZZATO, SCAMBIO, Premi tasto START); put `it_TEXETC.MRG` next to
`DotR.exe` with `lang=it` and the port serves it instead of the disc's file (runtime/textpack.c).

## Descriptions, dialogue, HUD labels

`gmatch.py` pairs the English texts of the two discs by content, anywhere in the file (card effects, tutorial and
story text); `build_pack.py` uses it after the offset pairing. The two player-name messages (US 2 and 4, which the
game edits while it runs) stay referenced by macro. `build_sys.py` writes `it_TEXSYS.MRG`: the PLAYER / ENEMY plates
come from the Italian European TEXSYS3.MRG, "Effetto" is drawn. `build_etc.py` also redraws the Rose cards.
