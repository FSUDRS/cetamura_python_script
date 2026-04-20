# Cetamura Batch Ingest Tool - Build Summary

| Platform | Script | Output |
|----------|--------|--------|
| Windows | `scripts/build/build_exe.ps1` | `dist/CetamuraBatchIngest.exe` |
| macOS | `scripts/build/build_exe_macos.sh` | `dist/CetamuraBatchIngest` |
| Linux | `scripts/build/build_cross_platform.sh` | `dist/CetamuraBatchIngest` |

## Common Commands

Windows:

```powershell
.\scripts\build\build_exe.ps1 -InstallDependencies
```

macOS:

```bash
./scripts/build/build_exe_macos.sh --install-dependencies
```

Linux:

```bash
./scripts/build/build_cross_platform.sh --install-dependencies
```

## Package Command

```powershell
.\scripts\build\create_dist_package.ps1 -Version 1.3.0
```
