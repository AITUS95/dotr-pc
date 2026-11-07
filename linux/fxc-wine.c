// Minimal fxc replacement for Wine: compiles one HLSL file with D3DCompile and writes a -Fh style header.
#define COBJMACROS
#include <windows.h>
#include <d3dcompiler.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char *winpath(const char *p) {
    char *o = malloc(strlen(p) + 4);
    if (p[0] == '/') { strcpy(o, "Z:"); strcat(o, p); } else strcpy(o, p);
    for (char *c = o; *c; c++) if (*c == '/') *c = '\\';
    return o;
}
int main(int argc, char **argv) {
    const char *target = "cs_5_0", *entry = "main", *var = "g_main", *out = NULL, *in = NULL;
    D3D_SHADER_MACRO macros[16]; int nm = 0; UINT flags = D3DCOMPILE_OPTIMIZATION_LEVEL3;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-T")) target = argv[++i];
        else if (!strcmp(argv[i], "-E")) entry = argv[++i];
        else if (!strcmp(argv[i], "-Vn")) var = argv[++i];
        else if (!strcmp(argv[i], "-Fh")) out = argv[++i];
        else if (!strncmp(argv[i], "-D", 2)) {
            char *d = _strdup(argv[i] + 2), *eq = strchr(d, '=');
            if (eq) *eq++ = 0;
            macros[nm].Name = d; macros[nm].Definition = eq ? eq : "1"; nm++;
        }
        else if (!strcmp(argv[i], "-Gis")) flags |= D3DCOMPILE_IEEE_STRICTNESS;
        else if (argv[i][0] == '-') { /* -nologo -O3 ignored */ }
        else in = argv[i];
    }
    macros[nm].Name = NULL; macros[nm].Definition = NULL;
    if (!in || !out) { fprintf(stderr, "usage\n"); return 2; }
    char *win = winpath(in), *wout = winpath(out);
    WCHAR wi[1024]; MultiByteToWideChar(CP_ACP, 0, win, -1, wi, 1024);
    ID3DBlob *code = NULL, *err = NULL;
    HRESULT hr = D3DCompileFromFile(wi, macros, D3D_COMPILE_STANDARD_FILE_INCLUDE, entry, target, flags, 0, &code, &err);
    if (err) fwrite(ID3D10Blob_GetBufferPointer(err), 1, ID3D10Blob_GetBufferSize(err), stderr);
    if (FAILED(hr)) { fprintf(stderr, "D3DCompileFromFile failed 0x%08lx\n", hr); return 1; }
    const unsigned char *b = ID3D10Blob_GetBufferPointer(code); SIZE_T n = ID3D10Blob_GetBufferSize(code);
    FILE *f = fopen(wout, "w"); if (!f) { fprintf(stderr, "cannot write %s\n", wout); return 1; }
    fprintf(f, "const BYTE %s[] =\n{\n", var);
    for (SIZE_T i = 0; i < n; i++) fprintf(f, "%s%4u,", (i % 6 == 0) ? "    " : " ", b[i]), (i % 6 == 5) ? fputc('\n', f) : 0;
    fprintf(f, "\n};\n");
    fclose(f); return 0;
}
