# Assembled Dependencies

This file records the dependency surfaces currently assembled under `deps/`.
The root coordinates these projects; their Git histories remain independent.

| Surface | Location | Source | Revision at assembly |
| --- | --- | --- | --- |
| Pyzo | `deps/pyzo` | `https://github.com/pyzo/pyzo.git` | `26c2c32778dddf8fca3c1a44112941b22f075264` |
| QtADS / PyQtAds | `deps/qt-advanced-docking-system` | `https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System.git` | `812ce784ce9ee2eba89d6a91e46cc4bcc86e9fd0` |
| PySide6-QtAds | `deps/pyside6-qtads` | `https://github.com/mborgerson/pyside6_qtads.git` | local `c77dd6e`, embedding local QtADS `0edfe64` |
| toas | `deps/toas` | local working tree: `/Users/tim/Documents/Projects/toas` (`https://github.com/joevalleyfield/toas.git`) | `919bf00a987c8049a54ce8706edbe5c38ad4776d` |
| rhizome | `deps/rhizome` | local working tree: `/Users/tim/Documents/Projects/rhizome` (`https://github.com/joevalleyfield/rhizome.git`) | `36beb4849cef8211203bead8390021e6689c88f9` |

## Assembly status

- Pyzo, QtADS, and the separate PySide6 binding were cloned from their public
  upstream repositories.
- toas and rhizome are exposed through symlinks to the existing local working
  trees so their current development state is not copied or detached.
- Pyzo, QtADS, and PySide6-QtAds now have local experiment commits in their own
  histories; the root records and validates those independently owned changes.
- Dependency revisions are descriptive assembly evidence, not permanent pins.

## Compatibility note

Canonical QtADS carries SIP/PyQt bindings in-tree, while Pyzo's exercised
runtime uses the separate Shiboken-based `PySide6-QtAds` package. That binding
embeds QtADS as a submodule. A macOS source build also needs a standalone Qt SDK
matching PySide; the Experiment 011 build used Qt 6.11.1 from `aqtinstall` and
`CMAKE_PREFIX_PATH=/tmp/qt/6.11.1/macos`.
