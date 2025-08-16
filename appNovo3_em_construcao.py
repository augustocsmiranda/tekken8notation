import os
import csv
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from idlelib.tooltip import Hovertip
import re

class VirtualKeyboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notation Image Generator")

        myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # Set window icon
        icon_path = os.path.join(os.getcwd(), "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self.root.geometry("1280x880")  # Window size

        self.assets_types = [
            ("T8 Default", "assets"),
            ("Xbox", "assets_xbox"),
            ("PlayStation", "assets_ps"),
        ]
        
        self.all_characters = [
            "None",
            "Alisa",
            "Asuka",
            "Azucena",
            "Bryan",
            "Claudio",
            "Clive",
            "Devil Jin",
            "Dragunov",
            "Eddy",
            "Fahkumram",
            "Feng",
            "Heihachi",
            "Hwoarang",
            "Jack 8",
            "Jin",
            "Jun",
            "Kazuya",
            "King",
            "Kuma",
            "Lars",
            "Law",
            "Lee",
            "Leo",
            "Leroy",
            "Lidia",
            "Lili",
            "Lidia",
            "Nina",
            "Panda",
            "Paul",
            "Raven",
            "Reina",
            "Shaheen",
            "Steve",
            "Victor",
            "Xiaoyu",
            "Yoshimitsu",
            "Zafina",
        ]
        
        # Load MoveDict CSV
        movedict_csv = os.path.join(os.getcwd(), "data", "MoveDictModified.csv")
        with open(movedict_csv, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            self.MoveDict = [row for row in csv_reader]
        
        # Load CharMoves CSV
        charmoves_csv = os.path.join(os.getcwd(), "data", "CharMoves.csv")
        with open(charmoves_csv, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            self.CharMoves = [row for row in csv_reader]
          
        # Agora selected_images será lista de listas, para múltiplas linhas
        self.selected_images_lines = []  # exemplo: [ [img1, img2], [img3, img4, img5], ... ]

        self.include_dark = tk.BooleanVar(value=False)

        # Variables for assets and character selection
        self.images_folder_var = tk.StringVar(value="T8 Default")
        self.images_folder_var.trace_add("write", self.load_and_reload_assets)
        
        self.character_var = tk.StringVar(value="None")
        self.character_var.trace_add("write", self.update_character_images)

        self.selected_assets = self.assets_types[0][1]
        self.character_image_buttons = []
        self.tooltips = []

        # Entry widget for string input (self.string_input)
        self.string_input = tk.Entry(root, font=("Arial", 14))
        self.string_input.grid(row=11, column=0, columnspan=5, sticky="ew", padx=10, pady=10)
        self.string_input.bind('<KeyRelease>', self.process_string_input)

        self.preview_frame = tk.Frame(self.root)
        self.preview_frame.grid(row=8, column=0, columnspan=5, pady=5)

        self.create_widgets()
        self.load_and_group_images()
        self.update_character_images()
        self.update_selected_images_display()
        self.update_preview_field()

    def process_string_input(self, event):
        input_string = self.string_input.get().upper().strip()
        # Dividir primeiro pela vírgula para linhas
        line_sequences = input_string.split(',')

        # Para cada linha, separar por espaços/vírgulas múltiplos (como estava antes) para tokens
        self.selected_images_lines = []
        for line in line_sequences:
            tokens = re.split(r'[\s]+', line.strip())
            tokens = [t for t in tokens if t]  # remove vazios
            images_line = []
            for sequence in tokens:
                for move_dict in self.MoveDict:
                    if sequence == move_dict["Move"].upper():
                        images_line.append(move_dict["Image"])
                        break
            # Transformar nomes de imagem em paths com pasta correta
            images_line_paths = [os.path.join(self.selected_assets, image_name) for image_name in images_line]
            self.selected_images_lines.append(images_line_paths)

        self.update_selected_images_display()

    def create_widgets(self):
        # Selected Images Display Frame
        self.image_frame = tk.Frame(self.root)
        self.image_frame.grid(row=0, column=0, columnspan=5, pady=10)

        # Load and group images for the selected asset folder
        image_files = self.load_and_group_images()

        self.image_buttons = [[] for _ in range(8)]

        for group in image_files:
            for filename in group:
                if "_Dark" in filename or "R9_" in filename:
                    continue

                image_path = os.path.join(self.selected_assets, filename)
                img = Image.open(image_path).resize((50, 50), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                button = tk.Button(self.image_frame, image=img_tk, command=lambda i=image_path: self.toggle_image(i))
                button.image = img_tk

                row = min(int(filename.split('_')[0][1]), 8)
                self.image_buttons[row - 1].append(button)

                self.file_name = filename[6:][:-4]
                move_name = self.find_move_name(self.file_name)
                if move_name:
                    self.tooltips.append(Hovertip(button, move_name, hover_delay=300))

        for i, row_buttons in enumerate(self.image_buttons):
            for j, button in enumerate(row_buttons):
                button.grid(row=i, column=j, padx=5, pady=5)

        # Assets style dropdown
        assets_menu_label = tk.Label(self.root, text="Button style:")
        assets_menu_label.grid(row=9, column=3, pady=10, columnspan=2, sticky="w")
        assets_menu = tk.OptionMenu(self.root, self.images_folder_var, *[option[0] for option in self.assets_types])
        assets_menu.grid(row=9, column=4, pady=10, columnspan=2, sticky="w")

        # Character dropdown
        character_label = tk.Label(self.root, text="Character:")
        character_label.grid(row=7, column=3, pady=10, columnspan=2, sticky="w")
        character_menu = tk.OptionMenu(self.root, self.character_var, *self.all_characters)
        character_menu.grid(row=7, column=4, pady=10, columnspan=2, sticky="w")

        # Character image button
        self.character_image_button = tk.Button(self.root, state=tk.DISABLED, command=self.add_character_image)
        self.character_image_button.grid(row=7, column=3, pady=10, columnspan=1)

        # Backspace button
        backspace_button = tk.Button(self.root, text="Backspace", command=self.remove_last_image)
        backspace_button.grid(row=10, column=0, pady=5, columnspan=1)

        # Clear button
        clear_button = tk.Button(self.root, text="Clear", command=self.clear_selected_images)
        clear_button.grid(row=10, column=1, pady=5, columnspan=1)

        # Include Dark checkbox
        include_dark_checkbox = tk.Checkbutton(self.root, text="Include dark notation", variable=self.include_dark)
        include_dark_checkbox.grid(row=10, column=2, pady=10, columnspan=2)

        # Export button
        export_button = tk.Button(self.root, text="Save as PNG", command=self.export_images)
        export_button.grid(row=10, column=4, pady=10, columnspan=1)

    def find_move_name(self, file_name):
        for data in self.MoveDict:
            if data['Move'].upper() == file_name.upper():
                return data['Name']
        return None

    def find_character_moves(self, character_name):
        for data in self.CharMoves:
            if data['Character'] == character_name:
                return data['Moves']
        return None

    def update_character_images(self, *args):
        selected_character = self.character_var.get()

        if selected_character == "None":
            self.character_image_button.configure(image='')
            self.character_image_button.config(state=tk.DISABLED)
        else:
            char_folder = os.path.join(os.getcwd(), "char")
            char_image_path = os.path.join(char_folder, selected_character + ".png")

            if os.path.exists(char_image_path):
                img = Image.open(char_image_path).resize((50, 50), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.character_image_button.config(state=tk.NORMAL, image=img_tk, command=self.add_character_image)
                self.character_image_button.image = img_tk
            else:
                messagebox.showwarning("Image Not Found", f"Image not found for character: {selected_character}")
                self.character_var.set("None")

        # Clear existing character-specific buttons
        for button_row in self.character_image_buttons:
            for button in button_row:
                button.grid_forget()

        if selected_character == "None":
            return

        char_moves_str = self.find_character_moves(selected_character)
        if not char_moves_str:
            return

        char_moves = char_moves_str.split(", ")
        char_moves.sort()
        self.character_image_buttons = []

        column_index = 0
        for move in char_moves:
            button_row = []
            for filename in os.listdir(self.selected_assets):
                if move == filename[3:][:-4]:
                    if "_Dark" in filename:
                        continue
                    image_path = os.path.join(self.selected_assets, filename)
                    img = Image.open(image_path).resize((50, 50), Image.LANCZOS)
                    img_tk = ImageTk.PhotoImage(img)
                    button = tk.Button(self.image_frame, image=img_tk, command=lambda i=image_path: self.toggle_image(i))
                    button.image = img_tk
                    button_row.append(button)

                    self.file_name = filename[3:][:-4]
                    move_name = self.find_move_name(self.file_name)
                    if move_name:
                        self.tooltips.append(Hovertip(button, move_name, hover_delay=300))

            self.character_image_buttons.append(button_row)
            for i, button in enumerate(button_row):
                button.grid(row=7, column=column_index, padx=5, pady=5)
                column_index += 1

        self.update_preview_field()

    def add_character_image(self):
        selected_character = self.character_var.get()
        if selected_character != "None":
            char_folder = os.path.join(os.getcwd(), "char")
            char_image_path = os.path.join(char_folder, selected_character + ".png")

            if os.path.exists(char_image_path):
                # Adicionar em última linha, se existir, senão criar nova linha
                if self.selected_images_lines:
                    self.selected_images_lines[-1].append(char_image_path)
                else:
                    self.selected_images_lines = [[char_image_path]]
                self.update_selected_images_display()

    def load_and_reload_assets(self, *args):
        value_to_find = self.images_folder_var.get()
        index = next(i for i, option in enumerate(self.assets_types) if option[0] == value_to_find)
        new_asset_folder = self.assets_types[index][1]

        temp_selected_images_lines = []
        for line in self.selected_images_lines:
            temp_line = []
            for item in line:
                temp_line.append(item.replace(self.selected_assets, new_asset_folder))
            temp_selected_images_lines.append(temp_line)

        self.selected_images_lines = temp_selected_images_lines
        self.selected_assets = new_asset_folder

        self.preview_frame.grid_forget()
        self.character_image_button.grid_forget()
        self.create_widgets()
        self.load_and_group_images()
        self.update_character_images()
        self.update_selected_images_display()
        self.update_preview_field()

    def load_and_group_images(self, *args):
        image_files = sorted(os.listdir(self.selected_assets))
        image_files = sorted(image_files, key=lambda x: (x.split('_')[0], x))

        grouped_images = [[] for _ in range(8)]
        for filename in image_files:
            if "_Dark" in filename:
                continue
            row = min(int(filename.split('_')[0][1]), 8)
            grouped_images[row - 1].append(filename)

        self.update_preview_field(grouped_images)
        return grouped_images

    def toggle_image(self, image_path):
        # Adiciona na última linha, se existir, senão cria nova linha
        if self.selected_images_lines:
            self.selected_images_lines[-1].append(image_path)
        else:
            self.selected_images_lines = [[image_path]]
        self.update_selected_images_display()

    def remove_last_image(self):
        if self.selected_images_lines:
            if self.selected_images_lines[-1]:
                self.selected_images_lines[-1].pop()
                if len(self.selected_images_lines[-1]) == 0:
                    self.selected_images_lines.pop()
            self.update_selected_images_display()

    def clear_selected_images(self):
        self.selected_images_lines = []
        self.update_selected_images_display()
        self.update_preview_field()

    def update_selected_images_display(self):
        for row_buttons in self.image_buttons:
            for button in row_buttons:
                button.config(state=tk.NORMAL)

        # Atualizar preview
        self.update_preview_field()

    def update_preview_field(self, grouped_images=None):
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # grouped_images não é usado aqui para preview
        # Vamos exibir self.selected_images_lines, linha por linha

        max_width = 17 * 50  # limite largura linha

        for row_index, line_images in enumerate(self.selected_images_lines):
            total_width = len(line_images) * 50
            if total_width > max_width:
                scale_factor = max_width / total_width
                scaled_size = int(50 * scale_factor)
            else:
                scaled_size = 50

            for col_index, image_path in enumerate(line_images):
                img = Image.open(image_path).resize((scaled_size, scaled_size), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                label = tk.Label(self.preview_frame, image=img_tk)
                label.image = img_tk
                label.grid(row=row_index, column=col_index, padx=0)

    def export_images(self):
        if not self.selected_images_lines or all(len(line) == 0 for line in self.selected_images_lines):
            messagebox.showinfo("Error", "Cannot save an empty notation.")
            return

        # Calcular largura total e altura total para a imagem combinada
        max_line_length = max(len(line) for line in self.selected_images_lines)
        line_count = len(self.selected_images_lines)
        width_per_image = 80
        height_per_image = 80
        total_width = max_line_length * width_per_image
        total_height = line_count * height_per_image

        combined_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

        for line_index, line in enumerate(self.selected_images_lines):
            current_width = 0
            for image_path in line:
                img = Image.open(image_path).resize((width_per_image, height_per_image), Image.LANCZOS)
                combined_image.paste(img, (current_width, line_index * height_per_image), mask=img.convert('RGBA').split()[3])
                current_width += width_per_image

        base_filename = "notation.png"
        if os.path.exists(base_filename):
            suffix = 1
            while os.path.exists(f"notation_{suffix}.png"):
                suffix += 1
            base_filename = f"notation_{suffix}.png"

        combined_image.save(base_filename)
        messagebox.showinfo("Save Successful", f"Image file saved as {base_filename}")

        if self.include_dark.get():
            dark_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
            for line_index, line in enumerate(self.selected_images_lines):
                current_width = 0
                for image_path in line:
                    dark_path = image_path.replace(".png", "_Dark.png")
                    if os.path.exists(dark_path):
                        dark_img = Image.open(dark_path).resize((width_per_image, height_per_image), Image.LANCZOS)
                        dark_image.paste(dark_img, (current_width, line_index * height_per_image), mask=dark_img.convert('RGBA').split()[3])
                    current_width += width_per_image

            dark_base_filename = base_filename.replace(".png", "_dark.png")
            if os.path.exists(dark_base_filename):
                suffix = 1
                while os.path.exists(f"notation_{suffix}_dark.png"):
                    suffix += 1
                dark_base_filename = f"notation_{suffix}_dark.png"

            dark_image.save(dark_base_filename)
            # Você pode descomentar a linha abaixo para mostrar mensagem de sucesso para a imagem dark
            # messagebox.showinfo("Save Successful", f"Dark image saved as {dark_base_filename}")
                    

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualKeyboardApp(root)
    root.mainloop()
