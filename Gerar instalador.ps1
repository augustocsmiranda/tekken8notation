  pyinstaller --clean --noconfirm `
  --name T8Notation `
  --onefile `
  --windowed `
  --icon ".\icon.ico" `
  --add-data ".\icon.ico;." `
  --add-data ".\assets;assets" `
  --add-data ".\data;data" `
  --add-data ".\char;char" `
  .\AppNovo5.py

  <#

  pyinstaller `
  --name T8Notation `
  --onefile `
  --windowed `
  --icon ".\icon.ico" `
  --add-data ".\assets;assets" `
  --add-data ".\assets_xbox;assets_xbox" `
  --add-data ".\assets_ps;assets_ps" `
  --add-data ".\data;data" `
  --add-data ".\char;char" `
  .\AppNovo5.py


  #>