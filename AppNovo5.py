import os
import csv
import ctypes
import re
import tkinter as tk  # uso p/ messagebox e alguns utilitários
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
PALETTE_MAX_COLS = 8  # número máximo de ícones por linha na palette

# Auto-ajuste da palette
ICON_MIN = 36   # tamanho mínimo do ícone
ICON_MAX = 64   # tamanho máximo do ícone
ICON_GAP = 6    # espaçamento horizontal usado na conta


class ScrollableFrame(ctk.CTkFrame):
    """Paleta com rolagem vertical para muitos ícones."""
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=CARD)
        self.vsb = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        # só vertical (sem horizontal; usamos auto-resize)
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
        self.geometry("1600x900")  # ajuste como preferir
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
        self.selected_images_lines = []  # lista de linhas; cada linha é lista de paths absolutos
        self.include_dark = tk.BooleanVar(value=False)
        self.images_folder_var = tk.StringVar(value="T8 Default")
        self.character_var = tk.StringVar(value="None")
        self.selected_assets = self.assets_types[0][1]
        self.character_image_buttons = []
        self.tooltips = []

        # cache de imagens (CTkImage) para HiDPI
        self._img_cache = {}
        # tamanho atual aplicado nos botões da palette
        self.current_icon_size = 48
        # debounce para não relayoutar em excesso
        self._relayout_id = None

        # widgets
        self.image_frame = None
        self.preview_frame = None
        self.string_input = None

        # ---- CONSTRÓI UI ESTILIZADA ----
        self._build_header()
        self._build_input()
        self._build_center()

        # liga traces (depois que os combos existem)
        self.images_folder_var.trace_add("write", self.load_and_reload_assets)
        self.character_var.trace_add("write", self.update_character_images)

        # carrega paleta e preview inicial
        self._load_and_group_images()
        self.update_character_images()
        self._update_selected_images_display()
        self._update_preview_field()
        self.after(100, self._relayout_palette)

    # ---------- Blocos de UI ----------
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

    def _build_header(self):
        header_card, header = self._card(self, pad=(16,12))
        header_card.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))
        header.grid_columnconfigure(0, weight=1)

        left  = ctk.CTkFrame(header, fg_color="transparent")
        right = ctk.CTkFrame(header, fg_color="transparent")
        left.grid_columnconfigure(0, weight=1)  # combo expande

        left.grid(row=0, column=0, sticky="w", padx=(2,0))
        right.grid(row=0, column=1, sticky="e")

        # Character
        self._field(left, "Character",
                    ctk.CTkComboBox, values=self.all_characters, width=220,
                    variable=self.character_var).grid(row=0, column=0, padx=(0,12), sticky="ew")

        # retrato do personagem ao lado do combo Character
        self.character_image_button = ctk.CTkButton(
            left, state="disabled", text="", width=48, height=48
        )
        self.character_image_button.grid(row=0, column=1, padx=(6, 0))

        # ações (placeholders)
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=0, column=0)
        for i, (txt, col) in enumerate([("↺", "#ff9f1c"), ("🗑", "#ef233c"), ("⬇", "#2ec4b6")]):
            ctk.CTkButton(actions, text=txt, width=38, height=38,
                          fg_color=col, hover_color=col, corner_radius=12).grid(row=0, column=i, padx=6)

    def _build_input(self):
        card, inner = self._card(self)
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,10))
        inner.grid_columnconfigure(0, weight=1)
        self.string_input = ctk.CTkEntry(inner, placeholder_text="Digite sua notação aqui...",
                                         height=56, corner_radius=12)
        self.string_input.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.string_input.bind("<KeyRelease>", self.process_string_input)
        self._debounce_id = None

    def _build_center(self):
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)
        center.grid_columnconfigure(0, weight=1, uniform="col")
        center.grid_columnconfigure(1, weight=1, uniform="col")
        center.grid_rowconfigure(0, weight=1)

        # LEFT: Paleta
        left_card, left_inner = self._card(center)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=(0,8))
        self._title(left_inner, "Palette").grid(row=0, column=0, sticky="w", padx=10, pady=(10,8))

        self.palette_scroll = ScrollableFrame(left_inner)
        # relayout quando o container mudar de tamanho/conteúdo
        self.palette_scroll.bind("<Configure>", lambda e: self._relayout_palette())
        self.palette_scroll.inner.bind("<Configure>", lambda e: self._relayout_palette())
        self.palette_scroll.grid(row=1, column=0, sticky="nsew", padx=10)
        left_inner.grid_rowconfigure(1, weight=1)
        left_inner.grid_columnconfigure(0, weight=1)

        self.image_frame = self.palette_scroll.inner  # onde coloco os botões

        # RIGHT: Preview + ações
        right_card, right_inner = self._card(center)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=(0,8))
        self._title(right_inner, "Preview").grid(row=0, column=0, sticky="w", padx=10, pady=(10,8))

        self.preview_frame = ctk.CTkFrame(right_inner, fg_color=CARD)
        self.preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,8))
        right_inner.grid_rowconfigure(1, weight=1)
        right_inner.grid_columnconfigure(0, weight=1)

        actions = ctk.CTkFrame(right_inner, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="e", padx=10, pady=(0,10))
        ctk.CTkButton(actions, text="Backspace",
                      command=lambda: self.remove_last_image()).grid(row=0, column=0, padx=4)
        ctk.CTkButton(actions, text="Clear",
                      command=lambda: self.clear_selected_images()).grid(row=0, column=1, padx=4)
        ctk.CTkButton(actions, text="Salvar PNG", fg_color=ACCENT,
                      command=lambda: self.export_images()).grid(row=0, column=2, padx=8)

        # Rodapé
        footer = ctk.CTkLabel(self, text="Tekken 8 Notation Generator • Create and share your combo notations",
                              text_color=SUBTXT)
        footer.grid(row=3, column=0, pady=(2, 12))

    def _field(self, parent, label, widget_cls, **kwargs):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=label, text_color=SUBTXT).grid(row=0, column=0, sticky="w", pady=(0,2))
        w = widget_cls(f, **kwargs)
        w.grid(row=1, column=0, sticky="ew")
        f.grid_columnconfigure(0, weight=1)
        return f

    # ---------- Imagens (CTkImage) ----------
    def _get_ctk_image(self, path, size):
        """Retorna um ctk.CTkImage (cacheado) para usar em CTkButton/CTkLabel."""
        key = (path, size)
        if key in self._img_cache:
            return self._img_cache[key]
        if not os.path.exists(path):
            return None
        pil = Image.open(path)
        cimg = ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
        self._img_cache[key] = cimg
        return cimg

    # ---------- Funções de negócio ----------
    def process_string_input(self, event=None):
        """Dispara parsing com debounce para evitar recomputar a cada tecla."""
        if getattr(self, "_debounce_id", None):
            try:
                self.after_cancel(self._debounce_id)
            except Exception:
                pass
        self._debounce_id = self.after(120, self._parse_and_update)

    def _parse_and_update(self):
        input_string = self.string_input.get().upper().strip()
        # separa por linhas (vírgula) e limpa vazios
        line_sequences = [seg for seg in (s.strip() for s in input_string.split(',')) if seg]

        new_lines = []
        for line in line_sequences:
            tokens = [t for t in re.split(r'[\s]+', line) if t]
            images_line = []
            for sequence in tokens:
                img_name = self.move_to_image.get(sequence)  # O(1) com mapa
                if img_name:
                    images_line.append(img_name)
            images_line_paths = [os.path.join(BASE_DIR, self.selected_assets, image.strip())
                                 for image in images_line]
            new_lines.append(images_line_paths)

        # evita redesenho se nada mudou
        if new_lines == self.selected_images_lines:
            return

        self.selected_images_lines = new_lines
        self._update_selected_images_display()

    def find_move_name(self, file_name):
        return self.move_to_name.get(file_name.upper())

    def find_character_moves(self, character_name):
        for data in self.CharMoves:
            if data['Character'] == character_name:
                return data['Moves']
        return None

    def update_character_images(self, *_):
        selected_character = self.character_var.get().strip()

        # Atualiza retrato
        char_folder = os.path.join(BASE_DIR, "char")
        if selected_character == "None":
            self.character_image_button.configure(state="disabled", text="(Character)", image=None)
            self.character_image_button.image = None
        else:
            char_image_path = os.path.join(char_folder, selected_character + ".png")
            if os.path.exists(char_image_path):
                cimg = self._get_ctk_image(char_image_path, (48, 48))
                self.character_image_button.configure(state="normal", text="", image=cimg,
                                                      command=self.add_character_image)
                self.character_image_button.image = cimg
            else:
                # desabilita sem popup
                self.character_image_button.configure(state="disabled", text="(Character)", image=None)
                self.character_image_button.image = None

        # Limpa botões anteriores de character moves
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

        column_index = 0
        assets_dir = os.path.join(BASE_DIR, self.selected_assets)
        for move in char_moves:
            button_row = []
            for filename in os.listdir(assets_dir):
                if "_Dark" in filename or not filename.lower().endswith(".png"):
                    continue
                if move == filename[3:][:-4]:
                    image_path = os.path.join(assets_dir, filename)  # <<< FALTAVA ISSO
                    cimg = self._get_ctk_image(image_path, (self.current_icon_size, self.current_icon_size))
                    button = ctk.CTkButton(self.image_frame, image=cimg, text="",
                                           width=self.current_icon_size, height=self.current_icon_size,
                                           fg_color="transparent", hover_color="#2d1b53",
                                           command=lambda p=image_path: self.toggle_image(p))
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
                row_base = getattr(self, "_palette_rows_used", 8)  # se não existir, usa 8 como antes
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

    def load_and_reload_assets(self, *_):
        value_to_find = self.images_folder_var.get()
        index = next(i for i, option in enumerate(self.assets_types) if option[0] == value_to_find)
        new_asset_folder = self.assets_types[index][1]

        # troca nos já selecionados
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
    def _relayout_palette(self):
        """Debounce para relayout da palette."""
        if getattr(self, "_relayout_id", None) is not None:
            try:
                self.after_cancel(self._relayout_id)
            except Exception:
                pass
        self._relayout_id = self.after(60, self._relayout_palette_now)

    def _relayout_palette_now(self):
        """Calcula o tamanho de ícone para caber a linha mais longa na largura disponível."""
        container = self.image_frame
        avail = max(0, container.winfo_width() - 16)
        if avail <= 0:
            self._relayout_id = self.after(80, self._relayout_palette_now)
            return

        # maior número de botões numa linha
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
        """Atualiza imagem e width/height de todos os botões de ícone."""
        # palette padrão
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

    # ---------- Montagem da palette (quebra de 8 em 8 por grupo Rn) ----------
    def _load_and_group_images(self):
        """Monta a palette agrupando por prefixo (R1, R2, ...)
        e quebra cada grupo em linhas de PALETTE_MAX_COLS colunas."""
        assets_dir = os.path.join(BASE_DIR, self.selected_assets)
        if not os.path.isdir(assets_dir):
            self.image_buttons = []
            self._palette_rows_used = 0
            return

        files = [f for f in sorted(os.listdir(assets_dir)) if f.lower().endswith(".png")]
        files = [f for f in files if "_Dark" not in f and "R9_" not in f]

        # limpa qualquer conteúdo anterior da área da palette
        for child in self.image_frame.winfo_children():
            child.destroy()

        # agrupa por prefixo: R1, R2, ...
        groups = {}
        for filename in files:
            try:
                prefix = filename.split('_')[0]  # ex: "R1"
            except Exception:
                continue
            groups.setdefault(prefix, []).append(filename)

        def key_group(g):
            try:
                return int(g[1:])  # número após 'R'
            except Exception:
                return 9999

        ordered_groups = sorted(groups.items(), key=lambda kv: key_group(kv[0]))

        # zera estrutura das linhas (agora dinâmica)
        self.image_buttons = []
        current_row = 0  # primeira linha disponível

        for prefix, flist in ordered_groups:
            flist.sort()
            for idx, filename in enumerate(flist):
                # calcula linha e coluna com quebra a cada PALETTE_MAX_COLS
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

                # tooltip
                try:
                    file_name = filename[6:][:-4]
                    move_name = self.find_move_name(file_name)
                    if move_name:
                        self.tooltips.append(Hovertip(btn, move_name, hover_delay=300))
                except Exception:
                    pass

            # após colocar o grupo, avança as linhas ocupadas por ele
            rows_used = (len(flist) + PALETTE_MAX_COLS - 1) // PALETTE_MAX_COLS
            current_row += rows_used

        self._palette_rows_used = current_row
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
        # limpa
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

        from PIL import Image as PILImage  # evitar colisão de nome
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
