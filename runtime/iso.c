/* ISO9660 reader for the owner's disc image (read-only). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <string.h>
#include "runtime.h"
#include "hle_rt.h"

static HANDLE g_iso = INVALID_HANDLE_VALUE;

int iso_open(const wchar_t *path)
{
    unsigned char pvd[2048];
    if (g_iso != INVALID_HANDLE_VALUE) CloseHandle(g_iso);
    g_iso = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (g_iso == INVALID_HANDLE_VALUE) return 0;
    if (!iso_read_sectors(16, 1, pvd) || memcmp(pvd + 1, "CD001", 5) != 0) {
        CloseHandle(g_iso);
        g_iso = INVALID_HANDLE_VALUE;
        return 0;
    }
    return 1;
}

double rt_hitch_disc_s;         /* time and bytes in disc reads since the last field (DOTR_HITCH, threads.c) */
unsigned rt_hitch_disc_bytes;

int iso_read(uint64_t offset, uint32_t size, void *dst)
{
    LARGE_INTEGER li;
    DWORD got = 0;
    double t0 = rt_seconds();
    int ok;
    li.QuadPart = (LONGLONG)offset;
    if (g_iso == INVALID_HANDLE_VALUE || !SetFilePointerEx(g_iso, li, NULL, FILE_BEGIN)) return 0;
    ok = ReadFile(g_iso, dst, size, &got, NULL) && got == size;
    rt_hitch_disc_s += rt_seconds() - t0;
    rt_hitch_disc_bytes += got;
    return ok;
}

/* Files of the disc replaced by a local file of the same layout (language packs: runtime/textpack.c). */
static struct { uint32_t lba, sectors; unsigned char *data; } g_over[8];
static int g_nover;

int iso_override_file(const char *disc_path, const char *local_path)
{
    uint32_t lba, size;
    FILE *f;
    long n;
    unsigned char *buf;
    if (g_nover >= 8 || !iso_find(disc_path, &lba, &size)) return 0;
    f = fopen(local_path, "rb");
    if (!f) return 0;
    fseek(f, 0, SEEK_END); n = ftell(f); fseek(f, 0, SEEK_SET);
    buf = (unsigned char *)calloc(((size_t)size + 2047) & ~(size_t)2047, 1);   /* never longer than the disc's file */
    if (!buf) { fclose(f); return 0; }
    if (fread(buf, 1, (size_t)(n < (long)size ? n : (long)size), f) == 0) { fclose(f); free(buf); return 0; }
    fclose(f);
    g_over[g_nover].lba = lba; g_over[g_nover].sectors = (size + 2047) / 2048; g_over[g_nover].data = buf; g_nover++;
    return 1;
}

int iso_read_sectors(uint32_t lba, uint32_t count, void *dst)
{
    int i;
    if (g_nover) {
        uint32_t s;
        for (s = 0; s < count; s++) {
            int hit = 0;
            for (i = 0; i < g_nover; i++)
                if (lba + s >= g_over[i].lba && lba + s < g_over[i].lba + g_over[i].sectors) {
                    memcpy((unsigned char *)dst + (size_t)s * 2048, g_over[i].data + (size_t)(lba + s - g_over[i].lba) * 2048, 2048);
                    hit = 1; break;
                }
            if (!hit && !iso_read((uint64_t)(lba + s) * 2048u, 2048u, (unsigned char *)dst + (size_t)s * 2048)) return 0;
        }
        return 1;
    }
    return iso_read((uint64_t)lba * 2048u, count * 2048u, dst);
}

static int name_eq(const unsigned char *rec_name, int len, const char *want, int want_len)
{
    int i, n = len;
    for (i = 0; i < len; i++) if (rec_name[i] == ';') { n = i; break; }
    if (n != want_len) return 0;
    for (i = 0; i < n; i++) {
        char a = (char)rec_name[i], b = want[i];
        if (a >= 'a' && a <= 'z') a -= 32;
        if (b >= 'a' && b <= 'z') b -= 32;
        if (a != b) return 0;
    }
    return 1;
}

/* path like "\\DATA\\MODEL.MRG" or "DATA/MODEL.MRG;1"; returns 1 and fills lba/size when found. */
int iso_find(const char *path, uint32_t *lba_out, uint32_t *size_out)
{
    unsigned char pvd[2048];
    static unsigned char dir[64 * 2048];
    uint32_t lba, size;
    const char *p = path;
    if (!iso_read_sectors(16, 1, pvd)) return 0;
    lba = *(uint32_t *)(pvd + 156 + 2);
    size = *(uint32_t *)(pvd + 156 + 10);
    while (*p == '\\' || *p == '/') p++;
    for (;;) {
        const char *end = p;
        int len, found = 0;
        uint32_t i;
        while (*end && *end != '\\' && *end != '/' && *end != ';') end++;
        len = (int)(end - p);
        if (size > sizeof(dir)) size = sizeof(dir);
        if (!iso_read_sectors(lba, (size + 2047) / 2048, dir)) return 0;
        for (i = 0; i < size;) {
            unsigned char n = dir[i];
            if (n == 0) { i = (i / 2048 + 1) * 2048; continue; }
            if (name_eq(dir + i + 33, dir[i + 32], p, len)) {
                lba = *(uint32_t *)(dir + i + 2);
                size = *(uint32_t *)(dir + i + 10);
                found = 1;
                break;
            }
            i += n;
        }
        if (!found) return 0;
        while (*end == ';' || (*end >= '0' && *end <= '9' && end > p && end[-1] == ';')) end++;
        if (*end == '\\' || *end == '/') { p = end + 1; continue; }
        *lba_out = lba;
        *size_out = size;
        return 1;
    }
}
