# BT Settings Component

## Scope

- show Bluetooth adapter state
- toggle adapter power
- toggle discoverable mode
- browse paired devices
- connect or disconnect selected device

## Planned Inputs

- `bluetoothctl show`
- `bluetoothctl paired-devices`
- `bluetoothctl info`

## Planned UI States

- adapter settings menu
- paired device list
- connection status message

## Notes

- This component handles adapter setup; media transport control belongs in `connect_phone`.
