#!/usr/bin/env bash
# install.sh : copie codescribe.py dans /usr/local/bin/codescribe

echo "Rend exécutable..."
chmod +x codescribe.py

echo "Copie dans /usr/local/bin..."
sudo cp codescribe.py /usr/local/bin/codescribe

echo "Installation terminée ! Vous pouvez taper : codescribe --help"
