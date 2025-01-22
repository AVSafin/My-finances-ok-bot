{ pkgs }: {
  deps = [
    pkgs.python311  # Python 3.11
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
  ];

  shellHook = ''
    pip install -r requirements.txt
  '';

  command = "python root/bot.py";  # Укажите правильный путь к точке входа
}