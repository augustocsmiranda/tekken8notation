import os
import csv
import ctypes
import re
import tkinter as tk  # messagebox e utilitários
from tkinter import messagebox
from PIL import Image
from idlelib.tooltip import Hovertip
import customtkinter as ctk

# ------------------ Paleta / Tema ------------------
BG      = "#1a1038"
CARD    = "#241645"
BORDER  = "#352866"
TEXT    = "#e6e6ff"
SUBTXT  = "#9aa3c7"
ACCENT  = "#7c3aed"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Grade da palette
PALETTE_MAX_COLS    = 8    # R1..R4 = 8 por linha
SECONDARY_MAX_COLS  = 12   # R5+    = 12 por linha (costurando)

# Auto-ajuste da palette
ICON_MIN = 24
ICON_MAX = 32
ICON_GAP = 6


class ScrollableFrame(ctk.CTkFrame):
    """Paleta com rolagem vertical para muitos ícones (só vertical)."""
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=CARD)
        self.vsb = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.inner = ctk.CTkFrame(self.canvas, fg_color="transparent")

        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))


class VirtualKeyboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ---- Janela / tema ----
        self.title("Notation Image Generator")
        self.geometry("1600x900")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # AppID + ícone (Windows)
        try:
            myappid = 'mycompany.myproduct.subproduct.version'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
        icon_path = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # ---- Dados / estado ----
        self.assets_types = [
            ("T8 Default", "assets"),
            ("Xbox", "assets_xbox"),
            ("PlayStation", "assets_ps"),
        ]
        self.all_characters = [
            "None","Alisa","Asuka","Azucena","Bryan","Claudio","Clive","Devil Jin","Dragunov","Eddy",
            "Fahkumram","Feng","Heihachi","Hwoarang","Jack 8","Jin","Jun","Kazuya","King","Kuma",
            "Lars","Law","Lee","Leo","Leroy","Lidia","Lili","Nina","Panda","Paul","Raven","Reina",
            "Shaheen","Steve","Victor","Xiaoyu","Yoshimitsu","Zafina",
        ]

        # CSVs
        movedict_csv = os.path.join(BASE_DIR, "data", "MoveDictModified.csv")
        with open(movedict_csv, mode='r', encoding='utf-8') as file:
            self.MoveDict = [row for row in csv.DictReader(file, delimiter=';')]

        charmoves_csv = os.path.join(BASE_DIR, "data", "CharMoves.csv")
        with open(charmoves_csv, mode='r', encoding='utf-8') as file:
            self.CharMoves = [row for row in csv.DictReader(file, delimiter=';')]

        # Mapas para lookup O(1)
        self.move_to_image = {row["Move"].upper(): row["Image"] for row in self.MoveDict}
        self.move_to_name  = {row["Move"].upper(): row["Name"]  for row in self.MoveDict}

        # Estado dinâmico
        self.selected_images_lines = []          # linhas selecionadas no preview
        self.include_dark = tk.BooleanVar(value=False)
        self.images_folder_var = tk.StringVar(value="T8 Default")
        self.character_var = tk.StringVar(value="None")
        self.selected_assets = self.assets_types[0][1]
        self.character_image_buttons = []
        self.tooltips = []

        # cache de imagens (CTkImage) para HiDPI
        self._img_cache = {}
        self.current_icon_size = 32
        self._relayout_id = None

        # Flicker control
        self._suspend_relayout = False
        self._last_palette_width = 0

        # widgets
        self.image_frame = None
        self.preview_frame = None
        self.string_input = None

        # ---- CONSTRÓI UI ----
        self._build_header()
        self._build_input()
        self._build_center()

        # liga traces
        self.images_folder_var.trace_add("write", self.load_and_reload_assets)
        self.character_var.trace_add("write", self.update_character_images)

        # carrega paleta e preview inicial
        self._load_and_group_images()
        self.update_character_images()
        self._update_selected_images_display()
        self._update_preview_field()

        # atalho para dicas
        self.bind("<F1>", lambda e: self.show_tips())

        # inicia auto-resize da palette
        self.after(120, self._relayout_palette)

    # ---------- Helpers de UI ----------
    def _card(self, parent, pad=(10,10)):
        outer = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        inner.grid(row=0, column=0, sticky="nsew", padx=pad[0], pady=pad[1])
        return outer, inner

    def _title(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=("Segoe UI", 18, "bold"), text_color=TEXT)

    def _divider(self, parent):
        return ctk.CTkFrame(parent, fg_color=BORDER, height=2, corner_radius=1)

    def _field(self, parent, label, widget_cls, **kwargs):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=label, text_color=SUBTXT).grid(row=0, column=0, sticky="w", pady=(0,2))
        w = widget_cls(f, **kwargs)
        w.grid(row=1, column=0, sticky="ew")
        f.grid_columnconfigure(0, weight=1)
        return f

    # ---------- Header ----------
    def _build_header(self):
        header_card, header = self._card(self, pad=(16,12))
        header_card.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))
        header.grid_columnconfigure(0, weight=1)

        left  = ctk.CTkFrame(header, fg_color="transparent")
        right = ctk.CTkFrame(header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(2,0))
        right.grid(row=0, column=1, sticky="e")

        # Character + retrato
        self._field(
            left, "Character",
            ctk.CTkComboBox,
            values=self.all_characters, width=220,
            variable=self.character_var
        ).grid(row=0, column=0, padx=(0,12), sticky="ew")

        self.character_image_button = ctk.CTkButton(
            left, state="disabled", text="", width=48, height=48
        )
        self.character_image_button.grid(row=0, column=1, padx=(6,0))

        # Ícones de ação no topo (com tooltip)
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=0, column=0)

        # ↺ Backspace
        btn_back = ctk.CTkButton(
            actions, text="↺", width=38, height=38,
            fg_color="#ff9f1c", hover_color="#ff9f1c", corner_radius=12,
            command=self.remove_last_image
        )
        btn_back.grid(row=0, column=0, padx=6)
        Hovertip(btn_back, "Backspace", hover_delay=300)

        # 🗑 Clear
        btn_clear = ctk.CTkButton(
            actions, text="🗑", width=38, height=38,
            fg_color="#ef233c", hover_color="#ef233c", corner_radius=12,
            command=self.clear_selected_images
        )
        btn_clear.grid(row=0, column=1, padx=6)
        Hovertip(btn_clear, "Clear", hover_delay=300)

        # ⬇ Salvar PNG
        btn_save = ctk.CTkButton(
            actions, text="⬇", width=38, height=38,
            fg_color="#2ec4b6", hover_color="#2ec4b6", corner_radius=12,
            command=self.export_images
        )
        btn_save.grid(row=0, column=2, padx=6)
        Hovertip(btn_save, "Salvar PNG", hover_delay=300)

        # 💡 Dicas
        btn_tips = ctk.CTkButton(
            actions, text="💡", width=38, height=38,
            fg_color="#7c3aed", hover_color="#6d28d9", corner_radius=12,
            command=self.show_tips
        )
        btn_tips.grid(row=0, column=3, padx=6)
        Hovertip(btn_tips, "Dicas de uso (F1)", hover_delay=300)

    # ---------- Entrada ----------
    def _build_input(self):
        card, inner = self._card(self)
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,10))
        inner.grid_columnconfigure(0, weight=1)

        self.string_input = ctk.CTkEntry(inner, placeholder_text="Digite sua notação aqui...",
                                         height=56, corner_radius=12)
        self.string_input.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.string_input.bind("<KeyRelease>", self.process_string_input)
        self._debounce_id = None

    # ---------- Centro ----------
    def _build_center(self):
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)
        center.grid_columnconfigure(0, weight=1, uniform="col")
        center.grid_columnconfigure(1, weight=1, uniform="col")
        center.grid_rowconfigure(0, weight=1)

        # LEFT: Palette
        left_card, left_inner = self._card(center)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=(0,8))
        self._title(left_inner, "Palette").grid(row=0, column=0, sticky="w", padx=10, pady=(10,8))

        self.palette_scroll = ScrollableFrame(left_inner)
        self.palette_scroll.grid(row=1, column=0, sticky="nsew", padx=10)
        left_inner.grid_rowconfigure(1, weight=1)
        left_inner.grid_columnconfigure(0, weight=1)
        self.image_frame = self.palette_scroll.inner

        # Reage somente a resize real da janela (evita flicker)
        self.bind("<Configure>", self._on_window_resize)

        # RIGHT: Preview
        right_card, right_inner = self._card(center)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=(0,8))
        self._title(right_inner, "Preview").grid(row=0, column=0, sticky="w", padx=10, pady=(10,8))

        self.preview_frame = ctk.CTkFrame(right_inner, fg_color=CARD)
        self.preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,8))
        right_inner.grid_rowconfigure(1, weight=1)
        right_inner.grid_columnconfigure(0, weight=1)

        footer = ctk.CTkLabel(self, text="Tekken 8 Notation Generator • Create and share your combo notations",
                              text_color=SUBTXT)
        footer.grid(row=3, column=0, pady=(2, 12))

    # ---------- Imagens (CTkImage) ----------
    def _get_ctk_image(self, path, size):
        key = (path, size)
        if key in self._img_cache:
            return self._img_cache[key]
        if not os.path.exists(path):
            return None
        pil = Image.open(path)
        cimg = ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
        self._img_cache[key] = cimg
        return cimg

    # ---------- Entrada: parsing com debounce ----------
    def process_string_input(self, event=None):
        if getattr(self, "_debounce_id", None):
            try:
                self.after_cancel(self._debounce_id)
            except Exception:
                pass
        self._debounce_id = self.after(120, self._parse_and_update)

    def _parse_and_update(self):
        input_string = self.string_input.get().upper().strip()
        line_sequences = [seg for seg in (s.strip() for s in input_string.split(',')) if seg]

        new_lines = []
        for line in line_sequences:
            tokens = [t for t in re.split(r'[\s]+', line) if t]
            images_line = []
            for sequence in tokens:
                img_name = self.move_to_image.get(sequence)
                if img_name:
                    images_line.append(img_name)
            images_line_paths = [os.path.join(BASE_DIR, self.selected_assets, image.strip())
                                 for image in images_line]
            new_lines.append(images_line_paths)

        if new_lines == self.selected_images_lines:
            return

        self.selected_images_lines = new_lines
        self._update_selected_images_display()

    # ---------- Utilidades de dados ----------
    def find_move_name(self, file_name):
        return self.move_to_name.get(file_name.upper())

    def find_character_moves(self, character_name):
        for data in self.CharMoves:
            if data['Character'] == character_name:
                return data['Moves']
        return None

    # ---------- Atualiza botões do personagem ----------
    def update_character_images(self, *_):
        selected_character = self.character_var.get().strip()

        # Retrato
        char_folder = os.path.join(BASE_DIR, "char")
        if selected_character == "None":
            self.character_image_button.configure(state="disabled", text="(Character)", image=None)
            self.character_image_button.image = None
        else:
            char_image_path = os.path.join(char_folder, selected_character + ".png")
            '''if os.path.exists(char_image_path):
                cimg = self._get_ctk_image(char_image_path, (48, 48))
                self.character_image_button.configure(state="normal", text="", image=cimg,
                                                      command=self.add_character_image)
                self.character_image_button.image = cimg'''
            if os.path.exists(char_image_path):
                cimg = self._get_ctk_image(char_image_path, (48, 48))
                # sem ação ao clicar
                self.character_image_button.configure(state="normal", text="", image=cimg)
                self.character_image_button.configure(command=None)  # garante que não faz nada ao clicar
                self.character_image_button.image = cimg

            else:
                self.character_image_button.configure(state="disabled", text="(Character)", image=None)
                self.character_image_button.image = None

        # Limpa botões anteriores
        for row in getattr(self, "character_image_buttons", []):
            for b in row:
                b.grid_forget()
        self.character_image_buttons = []
        self.tooltips = []

        if selected_character == "None":
            self._update_preview_field()
            self._relayout_palette()
            return

        char_moves_str = self.find_character_moves(selected_character)
        if not char_moves_str:
            self._update_preview_field()
            self._relayout_palette()
            return

        char_moves = sorted(char_moves_str.split(", "))
        assets_dir = os.path.join(BASE_DIR, self.selected_assets)
        column_index = 0
        for move in char_moves:
            button_row = []
            for filename in os.listdir(assets_dir):
                if "_Dark" in filename or not filename.lower().endswith(".png"):
                    continue
                if move == filename[3:][:-4]:
                    image_path = os.path.join(assets_dir, filename)
                    cimg = self._get_ctk_image(image_path, (self.current_icon_size, self.current_icon_size))
                    button = ctk.CTkButton(
                        self.image_frame, image=cimg, text="",
                        width=self.current_icon_size, height=self.current_icon_size,
                        fg_color="transparent", hover_color="#2d1b53",
                        command=lambda p=image_path: self.toggle_image(p)
                    )
                    button.image = cimg
                    button._image_path = image_path
                    button_row.append(button)

                    move_name = self.find_move_name(filename[3:][:-4])
                    if move_name:
                        try:
                            self.tooltips.append(Hovertip(button, move_name, hover_delay=300))
                        except Exception:
                            pass

            self.character_image_buttons.append(button_row)
            for i, b in enumerate(button_row):
                row_base = getattr(self, "_palette_rows_used", 8)
                b.grid(row=row_base, column=column_index, padx=4, pady=4)
                column_index += 1

        self._update_preview_field()
        self._relayout_palette()

    def add_character_image(self):
        selected_character = self.character_var.get().strip()
        if selected_character == "None":
            return
        char_image_path = os.path.join(BASE_DIR, "char", selected_character + ".png")
        if os.path.exists(char_image_path):
            if self.selected_images_lines:
                self.selected_images_lines[-1].append(char_image_path)
            else:
                self.selected_images_lines = [[char_image_path]]
            self._update_selected_images_display()

    # ---------- Troca de assets ----------
    def load_and_reload_assets(self, *_):
        value_to_find = self.images_folder_var.get()
        index = next(i for i, option in enumerate(self.assets_types) if option[0] == value_to_find)
        new_asset_folder = self.assets_types[index][1]

        tmp = []
        for line in self.selected_images_lines:
            tmp_line = []
            for item in line:
                old = os.path.join(BASE_DIR, self.selected_assets)
                new = os.path.join(BASE_DIR, new_asset_folder)
                tmp_line.append(item.replace(old, new))
            tmp.append(tmp_line)
        self.selected_images_lines = tmp
        self.selected_assets = new_asset_folder

        # reconstrói a paleta
        for child in self.image_frame.winfo_children():
            child.destroy()
        self._load_and_group_images()
        self.update_character_images()
        self._update_selected_images_display()

    # ---------- Auto-resize da palette ----------
    def _on_window_resize(self, event):
        # só trata o próprio toplevel (janela) e quando muda largura de verdade
        if event.widget is not self:
            return
        w = self.image_frame.winfo_width()
        if abs(w - self._last_palette_width) >= 8:
            self._last_palette_width = w
            self._relayout_palette()

    def _relayout_palette(self):
        # trava durante preview
        if self._suspend_relayout:
            return
        if getattr(self, "_relayout_id", None) is not None:
            try:
                self.after_cancel(self._relayout_id)
            except Exception:
                pass
        self._relayout_id = self.after(60, self._relayout_palette_now)

    def _relayout_palette_now(self):
        if self._suspend_relayout:
            self._relayout_id = self.after(60, self._relayout_palette_now)
            return

        container = self.image_frame
        avail = max(0, container.winfo_width() - 16)
        if avail <= 0:
            self._relayout_id = self.after(80, self._relayout_palette_now)
            return

        max_row_len = 0
        for row in getattr(self, "image_buttons", []):
            max_row_len = max(max_row_len, len(row))
        for row in getattr(self, "character_image_buttons", []):
            max_row_len = max(max_row_len, len(row))
        if max_row_len == 0:
            return

        size_by_width = int((avail - (max_row_len - 1) * ICON_GAP) / max_row_len)
        new_size = max(ICON_MIN, min(ICON_MAX, size_by_width))
        if new_size == self.current_icon_size:
            return

        self.current_icon_size = new_size
        self._apply_icon_size(new_size)

    def _apply_icon_size(self, size: int):
        # palette
        for row in getattr(self, "image_buttons", []):
            for btn in row:
                path = getattr(btn, "_image_path", None)
                if not path:
                    continue
                cimg = self._get_ctk_image(path, (size, size))
                btn.configure(image=cimg, width=size, height=size)
                btn.image = cimg
        # moves do personagem
        for row in getattr(self, "character_image_buttons", []):
            for btn in row:
                path = getattr(btn, "_image_path", None)
                if not path:
                    continue
                cimg = self._get_ctk_image(path, (size, size))
                btn.configure(image=cimg, width=size, height=size)
                btn.image = cimg

    # ---------- Montagem da palette ----------
    def _load_and_group_images(self):
        """R1..R4: 8 por linha por grupo; R5+: 12 por linha costurando."""
        assets_dir = os.path.join(BASE_DIR, self.selected_assets)
        if not os.path.isdir(assets_dir):
            self.image_buttons = []
            self._palette_rows_used = 0
            return

        files = [f for f in sorted(os.listdir(assets_dir)) if f.lower().endswith(".png")]
        files = [f for f in files if "_Dark" not in f and "R9_" not in f]

        # limpa a área da palette
        for child in self.image_frame.winfo_children():
            child.destroy()

        # agrupa por prefixo Rn (R1, R2, ...)
        groups = {}
        for filename in files:
            try:
                prefix = filename.split('_')[0]  # "R1", "R5", ...
            except Exception:
                continue
            groups.setdefault(prefix, []).append(filename)

        def key_group(prefix: str) -> int:
            try:
                return int(prefix[1:])
            except Exception:
                return 9999

        ordered_groups = sorted(groups.items(), key=lambda kv: key_group(kv[0]))

        self.image_buttons = []
        current_row = 0

        # Parte A: R1..R4 (8 por linha, por grupo)
        early_groups = [(p, flist) for (p, flist) in ordered_groups if key_group(p) < 5]
        for prefix, flist in early_groups:
            flist.sort()
            for idx, filename in enumerate(flist):
                row = current_row + (idx // PALETTE_MAX_COLS)
                col = idx % PALETTE_MAX_COLS

                while len(self.image_buttons) <= row:
                    self.image_buttons.append([])

                image_path = os.path.join(assets_dir, filename)
                cimg = self._get_ctk_image(image_path, (self.current_icon_size, self.current_icon_size))
                btn = ctk.CTkButton(
                    self.image_frame, image=cimg, text="",
                    width=self.current_icon_size, height=self.current_icon_size,
                    fg_color="transparent", hover_color="#2d1b53",
                    command=lambda p=image_path: self.toggle_image(p)
                )
                btn.image = cimg
                btn._image_path = image_path
                btn.grid(row=row, column=col, padx=4, pady=4)
                self.image_buttons[row].append(btn)

                try:
                    file_name = filename[6:][:-4]
                    move_name = self.find_move_name(file_name)
                    if move_name:
                        self.tooltips.append(Hovertip(btn, move_name, hover_delay=300))
                except Exception:
                    pass

            rows_used = (len(flist) + PALETTE_MAX_COLS - 1) // PALETTE_MAX_COLS
            current_row += rows_used

        # Parte B: R5+ (12 por linha, costurando)
        tail_files = []
        for prefix, flist in ordered_groups:
            if key_group(prefix) >= 5:
                flist.sort()
                tail_files.extend(flist)

        for i, filename in enumerate(tail_files):
            row = current_row + (i // SECONDARY_MAX_COLS)
            col = i % SECONDARY_MAX_COLS

            while len(self.image_buttons) <= row:
                self.image_buttons.append([])

            image_path = os.path.join(assets_dir, filename)
            cimg = self._get_ctk_image(image_path, (self.current_icon_size, self.current_icon_size))
            btn = ctk.CTkButton(
                self.image_frame, image=cimg, text="",
                width=self.current_icon_size, height=self.current_icon_size,
                fg_color="transparent", hover_color="#2d1b53",
                command=lambda p=image_path: self.toggle_image(p)
            )
            btn.image = cimg
            btn._image_path = image_path
            btn.grid(row=row, column=col, padx=4, pady=4)
            self.image_buttons[row].append(btn)

            try:
                file_name = filename[6:][:-4]
                move_name = self.find_move_name(file_name)
                if move_name:
                    self.tooltips.append(Hovertip(btn, move_name, hover_delay=300))
            except Exception:
                pass

        rows_used_tail = (len(tail_files) + SECONDARY_MAX_COLS - 1) // SECONDARY_MAX_COLS
        self._palette_rows_used = current_row + rows_used_tail

        # auto-ajuste
        self._relayout_palette()

    # ---------- Ações ----------
    def toggle_image(self, image_path):
        if self.selected_images_lines:
            self.selected_images_lines[-1].append(image_path)
        else:
            self.selected_images_lines = [[image_path]]
        self._update_selected_images_display()

    def remove_last_image(self):
        if self.selected_images_lines:
            if self.selected_images_lines[-1]:
                self.selected_images_lines[-1].pop()
                if len(self.selected_images_lines[-1]) == 0:
                    self.selected_images_lines.pop()
        self._update_selected_images_display()

    def clear_selected_images(self):
        # limpa a caixa de digitação também
        try:
            self.string_input.delete(0, tk.END)
        except Exception:
            pass
        self.selected_images_lines = []
        self._update_selected_images_display()
        self._update_preview_field()

    def _update_selected_images_display(self):
        for row_buttons in getattr(self, "image_buttons", []):
            for b in row_buttons:
                try:
                    b.configure(state="normal")
                except Exception:
                    pass
        self._update_preview_field()

    def _update_preview_field(self):
        # trava relayout da palette durante a recriação do preview
        self._suspend_relayout = True
        try:
            for w in self.preview_frame.winfo_children():
                w.destroy()

            if not self.selected_images_lines or all(len(line)==0 for line in self.selected_images_lines):
                ph = ctk.CTkLabel(self.preview_frame,
                                  text="Nenhuma notação selecionada.\nClique nos ícones ou digite os códigos.",
                                  text_color=SUBTXT, justify="center")
                ph.grid(row=0, column=0, padx=12, pady=12, sticky="n")
                return

            max_width = 17 * 60
            for r, line in enumerate(self.selected_images_lines):
                total = len(line) * 60
                scaled = max(28, int(60 * (max_width/total))) if total > max_width and len(line)>0 else 60
                for c, image_path in enumerate(line):
                    if not os.path.exists(image_path):
                        continue
                    cimg = self._get_ctk_image(image_path, (scaled, scaled))
                    lbl = ctk.CTkLabel(self.preview_frame, image=cimg, text="")
                    lbl.image = cimg
                    lbl.grid(row=r, column=c, padx=1, pady=2, sticky="w")
        finally:
            self._suspend_relayout = False
            self.after(1, self._relayout_palette)

    # ---------- Dicas ----------
    def show_tips(self):
        """Abre uma janelinha com dicas rápidas (fallback para messagebox)."""
        tips = (
            "• Digite a notação na caixa (com espaços em entre cada comando. separe linhas por vírgula(se necessário)).\n"
            "• Clique nos ícones da Palette para adicionar ao Preview.\n"
            "• ↺ remove o último comando, 🗑 limpa tudo (e a caixa), ⬇ salva PNG.\n"
            "• 🗑 limpa todo Preview (e a caixa texto), ⬇ salva PNG.\n"
            "• ⬇ salva PNG.\n"
            "• Escolha o personagem e clique no retrato para inserir o ícone.\n"
            "• R1..R4: 8 por linha; R5+: 12 por linha (costurando grupos).\n"
            "• F1 abre estas dicas.\n"
            "\n"
            "NOTATIONS TO TYPE\n"
                "    • f  → Front\n"
                "    • b  → Back\n"
                "    • u  → Up\n"
                "    • d  → Down\n"
                "    • db → Down Back\n"
                "    • df → Down Front\n"
                "    • uf → Up Front\n"
                "    • ub → Up Back\n"
                "    • fh  → Front Hold\n"
                "    • bh  → Back Hold\n"
                "    • uh  → Up Hold\n"
                "    • dh  → Down Hold\n"
                "    • dbh → Down Back Hold\n"
                "    • dfh → Down Front Hold\n"
                "    • ufh → Up Front Hold\n"
                "    • ubh → Up Back Hold\n"
                "    • 1   → Left Punch\n"
                "    • 2   → Right Punch\n"
                "    • 3   → Left Kick\n"
                "    • 4   → Right Kick\n"
                "    • 12  → Left Punch + Right Punch\n"
                "    • 34  → Left Kick + Right Kick\n"
                "    • 13  → Left Throw\n"
                "    • 24  → Right Throw\n"
                "    • 123  → Left Punch + Right Punch + Left Kick\n"
                "    • 124  → Left Punch + Right Punch + Right Kick\n"
                "    • 134  → Left Punch + Left Kick + Right Kick\n"
                "    • 234  → Right Punch + Left Kick + Right Kick\n"
                "    • 1234 → Ki Charge\n"

        )
        try:
            top = ctk.CTkToplevel(self)
            top.title("Dicas")
            top.geometry("800x600")
            top.transient(self)
            top.grab_set()
            top.configure(fg_color=CARD)

            ctk.CTkLabel(top, text="Dicas rápidas", font=("Segoe UI", 18, "bold"), text_color=TEXT)\
               .pack(pady=(16, 8))

            box = ctk.CTkTextbox(top, width=480, height=240)
            box.pack(padx=16, pady=8, fill="both", expand=True)
            box.insert("1.0", tips)
            box.configure(state="disabled")

            ctk.CTkButton(top, text="Fechar", fg_color=ACCENT, command=top.destroy)\
               .pack(pady=(0, 16))
        except Exception:
            messagebox.showinfo("Dicas", tips)

    # ---------- Exportar PNG ----------
    def export_images(self):
        if not self.selected_images_lines or all(len(line)==0 for line in self.selected_images_lines):
            messagebox.showinfo("Error", "Cannot save an empty notation.")
            return

        width_per_image = 80
        height_per_image = 80
        max_line_length = max(len(line) for line in self.selected_images_lines)
        line_count = len(self.selected_images_lines)
        total_width = max_line_length * width_per_image
        total_height = line_count * height_per_image

        from PIL import Image as PILImage
        combined = PILImage.new('RGBA', (total_width, total_height), (0,0,0,0))
        for r, line in enumerate(self.selected_images_lines):
            x = 0
            for p in line:
                img = PILImage.open(p).resize((width_per_image, height_per_image), PILImage.LANCZOS)
                combined.paste(img, (x, r*height_per_image), mask=img.convert('RGBA').split()[3])
                x += width_per_image

        out = os.path.join(BASE_DIR, "notation.png")
        if os.path.exists(out):
            i = 1
            while os.path.exists(os.path.join(BASE_DIR, f"notation_{i}.png")):
                i += 1
            out = os.path.join(BASE_DIR, f"notation_{i}.png")
        combined.save(out)
        messagebox.showinfo("Save Successful", f"Image file saved as {os.path.basename(out)}")

        if self.include_dark.get():
            dark = PILImage.new('RGBA', (total_width, total_height), (0,0,0,0))
            for r, line in enumerate(self.selected_images_lines):
                x = 0
                for p in line:
                    dark_path = p.replace(".png", "_Dark.png")
                    if os.path.exists(dark_path):
                        dimg = PILImage.open(dark_path).resize((width_per_image, height_per_image), PILImage.LANCZOS)
                        dark.paste(dimg, (x, r*height_per_image), mask=dimg.convert('RGBA').split()[3])
                    x += width_per_image
            dp = out.replace(".png", "_dark.png")
            dark.save(dp)


if __name__ == "__main__":
    app = VirtualKeyboardApp()
    app.mainloop()
