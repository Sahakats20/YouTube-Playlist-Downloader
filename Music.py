import os
import threading
import traceback
from yt_dlp import YoutubeDL
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pyperclip
import sys
import subprocess
import browser_cookie3

# Проверяем, не запущен ли скрипт из терминала
if sys.stdout.isatty():
    # Запускаем новую копию без терминала
    subprocess.Popen(["python3", __file__], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(0)

# Переменные для отслеживания состояния загрузки
successful_downloads = 0
failed_downloads = 0
current_song = ""
download_thread = None
is_downloading = False

def check_dependencies():
    """Проверка наличия необходимых зависимостей"""
    try:
        import yt_dlp
        import pyperclip
        import browser_cookie3
    except ImportError as e:
        messagebox.showerror("Ошибка зависимостей", 
                           f"Отсутствует необходимая библиотека: {e}.\n"
                           "Установите необходимые библиотеки:\n"
                           "pip install yt-dlp pyperclip browser-cookie3")
        return False
    return True

def download_playlist(playlist_url, download_path="downloads"):
    """
    Загрузить музыкальный плейлист с YouTube.
    """
    global successful_downloads, failed_downloads, current_song, is_downloading
    
    is_downloading = True
    button_download.config(state=tk.DISABLED)
    button_stop.config(state=tk.NORMAL)
    
    try:
        # Конвертируем ссылку music.youtube.com в обычную
        if 'music.youtube.com' in playlist_url:
            playlist_url = playlist_url.replace('music.youtube.com', 'www.youtube.com')
            log_message("Конвертирована ссылка YouTube Music в обычную YouTube ссылку")
        
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        
        log_message(f"Начинаем загрузку с {playlist_url}")
        
        # Получаем cookies из браузера
        try:
            cookies = browser_cookie3.load(domain_name='youtube.com')
            cookies_dict = {c.name: c.value for c in cookies}
            log_message("Успешно загружены cookies из браузера")
        except Exception as e:
            log_message(f"Ошибка загрузки cookies: {e}")
            cookies_dict = None
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'noplaylist': False,
            'extract_flat': False,
            'geo_bypass': True,
            'ignoreerrors': True,
            'progress_hooks': [progress_hook],
        }
        
        # Добавляем cookies если они есть
        if cookies_dict:
            ydl_opts['cookies'] = cookies_dict
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])
            
        log_message(f"Загрузка завершена. Успешно: {successful_downloads}, Ошибок: {failed_downloads}")
    
    except Exception as e:
        error_details = traceback.format_exc()
        log_message(f"Произошла ошибка: {e}\n{error_details}")
        messagebox.showerror("Ошибка загрузки", f"Произошла ошибка: {e}")
    
    finally:
        is_downloading = False
        button_download.config(state=tk.NORMAL)
        button_stop.config(state=tk.DISABLED)

def progress_hook(d):
    """Функция отслеживания прогресса загрузки."""
    global successful_downloads, failed_downloads, current_song
    
    if not is_downloading:
        return
    
    filename = d.get('filename', '').split(os.sep)[-1] if 'filename' in d else 'Неизвестный файл'
    
    if d['status'] == 'downloading':
        current_song = filename
        if '_percent_str' in d:
            percent = d['_percent_str']
            speed = d.get('_speed_str', 'неизвестно')
            eta = d.get('_eta_str', 'неизвестно')
            status_text = f"Загружается: {filename}\nПрогресс: {percent} ({speed}, ETA: {eta})"
            update_status_threadsafe(status_text)
            
    elif d['status'] == 'finished':
        log_message(f"Загружен: {filename}")
        successful_downloads += 1
        update_statistics_threadsafe()
        
    elif d['status'] == 'error':
        log_message(f"Ошибка загрузки: {filename}")
        failed_downloads += 1
        update_statistics_threadsafe()

def update_status_threadsafe(text):
    """Безопасное обновление статуса из другого потока"""
    if root.winfo_exists():
        root.after(0, lambda: label_status.config(text=text))

def update_statistics_threadsafe():
    """Безопасное обновление статистики из другого потока"""
    if root.winfo_exists():
        root.after(0, lambda: label_stats.config(text=f"Загружено: {successful_downloads} файлов | Ошибок: {failed_downloads}"))

def log_message(message):
    """Добавляет сообщение в лог"""
    if root.winfo_exists():
        root.after(0, lambda: text_log.insert(tk.END, f"{message}\n"))
        root.after(0, lambda: text_log.see(tk.END))

def browse_folder():
    """Открывает диалоговое окно для выбора папки сохранения"""
    folder = filedialog.askdirectory()
    if folder:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, folder)

def start_download():
    """Функция для начала загрузки плейлиста"""
    global successful_downloads, failed_downloads, download_thread
    
    successful_downloads = 0
    failed_downloads = 0
    
    playlist_url = entry_url.get().strip()
    download_path = entry_path.get().strip()
    
    if not playlist_url:
        messagebox.showerror("Ошибка", "Пожалуйста, введите ссылку на плейлист!")
        return
    
    if not download_path:
        download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        entry_path.delete(0, tk.END)
        entry_path.insert(0, download_path)
        log_message(f"Используется путь по умолчанию: {download_path}")
    
    download_thread = threading.Thread(target=download_playlist, args=(playlist_url, download_path))
    download_thread.daemon = True
    download_thread.start()

def stop_download():
    """Останавливает текущую загрузку"""
    global is_downloading
    if is_downloading:
        is_downloading = False
        log_message("Загрузка остановлена пользователем")
        button_download.config(state=tk.NORMAL)
        button_stop.config(state=tk.DISABLED)

def paste_from_clipboard():
    """Вставляет ссылку из буфера обмена"""
    try:
        clipboard_content = pyperclip.paste()
        entry_url.delete(0, tk.END)
        entry_url.insert(0, clipboard_content)
    except Exception as e:
        messagebox.showerror("Ошибка буфера обмена", f"Не удалось получить содержимое буфера обмена: {e}")

def on_closing():
    """Обработчик закрытия окна"""
    global is_downloading
    if is_downloading:
        if messagebox.askokcancel("Завершение работы", "Загрузка активна. Вы уверены, что хотите выйти?"):
            is_downloading = False
            root.destroy()
    else:
        root.destroy()

# Проверяем зависимости перед запуском
if not check_dependencies():
    sys.exit(1)

# Создаем графический интерфейс
root = tk.Tk()
root.title("YouTube Playlist Downloader")
root.geometry("700x550")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Фрейм для URL и кнопок
frame_top = tk.Frame(root)
frame_top.pack(fill=tk.X, padx=10, pady=10)

label_url = tk.Label(frame_top, text="Ссылка на плейлист YouTube:")
label_url.grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_url = tk.Entry(frame_top, width=50)
entry_url.grid(row=0, column=1, padx=5, pady=5, sticky="we")
button_paste = tk.Button(frame_top, text="Вставить", command=paste_from_clipboard)
button_paste.grid(row=0, column=2, padx=5, pady=5)

label_path = tk.Label(frame_top, text="Путь для сохранения:")
label_path.grid(row=1, column=0, padx=5, pady=5, sticky="w")
entry_path = tk.Entry(frame_top, width=50)
entry_path.grid(row=1, column=1, padx=5, pady=5, sticky="we")
button_browse = tk.Button(frame_top, text="Обзор...", command=browse_folder)
button_browse.grid(row=1, column=2, padx=5, pady=5)

frame_top.columnconfigure(1, weight=1)

# Кнопки управления
frame_buttons = tk.Frame(root)
frame_buttons.pack(fill=tk.X, padx=10, pady=5)

button_download = tk.Button(frame_buttons, text="Загрузить", command=start_download, 
                          bg="green", fg="white", pady=5, padx=20)
button_download.pack(side=tk.LEFT, padx=5)

button_stop = tk.Button(frame_buttons, text="Остановить", command=stop_download, 
                      bg="red", fg="white", pady=5, padx=20, state=tk.DISABLED)
button_stop.pack(side=tk.LEFT, padx=5)

# Статус загрузки
label_status = tk.Label(root, text="Ожидание начала загрузки...", justify="left", pady=5)
label_status.pack(fill=tk.X, padx=10, pady=5)

# Статистика
label_stats = tk.Label(root, text="Загружено: 0 файлов | Ошибок: 0", justify="left")
label_stats.pack(fill=tk.X, padx=10, pady=5)

# Лог операций
frame_log = tk.LabelFrame(root, text="Журнал событий")
frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

text_log = scrolledtext.ScrolledText(frame_log, height=10)
text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Автоматическая настройка при запуске
try:
    paste_from_clipboard()
except:
    pass

default_download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
entry_path.insert(0, default_download_path)

log_message("Программа готова к работе")
log_message("Для работы требуется библиотека yt-dlp и FFmpeg для конвертации аудио")

root.mainloop()
