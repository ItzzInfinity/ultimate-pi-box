# Ultimate Pi Box v2

This directory is the clean rewrite area for the project described in [FSD.md](../FSD.md).

## Purpose

- Keep the old prototype files untouched.
- Build the final app in a modular layout.
- Separate shared runtime code, component code, data files, and documentation.

## Current Structure

- `main.py`
  Entry point for the service-friendly application.
- `menu.json`
  Menu definition used by the main controller.
- `requirements.txt`
  Python dependencies expected on the Raspberry Pi.
- `progress.md`
  Development log for this rewrite.
- `data/`
  Runtime assets such as radio station CSV files, YouTube sources, and local music folders.
- `ultimate_pi_box/`
  Shared runtime package.

## Status

The shared runtime files have been created:

- configuration loading
- hardware abstraction
- rendering helpers
- VLC helper
- basic application shell

The component package directories and their documentation are defined next so each feature has a clear home before implementation.
