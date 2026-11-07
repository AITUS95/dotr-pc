# DotR-PC — branch `italiano`

Fork di [kira-502/dotr-pc](https://github.com/kira-502/dotr-pc) che aggiunge **la traduzione italiana** di
*Yu-Gi-Oh! The Duelists of the Roses* (USA, SLUS-20515), usando i testi della versione europea (Fr,De,Es,It),
e gli strumenti per **compilare ed eseguire il port su Linux** (cross-compilazione con clang-cl e Wine).

**Non affiliato a Konami.** Il repository non contiene dati del gioco: servono i tuoi dischi (ISO USA ed europea).
I file derivati dai dischi (`it_pack.bin`, `it_TEXETC.MRG`, `it_TEXSYS.MRG`) si generano in locale e sono esclusi da git.

## Stato attuale

| Parte | Stato |
|---|---|
| Messaggi (interfaccia, nomi e descrizioni delle carte, tutorial, storia) | ~2.750 su ~3.050 in italiano |
| Titolo e menu principale (immagini) | in italiano |
| Etichette del duello (GIOCATORE / NEMICO / Effetto), carte Rosa Rossa / Rosa Bianca | in italiano |
| Costruttore di mazzi, scambio, menu (stringhe dell'eseguibile) | in italiano, con parole accorciate per stare nei riquadri |
| Circa 50 frasi di dialogo (la versione europea le divide in modo diverso) | ancora in inglese |
| Piccolo testo sulle carte coperte e sulle cornici Labirinto (texture) | in inglese, come nella versione europea |
| Un testo di carta con più di 17 righe in italiano | lasciato in inglese (il gioco ne gestisce 17) |
| Filmato iniziale sotto Wine | non parte |
| Parole sovrapposte o tagliate in alcune schermate | segnalate, **ancora da individuare** (serve uno screenshot) |

Verificato su screenshot di storia, duello, menu, costruttore di mazzi e scambio; non ancora giocato per intero.
Il renderer GPU funziona con DXVK (Wine); gli shader si compilano con `d3dcompiler_47.dll` e un `fxc` minimale
(`linux/`).

## Come funziona la traduzione

- I testi USA sono una tabella di messaggi (sequenze di indici di glifi) nell'eseguibile; la versione europea li ha
  in `MSG/MSG_<lingua>.DAT`. `i18n/build_pack.py` abbina i messaggi USA a quelli europei (stesso testo inglese, anche
  in posizioni diverse), espande le macro e scrive `it_pack.bin`.
- `runtime/textpack.c` (ini: `lang=it`) risponde a `SzMsg_LoadFont_Pipe` con il testo italiano dei messaggi che
  il pacchetto contiene; gli altri restano in inglese. I nomi dei giocatori, inseriti dal gioco, restano macro.
- Le stringhe dell'interfaccia dell'eseguibile (`gen/ui_strings.json`) sono spostate in slot propri dal generatore,
  così il pacchetto può metterci stringhe di lunghezza diversa.
- Le immagini del menu stanno in `TEXETC.MRG` / `TEXSYS.MRG` (testure RH2): `i18n/build_etc.py` e
  `i18n/build_sys.py` le ridisegnano; il port serve i file `it_*.MRG` al posto di quelli del disco.

## Uso (Linux)

1. Compila il port come descritto in `linux/` (toolchain CMake per clang-cl, SDK di xwin, `fxc` per Wine).
2. Estrai dai dischi `SLUS_205.15`, `MSG_E.DAT`, `MSG_I.DAT`, `TEXETC.MRG`, `TEXSYS.MRG` (USA) e `TEXSYS3.MRG` (europeo).
3. `python3 i18n/build_pack.py SLUS_205.15 MSG_E.DAT MSG_I.DAT it_pack.bin`, `build_etc.py`, `build_sys.py`.
4. Metti i file accanto a `DotR.exe` con `lang=it` in `DotR-PC.ini`.

Dettagli e note di ricerca: [i18n/README.md](i18n/README.md).

## Prossimi passi

1. Individuare e correggere le parole sovrapposte/tagliate (servono esempi).
2. Tradurre le ultime frasi di storia rimaste in inglese.
3. Rendere l'IA degli avversari più difficile (modificando il C in `src/ai` della decompilazione).

---

# DotR-PC

A native Windows port of *Yu-Gi-Oh! The Duelists of the Roses* (PlayStation 2, USA release SLUS-20515), built from
the game's matching decompilation.

**Not affiliated with or endorsed by Konami.** This repository contains no game data: no pictures, sounds, movies,
text or game code. You need your own copy of the game, the USA disc, as a disc image (`.iso`). The program reads the
game from that image at run time; the build reads the game's executable and code modules from it too.

## How it works

```
the decompilation (C that compiles to the PS2 game, separate repository)
        |  gen/  : the port generator turns its C into C that compiles for 32-bit Windows
        v
  native game code  +  recomp/ : the 762 code modules (card effects, battle animations), translated from MIPS to C
        |
        v
  runtime/ + hle/ : the PS2 the game expects, answered on the PC: memory map at the console's addresses, threads,
                    timers, DMA, memory cards, pad, disc, Sony library calls
  gfx/            : DMA/VIF/VU1/GIF/GS: an exact software renderer and a Direct3D 11 one, the window
  sound/, movie/  : the IOP and its SPU2 sound driver (the game's own IOP code), the PSS movies
```

`DotR.exe` is a tiny loader that reserves the PS2 address range and loads `dotr.dll`, which holds the game and the
PC layer.

## Status

The game boots and plays on the PC: menus, the campaign, duels, battle animations, movies, sound, memory cards. It
has not been played through end to end in every part. Duels between the game's computer players are deterministic
and checked against the original PS2 code by an "oracle" that runs the original MIPS code beside the port. Expect
bugs; see CONTRIBUTING.md.

## Building

See [BUILDING.md](BUILDING.md). In short: Windows with the Visual Studio 2022 Build Tools (clang-cl), WSL with the
decompilation's toolchain, the decompilation at the commit in `gen/DECOMP_COMMIT`, and your disc image; then
`full-build.cmd your.iso`.

## Developing

[docs/DEVELOPING.md](docs/DEVELOPING.md): the developer switches (developer menu, computer-vs-computer duels,
automatic duels, pad scripts, headless runs, pictures, reports), the logs, and the checks every change should pass
(`tools/gate.cmd`).

## Layout

| folder | what |
|---|---|
| `loader/` | `DotR.exe` (console) and the window build: reserve PS2 memory, load `dotr.dll` |
| `gen/` | the port generator: decomp C (pinned commit) -> compilable PC C, its rules (`rules.json`) and checks |
| `runtime/` | memory map, ELF loading from the disc, threads, timers, virtual hardware registers, pad, memory cards, crash and hang reports, bot duels, pad scripts |
| `hle/` | Sony library calls answered on the PC (kernel, SIF/IOP, CD, pad, memory card, C library) |
| `recomp/` | the module recompiler (MIPS -> C) and its checks, including the oracle |
| `gfx/` | graphics: DMA/VIF1/VU1/GIF/GS, renderers, window, VU0 maths, F12 capture and replay |
| `sound/`, `movie/` | IOP emulator + SPU2, movie player |
| `mcimport/` | imports a PS2 memory-card save into the PC's memory-card folders |
| `tests/`, `tools/` | windowless checks, the gate, release scripts |

## Licence

CC0 1.0 (public domain dedication), like the decompilation: see [LICENSE](LICENSE). Third-party parts keep their
own licences: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The licence covers this project's own work only; it
grants no rights in the game or in Sony's libraries.

No builds are published here. Build it yourself from your own disc.
