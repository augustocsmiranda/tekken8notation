# Tekken 8 – Combo Notation Generator (fork)

Este repositório é um **fork** do projeto **NotationImageGenerator** criado por **lolJooh11**.  
Eu parti do código original e **modifiquei/estendi** a ferramenta com melhorias de interface, carregamento de recursos para empacotamento (PyInstaller) e fluxo de exportação. **Todos os créditos do projeto base** são do autor original.

<img width="1609" height="929" alt="image" src="https://github.com/user-attachments/assets/c7b8311b-bdec-4f8b-a9c7-ac0d9b8ce4f8" />

---

## ✨ O que este fork adiciona

- UI modernizada com **customtkinter** (tema escuro, layout em cartões, preview ao lado).
- Função **`resource_path(...)`** para localizar arquivos quando empacotado com **PyInstaller** (suporte a *one-file* e *one-folder*).
- **Pasta de saída persistente** `Saved Notations/` (não salva em `_MEIPASS`).
- **Preview multi‑linhas**: separe linhas com vírgula (**`,`**).
- **Redimensionamento automático** do preview (base 32px) e **auto‑resize** da paleta.
- **Atalhos**: `F1` Dicas • `F2` Backspace • `F3` Clear • `F4` Salvar PNG.
- **Ícone** da janela + **AppUserModelID** no Windows (melhor pin na taskbar).
- Exportação opcional **dark** usando imagens com sufixo `_Dark.png`.
- Leitura de CSVs `MoveDictModified.csv` e `CharMoves.csv` (delimitador `;`, UTF‑8).

> O projeto original usa `tkinter` puro, pré‑visualização a 50px e salva na pasta atual.  
> Este fork reorganiza a UI, padroniza paths para empacotamento e define um diretório de saída estável.

---

## 🧭 Como usar

1. **Palette** (esquerda): clique nos ícones para adicionar ao preview.  
2. **Campo de texto**: digite notações (separe entradas por **espaço**).
   
   Ex.: `F N D DF 2 > F F 2 FH > SEN 3 > DF 1 FH > SEN 12 > HW 3 4 `
   
   <img width="1609" height="940" alt="image" src="https://github.com/user-attachments/assets/d9d5ecd0-ad29-4bbe-873f-6fc5490a1a05" />
   
   Use **vírgula** (**`,`**) para **quebrar linha** no preview.
   
   Ex.: `f f 2, d 1 2`

   <img width="1614" height="939" alt="image" src="https://github.com/user-attachments/assets/2fc65718-8c2b-4d54-86a9-0d2dca9b2afd" />


4. **Character**: escolha um personagem para exibir o retrato e botões de golpes dele.
5. **Salvar PNG**: botão **⬇** ou **F4** → arquivo(s) vão para `Saved Notations/`.

Atalhos úteis: **F1** Dicas • **F2** Backspace • **F3** Clear • **F4** Salvar.

---

## 📁 Estrutura de pastas

```
.
├─ AppNovo5.py
├─ icon.ico
├─ char/
├─ assets/
├─ data/
│  ├─ MoveDictModified.csv
│  └─ CharMoves.csv
└─ Saved Notations/   # gerada em runtime (saída)
```

**CSV – formatos:**
- `MoveDictModified.csv` → colunas **Move**, **Image**, **Name**  
- `CharMoves.csv` → colunas **Character**, **Moves** (lista separada por “, ”)

---

## 🙌 Créditos

- Projeto base: **NotationImageGenerator** por **lolJooh11**.
- https://github.com/LolJohn11/NotationImageGenerator?tab=readme-ov-file
- Este fork: melhorias de UI/empacotamento e ajustes de preview/paths.

> Este repositório existe **em homenagem e com respeito** ao trabalho do autor original.  
