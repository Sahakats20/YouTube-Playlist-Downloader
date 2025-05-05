
### 3. Обновленный `install.sh`
```bash
#!/bin/bash
# Скрипт установки зависимостей для YouTube Playlist Downloader

echo "Установка зависимостей для YouTube Playlist Downloader..."
echo ""

# Проверка Python3
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не установлен"
    echo "Установите Python3:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  Fedora: sudo dnf install python3"
    echo "  Arch Linux: sudo pacman -S python"
    exit 1
fi

# Установка pip и venv
if ! command -v pip3 &> /dev/null; then
    echo "Установка pip..."
    sudo apt install python3-pip python3-venv || sudo dnf install python3-pip || sudo pacman -S python-pip
fi

# Создание виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка Python-зависимостей
echo "Установка Python-зависимостей..."
pip install -r requirements.txt

# Установка системных зависимостей
echo "Установка системных зависимостей..."
sudo apt install ffmpeg python3-tk xclip || sudo dnf install ffmpeg python3-tkinter xclip || sudo pacman -S ffmpeg tk xclip

echo ""
echo "Установка завершена!"
echo "Запустите программу: python3 Music.py"
