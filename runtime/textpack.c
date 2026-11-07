/* Alternative game text (DotR-PC.ini "lang=it", env DOTR_LANG): messages of the US build replaced by the text of
 * another language, read from it_pack.bin next to the exe (made by i18n/build_pack.py from the player's own
 * European disc). The English text stays where it is: messages without a replacement, and the English texts that
 * the other messages reference, are used unchanged. The generated SzMsg_LoadFont_Pipe asks here for the glyph
 * stream of a message (gen/rules.json). */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "runtime.h"

#define TAB_ADDR  0x002D19D0u
#define BLOB_ADDR 0x002D49D4u
#define IMG_ADDR  0x002F8DEC
#define GLYPH     242
#define NMSG      3073

static unsigned short **g_alt;      /* per message id: replacement stream or NULL */
static int g_state;                  /* 0 not tried, 1 active, 2 off */

static void textpack_load(void)
{
    const char *lang = getenv("DOTR_LANG");
    char path[MAX_PATH], *slash;
    FILE *f;
    unsigned char hdr[8];
    unsigned n, i;

    g_state = 2;
    if (!lang || !*lang || !strcmp(lang, "en")) return;
    if (getenv("DOTR_TEXTPACK")) strncpy(path, getenv("DOTR_TEXTPACK"), MAX_PATH - 1), path[MAX_PATH - 1] = 0;
    else {
        GetModuleFileNameA(NULL, path, MAX_PATH);
        slash = strrchr(path, '\\');
        strcpy(slash ? slash + 1 : path, "it_pack.bin");
    }
    f = fopen(path, "rb");
    if (!f) { hw_log(1, "textpack: %s not found: English text", path); return; }
    if (fread(hdr, 1, 8, f) != 8 || memcmp(hdr, "DOTRIT02", 8)) { fclose(f); hw_log(0, "textpack: bad file %s", path); return; }
    if (fread(&n, 4, 1, f) != 1) { fclose(f); return; }
    for (i = 0; i < n; i++) {                       /* glyph images into the free tail of the glyph area */
        unsigned short code;
        unsigned char img[GLYPH];
        if (fread(&code, 2, 1, f) != 1 || fread(img, 1, GLYPH, f) != GLYPH) { fclose(f); return; }
        if (code < 529) memcpy((unsigned char *)(size_t)(IMG_ADDR + code * GLYPH), img, GLYPH);
    }
    g_alt = (unsigned short **)calloc(NMSG, sizeof *g_alt);
    if (fread(&n, 4, 1, f) != 1) { fclose(f); return; }
    for (i = 0; i < n; i++) {
        unsigned short id, len;
        unsigned short *w;
        if (fread(&id, 2, 1, f) != 1 || fread(&len, 2, 1, f) != 1) break;
        w = (unsigned short *)malloc(len * 2u);
        if (fread(w, 2, len, f) != len || id >= NMSG) { free(w); break; }
        g_alt[id] = w;
    }
    fclose(f);
    g_state = 1;
    hw_log(2, "textpack: %u messages from %s (lang=%s)", n, path, lang);
}

unsigned short *dotr_text_stream(int msg)
{
    static unsigned char seen[NMSG];
    if (g_state == 0) textpack_load();
    if (msg >= 0 && msg < NMSG && !seen[msg] && getenv("DOTR_TEXTLOG")) {      /* each message id once: which texts the game asks for */
        seen[msg] = 1;
        hw_log(2, "textpack: message %d %s", msg, (g_state == 1 && g_alt[msg]) ? "italian" : "english");
    }
    if (g_state == 1 && msg >= 0 && msg < NMSG && g_alt[msg]) return g_alt[msg];
    return (unsigned short *)(size_t)BLOB_ADDR + ((int *)(size_t)TAB_ADDR)[msg];
}
