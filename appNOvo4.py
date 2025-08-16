import customtkinter as ctk

# ---------- Paleta ----------
BG      = "#1a1038"  # fundo geral (roxinho escuro)
CARD    = "#241645"  # cartão/painéis
BORDER  = "#352866"  # borda sutil
TEXT    = "#e6e6ff"  # texto claro
SUBTXT  = "#9aa3c7"  # subtítulo
ACCENT  = "#7c3aed"  # roxo destaque

class TekkenNotationUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Tekken 8 Notation Generator")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        # fundo geral
        self.configure(fg_color=BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # parte central expande

        # ====== HEADER ======
        self.header_card, self.header = self._card(self, pad=(16,12))
        self.header_card.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))
        self.header.grid_columnconfigure(0, weight=1)

        left  = ctk.CTkFrame(self.header, fg_color="transparent")
        right = ctk.CTkFrame(self.header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(2,0))
        right.grid(row=0, column=1, sticky="e")


        # Controles (esquerda)
        # Controles (esquerda)
        self._field(left, "Character",
                    ctk.CTkComboBox, values=["Kazuya","Jin","King","None"], width=220) \
            .grid(row=0, column=0, padx=(0,12), sticky="ew")
        '''
        self._field(left, "Button Style",
                    ctk.CTkComboBox, values=["T8 Default","Xbox","PlayStation"], width=220) \
            .grid(row=0, column=1, padx=(0,12), sticky="ew")

        self.dark_check = ctk.CTkCheckBox(left, text="Include Dark Notation")
        self.dark_check.grid(row=0, column=2)
        '''

        # Ações (direita) – placeholders (sem lógica)
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=0, column=0)
        for i, (txt, col) in enumerate([("↺", "#ff9f1c"), ("🗑", "#ef233c"), ("⬇", "#2ec4b6")]):
            btn = ctk.CTkButton(actions, text=txt, width=38, height=38,
                                fg_color=col, hover_color=col, corner_radius=12)
            btn.grid(row=0, column=i, padx=6)

        # ====== INPUT GRANDÃO ======
        self.input_card, input_inner = self._card(self)
        self.input_card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,10))
        input_inner.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(input_inner, placeholder_text="Digite sua notação aqui...",
                                        height=56, corner_radius=12)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        # ====== CENTRO: 2 colunas ======
        self.center = ctk.CTkFrame(self, fg_color="transparent")
        self.center.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)
        self.center.grid_columnconfigure(0, weight=1, uniform="col")
        self.center.grid_columnconfigure(1, weight=1, uniform="col")
        self.center.grid_rowconfigure(0, weight=1)

        # LEFT CARD
        self.left_card, left_inner = self._card(self.center)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=(0,8))
        self._card_title(left_inner, "Directional Inputs").grid(row=0, column=0, sticky="w", padx=10, pady=(10,8))
        self._placeholder_box(left_inner, height=230).grid(row=1, column=0, sticky="nsew", padx=10)
        self._divider(left_inner).grid(row=2, column=0, sticky="ew", padx=10, pady=12)
        self._card_title(left_inner, "Attack Buttons").grid(row=3, column=0, sticky="w", padx=10)
        self._placeholder_box(left_inner, height=120).grid(row=4, column=0, sticky="nsew", padx=10, pady=(6,10))
        left_inner.grid_rowconfigure(1, weight=1)

        # RIGHT CARD
        self.right_card, right_inner = self._card(self.center)
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=(0,8))
        self._card_title(right_inner, "Special Notations").grid(row=0, column=0, sticky="w", padx=10, pady=(10,8))
        self._placeholder_box(right_inner, height=260).grid(row=1, column=0, sticky="nsew", padx=10)
        self._divider(right_inner).grid(row=2, column=0, sticky="ew", padx=10, pady=12)
        self._card_title(right_inner, "Frame Data & Properties").grid(row=3, column=0, sticky="w", padx=10)
        self._placeholder_box(right_inner, height=120).grid(row=4, column=0, sticky="nsew", padx=10, pady=(6,10))
        right_inner.grid_rowconfigure(1, weight=1)    

        # ====== RODAPÉ ======
        footer = ctk.CTkLabel(self, text="Tekken 8 Notation Generator • Create and share your combo notations",
                              text_color=SUBTXT)
        footer.grid(row=3, column=0, pady=(2, 12))

    # --------- Helpers de UI ----------
    def _card(self, parent, pad=(10,10)):
        outer = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=18,
                            border_width=1, border_color=BORDER)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=pad[0], pady=pad[1])

        return outer, inner


    def _card_title(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=("Segoe UI", 18, "bold"), text_color=TEXT)

    def _divider(self, parent):
        return ctk.CTkFrame(parent, fg_color=BORDER, height=2, corner_radius=1)

    def _placeholder_box(self, parent, height=160):
        box = ctk.CTkFrame(parent, fg_color="#2d1b53", corner_radius=14)
        box.configure(height=height)
        box.grid_propagate(False)
        # dica visual
        ctk.CTkLabel(box, text="(Área para conteúdo / chips / botões)",
                     text_color=SUBTXT).place(relx=0.5, rely=0.5, anchor="center")
        return box

    def _field(self, parent, label, widget_cls, **kwargs):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        # label acima
        ctk.CTkLabel(f, text=label, text_color=SUBTXT).grid(row=0, column=0, sticky="w", pady=(0, 2))
        # widget criado com pai = f
        w = widget_cls(f, **kwargs)
        w.grid(row=1, column=0, sticky="ew")
        f.grid_columnconfigure(0, weight=1)
        return f

if __name__ == "__main__":
    app = TekkenNotationUI()
    app.mainloop()
