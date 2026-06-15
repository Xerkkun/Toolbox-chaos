# Installation

Chaos Toolbox 0.1.0 is developed by Fer Moreno and distributed under the MIT License.

## Supported Platforms

- Windows 10/11 x64.
- macOS 13+ on x64 or arm64, built on macOS.
- Modern Linux x64 distributions with desktop Qt support.

## End Users

Install the platform package for your system:

- Windows: `chaos-toolbox-v0.1.0-windows-x64-setup.exe`.
- macOS: `.app` inside `chaos-toolbox-v0.1.0-macos-arm64.dmg` or matching architecture.
- Linux: `chaos-toolbox-v0.1.0-linux-x64.AppImage`, with optional `.deb`/`.rpm` when published.

Installing a newer version over an older version should not remove user configuration, generated results, configured external resources, or local galleries.

## Source Install

```powershell
python -m pip install -r requirements.txt
python main.py
```

Academic warning: numerical outputs are computational evidence, not automatic mathematical proof.
