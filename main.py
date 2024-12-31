import os
import sys
import threading
import hashlib
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import winreg
import shutil
from pathlib import Path
import pickle
import locale
import webbrowser


def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path.cwd()
    return base_path / relative_path

class Tooltip:
    def __init__(self, widget, text, image_path=None):
        self.widget = widget
        self.text = text
        self.image_path = Path.cwd() / 'repair' / image_path if image_path else None
        self.tooltip_window = None

        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window is not None:
            return

        # Позиция подсказки относительно курсора
        x = event.x_root + 10
        y = event.y_root + 20
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Фрейм для автоматической настройки размеров
        frame = tk.Frame(self.tooltip_window, background="gray99")
        frame.pack()

        # Если есть изображение, загружаем и добавляем его без фиксированной ширины
        if self.image_path and self.image_path.exists():
            image = PhotoImage(file=str(self.image_path))
            img_label = tk.Label(frame, image=image, anchor="center", pady=15, padx=10)
            img_label.image = image  # сохраняем ссылку на изображение
            img_label.pack(side="top")
            label = tk.Label(frame, text=self.text, background="gray99", relief="solid", borderwidth=0, pady=10, padx=10)
            label.pack(side="top")
        else:
            # Добавляем текст, который также будет подстраиваться по ширине
            label = tk.Label(
                frame,
                text=self.text,
                background="gray99",
                relief="solid",
                borderwidth=1,
                padx=5,
                pady=5
            )
            label.pack(side="top")

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Устранение неполадок")
        self.iconbitmap(resource_path("akashi.ico"))
        self.grid()
        self.resizable(False, False)
        self.repair_dir = Path.cwd() / 'repair'
        self.create_widgets()

    def create_widgets(self):
        info_label = ttk.Label(self, text="Данная утилита поможет вам обнаружить и устранить возможные неполадки с установленной игрой.")
        info_label.pack(pady=10, padx=20)

        # Кнопка для проверки целостности файлов
        self.check_integrity_button = ttk.Button(self, text="Проверить целостность файлов", command=self.check_integrity)
        self.check_integrity_button.pack(pady=5)
        Tooltip(self.check_integrity_button, "Если игра не запускается или некорректно работает, есть смысл проверить, все ли файлы целы.\nЭта опция запускает проверку целостности всех файлов, сравнивая их по хеш-сумме MD5.\nСкорость проверки зависит от скорости диска.")

        # Кнопка для проверки шрифта
        self.check_font_button = ttk.Button(self, text="Починить отображение текста (крякозябры в игре)", command=self.fix_font)
        self.check_font_button.pack(pady=5)
        Tooltip(self.check_font_button, "Для корректного отображения русского текста игре требуется специальный шрифт.\nЕсли текст в игре выглядит так же некорректно, как на изображении, эта опция установит необходимый шрифт.\nТакже вы можете посмотреть и установить шрифт (YasuSakuuta.ttf) самостоятельно, он находится в папке 'repair'.", image_path=resource_path("img/font_missing.png"))

        # Кнопка для проверки локали
        self.check_locale_button = ttk.Button(self, text="Починить заголовок окна", command=self.fix_window_title)
        self.check_locale_button.pack(pady=5)
        Tooltip(self.check_locale_button, "На отображение заголовка окна может влиять ваша локаль (см. изображение).\nДанный пункт проверяет локаль и в случае необходимости заменяет необходимый файл движка.\nЕсли не сработало, можете сами скопировать файл 'ipl._bp' из папки 'repair' в папку с игрой с заменой.", image_path=resource_path("img/bad_ipl.png"))

        # Кнопка для проверки пути
        self.check_path_button = ttk.Button(self, text="Исправить 'error!!' при запуске", command=self.fix_path)
        self.check_path_button.pack(pady=5)
        Tooltip(self.check_path_button, "Помогает исправить ошибку (см. примерное изображение), связанную с некорректным путём к главному исполняемому файлу.", image_path=resource_path("img/bad_path.png"))

        # Кнопка для проверки всего
        self.check_all_button = ttk.Button(self, text="Проверить всё", command=self.check_all)
        self.check_all_button.pack(pady=5)
        Tooltip(self.check_all_button,
                "Проверяет все пункты.\nНе рекомендуется, так как вряд ли у вас сломано всё разом, и это может занять длительное время.")

        # Полоса прогресса
        self.progress = ttk.Progressbar(self, orient="horizontal", length=450, mode="determinate")
        self.progress.pack(pady=10)

        # Метка для отображения статуса
        self.status_label = ttk.Label(self, text="")
        self.status_label.pack()

        # Toggle button to show/hide info_label2
        self.toggle_button = ttk.Button(self, text="Ничего не работает", command=self.toggle_info_label2)
        self.toggle_button.pack(pady=10)

        self.info_label2 = ttk.Label(self,
                                     text="Важно понимать, что эта программа предназначена для выявления и исправления только самых вероятных проблем с установкой."
                                          "\nЕсли никакой из пунктов не смог решить вашу проблему, то, скорее всего, она связана конкретно с вашей системой и оборудованием."
                                          "\nВы можете предпринять следующие шаги, которые могут вам помочь:"
                                          "\n- Начисто переустановить игру (заново скачать установщик и выполнить установку)"
                                          "\n- Выполнить диагностику Windows (sfc, CCleaner, Advanced SystemCare, Windows Repair Toolbox и т.д)"
                                          "\n- Убедиться, что состояние вашего жёсткого диска или SSD в норме. (chkdsk, VictoriaHDD, CrystalDiskInfo и т.д.)"
                                          "\n- Переустановить Windows"
                                          "\n- Произвести полный осмотр компьютерных деталей с чисткой или заменить компьютер как таковой",
                                     justify='center',
                                     anchor='center')

    def toggle_info_label2(self):
        if self.info_label2.winfo_ismapped():
            # Скрыть info_label2
            self.info_label2.pack_forget()
            # Опционально изменить текст кнопки
            self.toggle_button.config(text="Ничего не работает")
        else:
            # Установить wraplength в соответствии с текущей шириной окна
            window_width = self.winfo_width()
            wrap_length = window_width - 20  # Учтём отступы
            self.info_label2.configure(wraplength=wrap_length)
            # Показать info_label2
            self.info_label2.pack(padx=10)
            # Опционально изменить текст кнопки
            self.toggle_button.config(text="Скрыть")

    def check_integrity(self):
        threading.Thread(target=self._check_integrity_thread).start()

    def _check_integrity_thread(self):
        self.perform_integrity_check()

    def perform_integrity_check(self):
        file_list = self.get_file_list()
        total_files = len(file_list)
        self.progress["maximum"] = total_files
        failed_files = []
        total_size = 0
        failed_size = 0

        for idx, (file_path, expected_hash, expected_size) in enumerate(file_list, 1):
            try:
                rel_file_path = file_path.relative_to(Path.cwd())
            except ValueError:
                rel_file_path = file_path
            self.status_label.config(text=f"Проверяется файл: {rel_file_path} ({idx}/{total_files})")
            self.progress["value"] = idx
            self.update_idletasks()


            total_size += expected_size

            if not file_path.exists():
                failed_files.append(str(rel_file_path))
                failed_size += expected_size  # Add expected size since the file is missing
                continue

            actual_hash = self.compute_file_hash(file_path)
            if actual_hash != expected_hash:
                failed_files.append(str(rel_file_path))
                failed_size += expected_size  # Add expected size of the failed file

        # messagebox.showinfo("Инфо", f'Общий размер: {total_size} \nБитый размер: {failed_size},\nРазница: {total_size - failed_size}')

        if failed_files:
            result = messagebox.askyesno(
            "Проверка целостности",
            "Следующие файлы не прошли проверку:\n"
            + "\n".join(failed_files)
            + "\n\nРекомендуется переустановить игру.\n"
              "Перейти на страницу скачивания?"
              "\n\nВы можете спасти сохранения, воспользовавшись\n"
              "соответствующей опцией деинсталятора, или вручную\n"
              "скопировав папку \"UserData\" и файл \"BGI.gdb\"\n"
              "из корня игры."
        )
            if result:
                webbrowser.open("https://yasuragivn.wordpress.com/sakura-no-uta/")  # Replace with actual link

        else:
            messagebox.showinfo("Проверка целостности", "Все файлы успешно прошли проверку.")

        self.status_label.config(text="")
        self.progress["value"] = 0

    def get_file_list(self):
        hash_file_path = resource_path("file_hashes.bin")
        file_hash_list_abs = []
        try:
            with open(hash_file_path, "rb") as f:
                file_hash_list = pickle.load(f)
            current_dir = Path.cwd()
            for rel_path_str, md5, file_size in file_hash_list:
                rel_path = Path(rel_path_str)
                file_path = current_dir / rel_path
                file_hash_list_abs.append((file_path, md5, file_size))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список файлов для проверки:\n{e}")
        return file_hash_list_abs

    def compute_file_hash(self, file_path):
        md5_hash = hashlib.md5()
        try:
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            return None

    def fix_font(self):
        font_name = "YasuSakuuta.ttf"
        if not self.is_font_installed(font_name):
            result = messagebox.askyesno("Шрифт не найден", f"Необходимый шрифт '{font_name}' не найден.\nУстановить его?")
            if result:
                self.install_font(font_name)
        else:
            messagebox.showinfo("Проверка шрифта", f"Шрифт '{font_name}' уже установлен.")

    def is_font_installed(self, font_name):
        # Проверяем наличие шрифта в системной папке Fonts
        fonts_dir = Path(os.environ['WINDIR']) / 'Fonts'
        font_files = [font.name.lower() for font in fonts_dir.iterdir()]
        return font_name.lower() in font_files

    def install_font(self, font_name):
        fonts_dir = Path(os.environ['WINDIR']) / 'Fonts'
        source_path = self.repair_dir / font_name
        dest_path = fonts_dir / font_name

        try:
            shutil.copyfile(source_path, dest_path)
            # Регистрация шрифта в реестре
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", 0, winreg.KEY_SET_VALUE | winreg.KEY_WRITE)
            winreg.SetValueEx(key, font_name, 0, winreg.REG_SZ, font_name)
            winreg.CloseKey(key)

            # Обновляем кэш шрифтов
            ctypes.windll.gdi32.AddFontResourceW(str(dest_path))
            ctypes.windll.user32.SendMessageW(0xffff, 0x001D, 0, 0)

            messagebox.showinfo("Установка шрифта", f"Шрифт '{font_name}' успешно установлен.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось установить шрифт:\n{e}")

    def get_locale_info(self):
        lang_id = ctypes.windll.kernel32.GetSystemDefaultLangID()
        primary_lang_id = lang_id & 0x3ff
        locale_name = locale.windows_locale.get(lang_id, "Неизвестная")
        codepage = ctypes.windll.kernel32.GetACP()
        encoding = 'cp' + str(codepage)
        return lang_id, primary_lang_id, locale_name, codepage, encoding

    def fix_window_title(self):
        lang_id, primary_lang_id, locale_name, _, _ = self.get_locale_info()
        LOCALE_RUSSIAN = [
            0x19,  # Русский
            0x22,  # Украинский
            0x02,  # Болгарский
            0x1a,  # Сербский (кириллица)
            0x2f,  # Македонский
            0x50,  # Монгольский (кириллица)
            0x23,  # Белорусский
            0x43,  # Узбекский (кириллица)
            0x40  # Киргизский (кириллица)
        ]

        # LANG_RUSSIAN = 0x19
        LOCALE_JAPANESE = 0x11

        jp_ipl_md5_hash = "31888256646e301b74f8d7ce744eb0b8"
        ru_ipl_md5_hash = "3190ae2bf6ff7ec09869cebb9bd102b8"

        current_dir = Path.cwd()
        curr_md5_hash = self.compute_file_hash(current_dir / "ipl._bp")

        if primary_lang_id in LOCALE_RUSSIAN:
            if curr_md5_hash == ru_ipl_md5_hash:
                messagebox.showinfo("Проверка локали", f'Ваша системная локаль совместима с текущей\nконфигурацией!\nНикаких дополнительных действий не требуется.')
            else:
                result = messagebox.askyesno("Несоответствие локали", f'Ваша локаль: "{locale_name}" и текущий конфигурационный файл "{(current_dir / "ipl._bp").name}" не совместимы. Заменить этот файл на нужный?')
                if result:
                    source_file = self.repair_dir / "ipl_ru._bp"
                    dest_file = current_dir / "ipl._bp"
                    try:
                        shutil.copyfile(source_file, dest_file)
                        messagebox.showinfo("Починка локали", f'Файл "{source_file.name}" скопирован в "{current_dir} "как "{dest_file.name}".')
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")

        elif primary_lang_id == LOCALE_JAPANESE:
            if curr_md5_hash == jp_ipl_md5_hash:
                messagebox.showinfo("Проверка локали", f'Ваша системная локаль совместима с текущей\nконфигурацией!\nНикаких дополнительных действий не требуется.')
            else:
                result = messagebox.askyesno("Несоответствие локали", f'Ваша локаль: "{locale_name}" и текущий конфигурационный файл "{(current_dir / "ipl._bp").name}" не совместимы. Заменить этот файл на\nподходящий?')
                if result:
                    source_file = self.repair_dir / "ipl_jp._bp"
                    dest_file = current_dir / "ipl._bp"
                    try:
                        shutil.copyfile(source_file, dest_file)
                        messagebox.showinfo("Починка локали", f'Файл "{source_file.name}" скопирован в "{current_dir} "как "{dest_file.name}".')
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")

        else:
            result = messagebox.askyesno("Непподдерживаемая локаль",
                                         f'Ваша локаль: "{locale_name}" отсутствует в списке поддерживаемых напрямую, но вы можете воспользоваться универсальным файлом.\nПодставить универсальный файл?')
            if result:
                source_file = self.repair_dir / "ipl._bp"
                dest_file = current_dir / "ipl._bp"
                try:
                    shutil.copyfile(source_file, dest_file)
                    messagebox.showinfo("Починка локали",
                                        f'Файл "{source_file.name}" скопирован в "{current_dir} "как "{dest_file.name}".')
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")


    def is_path_valid(self, path):
        _, _, _, codepage, encoding = self.get_locale_info()
        invalid_components = []


        path_obj = Path(path)
        for part in path_obj.parts:
            try:
                part.encode(encoding)
            except UnicodeEncodeError:
                invalid_components.append(part)
        return True if not invalid_components else invalid_components


    def fix_path(self):

        message = ("Если игра не запускается с ошибкой типа 'error!!', это\nозначает, что путь к игре содержит символы,\nнесовместимые с вашей системной локалью. Важно\nпонимать, что это распространяется на полный путь к\nигре, а не только на название её папки."
                    "\nИсправить эту ошибку можно несколькими способами:\n1. Убедиться, что в пути нет никаких других символов,\nкроме английских букв и цифр, например:\n'D:\\Games02\\Sakura no Uta'."
                    "\n2. Сменить системную локаль на ту, что поддерживает\nсимволы,которые у вас в пути. Например, если вы хотите,\nчтобы игра запускалась из папки 'サクラノ詩', вам\nпонадобится сменить локаль на японскую."
                    "\n3. Запустить 'Стих Сакуры.exe' с помощью эмулятора\nлокали (applocale, ntlea, Locale-Emulator), выбрав локаль,\nсимволы которой вас интересуют."
                    "\n4. Если вы нажмёте 'Да', программа проверит путь и\nпопытается найти символы, мешающие запуску.")

        result = messagebox.askyesno("Проверка пути", message)
        if result:
            current_dir = Path.cwd()
            program_path = os.path.abspath(current_dir)
            lang_id, _, _, codepage, encoding = self.get_locale_info()
            locale_name = locale.windows_locale.get(lang_id, "Неизвестная")

            invalid_components = self.is_path_valid(program_path)
            if invalid_components is True:
                messagebox.showinfo("Проблем не обнаружено",
                                    f"Путь содержит только допустимые символы для вашей\nлокали и кодировки ({locale_name}, {encoding}).")
            else:
                invalid_components_str = '\n'.join(invalid_components)
                path_message = (
                    f"Путь к игре: {program_path}\n"
                    f"Системная локаль: {locale_name}\n"
                    f"Кодировка: {encoding}\n"
                    f"Потенциально недопустимые элементы пути:\n{invalid_components_str}\n"
                    f"----------------------------------------------------------------"
                    f"Уберите их или замените на корректные, после чего попробуйте заново запустить игру."
                )
                messagebox.showwarning("Обнаружены недопустимые символы!", path_message)

    def check_all(self):
        result = messagebox.askyesno("Подтверждение",
                                     "Вы уверены, что хотите выполнить все пункты?\nРекомендуется исправлять конкретные ошибки.")
        if result:
            threading.Thread(target=self._check_all_thread).start()

    def _check_all_thread(self):
        total_steps = 4
        self.status_label.config(text="Проверяется целостность файлов")
        self.perform_integrity_check()

        # После проверки целостности файлов сбрасываем полосу прогресса
        self.progress["maximum"] = total_steps
        self.progress["value"] = 1
        self.update_idletasks()

        self.status_label.config(text="Проверяется шрифт")
        self.fix_font()
        self.progress["value"] = 2
        self.update_idletasks()

        self.status_label.config(text="Проверяется заголовок окна")
        self.fix_window_title()
        self.progress["value"] = 3
        self.update_idletasks()

        self.status_label.config(text="Проверяется путь")
        self.fix_path()
        self.progress["value"] = 4
        self.update_idletasks()

        self.status_label.config(text="Проверка завершена")
        self.progress["value"] = 0
        self.update_idletasks()




if __name__ == "__main__":
    app = App()
    app.mainloop()
