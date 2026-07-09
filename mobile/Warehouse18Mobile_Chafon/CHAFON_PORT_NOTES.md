# Warehouse18Mobile Chafon - Step 22

## Goal
Unify the Chafon Inventory by Location screen with the Zebra visual style.

## Changes
- Inventory screen now uses a light background like Zebra.
- Uses the W18 Inventory logo at the top.
- Shows the instruction text directly below the logo.
- Shows location barcode input in the same row as circular action buttons:
  - refresh/load location
  - submit inventory
  - clear
- Shows Loaded / Ok / Pending cards.
- Shows an item table with Item / Reads / Status.
- Keeps existing Chafon barcode input mechanism through a real Android EditText.
- Keeps existing backend/RFID logic unchanged.
- Adds a reload callback for the refresh button.
- Keeps Start/Stop RFID inventory available when expected items are loaded, because Chafon still needs an explicit RFID control.

## Notes
- No Android/Gradle compilation was attempted in this environment.
