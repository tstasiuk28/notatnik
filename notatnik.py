import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import pywinstyles

def licz_sylaby(linia):
    samogloski = "aeiouyąęóüöä"
    tekst = linia.lower()
    licznik = sum(1 for char in tekst if char in samogloski)
    for i in range(len(tekst) - 1):
        if tekst[i] == 'i' and tekst[i+1] in samogloski:
            licznik -= 1
    return max(0, licznik)

def pobierz_aktywne_komponenty():
    try:
        tab_id = notebook.select()
        tab_frame = notebook.nametowidget(tab_id)
        return {
            "text": tab_frame.text_area,
            "lines": tab_frame.line_numbers,
            "syllables": tab_frame.syllable_counts
        }
    except:
        return None

def aktualizuj_wszystko(event=None):
    komp = pobierz_aktywne_komponenty()
    if not komp: return

    # --- Poprawiona logika numeracji i sylab ---
    linie_text = komp["text"].get('1.0', 'end-1c').split('\n')
    nowe_numery, nowe_sylaby = [], []
    
    licznik_wersow = 1  # Zaczynamy od 1

    for linia in linie_text:
        if linia.strip(): 
            nowe_numery.append(str(licznik_wersow))
            nowe_sylaby.append(str(licz_sylaby(linia)))
            licznik_wersow += 1  # Zwiększamy tylko, gdy linia ma treść
        else:
            nowe_numery.append("")
            nowe_sylaby.append("")
            # Tutaj licznik_wersow NIE rośnie
            
    for k, dane in [("lines", nowe_numery), ("syllables", nowe_sylaby)]:
        komp[k].config(state='normal')
        komp[k].delete('1.0', tk.END)
        komp[k].insert('1.0', "\n".join(dane))
        komp[k].config(state='disabled')
        komp[k].yview_moveto(komp["text"].yview()[0])

  # --- KOLOROWANIE TAGÓW ---
    txt = komp["text"]
    
    # 1. Czyścimy stare kolory wszystkich tagów
    txt.tag_remove("green_tag", "1.0", tk.END)
    txt.tag_remove("gray_tag", "1.0", tk.END)

    # 2. Funkcja pomocnicza, żeby nie powtarzać kodu
    def zastosuj_kolor(char_start, char_end, tag_name):
        s_pos = "1.0"
        while True:
            s_pos = txt.search(char_start, s_pos, stopindex=tk.END)
            if not s_pos: break
            
            e_pos = txt.search(char_end, s_pos, stopindex=tk.END)
            if not e_pos: break
            
            e_pos = f"{e_pos}+1c"
            txt.tag_add(tag_name, s_pos, e_pos)
            s_pos = e_pos

    # 3. Wywołujemy dla Twoich par znaków
    zastosuj_kolor("<", ">", "green_tag")
    zastosuj_kolor("(", ")", "gray_tag")


    # Status bar
    index = txt.index(tk.INSERT)
    label_status.config(text=f"Wiersz: {index.split('.')[0]} | Zakładek: {len(notebook.tabs())}  ")

def on_scroll(event):
    komp = pobierz_aktywne_komponenty()
    if not komp: return
    delta = int(-1 * (event.delta / 120))
    komp["text"].yview_scroll(delta, "units")
    pos = komp["text"].yview()[0]
    komp["lines"].yview_moveto(pos)
    komp["syllables"].yview_moveto(pos)
    return "break"

def domykaj_znaki_pro(event):
    pary = {'"': '"', '(': ')', '{': '}', '[': ']', "<": ">"}
    komp = pobierz_aktywne_komponenty()
    if not komp or event.char not in pary: return
    
    txt = komp["text"]
    try:
        # Jeśli coś jest zaznaczone, otocz to znakami
        start, end = txt.index(tk.SEL_FIRST), txt.index(tk.SEL_LAST)
        wybrany = txt.get(start, end)
        txt.delete(start, end)
        txt.insert(start, event.char + wybrany + pary[event.char])
        return "break"
    except tk.TclError:
        # Jeśli nic nie jest zaznaczone, wstaw parę i cofnij kursor o 1
        pos = txt.index(tk.INSERT)
        txt.insert(pos, event.char + pary[event.char])
        txt.mark_set(tk.INSERT, f"{pos}+1c")
        return "break"

def usun_slowo(event=None):
    komp = pobierz_aktywne_komponenty()
    if not komp: return "break"
    
    txt = komp["text"]
    
    # Pobieramy pozycję kursora
    insert_pos = txt.index(tk.INSERT)
    
    # Jeśli kursor jest na samym początku, nie ma czego usuwać
    if insert_pos == "1.0":
        return "break"
    
    # Wyznaczamy początek słowa używając wewnętrznej logiki Tkintera
    # "insert -1c wordstart" cofa się o jeden znak i szuka początku słowa
    start_pos = txt.index(f"{insert_pos}-1c wordstart")
    
    # Usuwamy tekst od znalezionego początku do obecnej pozycji kursora
    txt.delete(start_pos, insert_pos)
    
    aktualizuj_wszystko()
    return "break"

def usun_wers(event=None):
    komp = pobierz_aktywne_komponenty()
    if not komp: return "break"
    idx = komp["text"].index(tk.INSERT).split('.')[0]
    komp["text"].delete(f"{idx}.0", f"{idx}.end+1c")
    aktualizuj_wszystko()
    return "break"

def cofnij_zmiane(event=None):
    komp = pobierz_aktywne_komponenty()
    if not komp: return "break"
    try: komp["text"].edit_undo()
    except: pass
    aktualizuj_wszystko()
    return "break"

def otworz_plik(event=None):
    path = filedialog.askopenfilename(filetypes=[("Tekst", "*.txt"), ("Wszystkie", "*.*")])
    if path:
        with open(path, "r", encoding="utf-8") as f:
            nowa_zakladka(path.split("/")[-1], f.read())

def zapisz_plik(event=None):
    komp = pobierz_aktywne_komponenty()
    if not komp: return
    obecna_nazwa = notebook.tab(notebook.select(), "text").replace("   x", "")
    path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=obecna_nazwa)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(komp["text"].get("1.0", tk.END))
        notebook.tab(notebook.select(), text=f"{path.split('/')[-1]}   x")

def nowa_zakladka(nazwa="Nowy", tresc=""):
    tab_title = f"{nazwa}   x"
    tab = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(tab, text=tab_title)
    
    ln = tk.Text(tab, width=3, padx=2, pady=5, fg="#858585", bg="#1e1e1e", font=("Consolas", 12), state='disabled', borderwidth=0, highlightthickness=0)
    ln.pack(side="left", fill="y")

    sc = tk.Text(tab, width=3, padx=2, pady=5, fg="#5a5a5a", bg="#1e1e1e", font=("Consolas", 12), state='disabled', borderwidth=0, highlightthickness=0)
    sc.pack(side="right", fill="y")

    ta = tk.Text(tab, wrap="none", padx=2, pady=5, fg="#d4d4d4", bg="#1e1e1e", insertbackground="white", font=("Consolas", 12), borderwidth=0, highlightthickness=0, undo=True)
    ta.pack(side="left", expand=True, fill="both")
    ta.tag_configure("green_tag", foreground="#4ec9b0") # Dla <...>
    ta.tag_configure("gray_tag", foreground="#787878")  # Dla (...)
    ta.insert("1.0", tresc)

    tab.text_area, tab.line_numbers, tab.syllable_counts = ta, ln, sc

    # Bindowanie funkcji dla pola tekstowego
    ta.bind("<KeyRelease>", aktualizuj_wszystko)
    ta.bind("<ButtonRelease-1>", aktualizuj_wszystko)
    ta.bind("<MouseWheel>", on_scroll)
    ta.bind("<Key>", domykaj_znaki_pro)  # PRZYWRÓCONE DOMYKANIE
    
    notebook.select(tab)
    aktualizuj_wszystko()

def obsluga_klikniecia_zakladki(event):
    try:
        index = notebook.index(f"@{event.x},{event.y}")
        # Sprawdzamy czy kliknięto w okolicach 'x'
        if event.x > (notebook.bbox(index)[0] + notebook.bbox(index)[2] - 25):
            # Zamiast notebook.forget, wywołujemy naszą nową funkcję z pytaniem
            notebook.select(index) # Najpierw zaznaczamy tę zakładkę
            zamknij_zakladke()
    except: pass

def zamknij_zakladke(event=None):
    odpowiedz = messagebox.askyesnocancel("Zapisz zmiany", "Czy chcesz zapisać zmiany przed zamknięciem?")
    
    if odpowiedz is True:
        zapisz_plik()
    elif odpowiedz is None:
        return "break" # TO JEST KLUCZOWE
        
    if len(notebook.tabs()) > 1:
        notebook.forget(notebook.select())
    else:
        # Jeśli to ostatnia zakładka, nie niszczymy roota tutaj, 
        # bo funkcja zamknij_aplikacje zrobi to sama
        notebook.forget(notebook.select())

def zamknij_aplikacje():
    # Pobieramy listę wszystkich zakładek
    while len(notebook.tabs()) > 0:
        notebook.select(0) # Zawsze wybieramy pierwszą od lewej
        wynik = zamknij_zakladke()
        if wynik == "break": # Jeśli użytkownik kliknął 'Anuluj'
            return
    root.destroy() # Jeśli wszystkie zakładki zamknięte (lub wybrano 'Nie')

root = tk.Tk()
root.title("Notatnik_28")
root.geometry("1028x728")
root.configure(bg="#1e1e1e")
pywinstyles.apply_style(root, "dark")

style = ttk.Style()
style.theme_use('default')
style.configure("TNotebook", background="#2d2d2d", borderwidth=0)
style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#b4b4b4", padding=[10, 3], borderwidth=0)
style.map("TNotebook.Tab", background=[("selected", "#1e1e1e")], foreground=[("selected", "#007acc")])

# Pasek górny
top_bar = tk.Frame(root, bg="#2d2d2d", height=30)
top_bar.pack(side="top", fill="x")

# Menu Plik
plik_btn = tk.Menubutton(top_bar, text="Plik", bg="#2d2d2d", fg="#d4d4d4", font=("Segoe UI", 10), borderwidth=0)
plik_btn.pack(side="left")
plik_m = tk.Menu(plik_btn, tearoff=0, bg="#2d2d2d", fg="#d4d4d4", activebackground="#007acc")
plik_m.add_command(label="Nowa (Ctrl+N)", command=nowa_zakladka)
plik_m.add_command(label="Otwórz (Ctrl+O)", command=otworz_plik)
plik_m.add_command(label="Zapisz (Ctrl+S)", command=zapisz_plik)
plik_m.add_separator()
plik_m.add_command(label="Wyjdź", command=zamknij_aplikacje)
plik_btn.config(menu=plik_m)

plus_btn = tk.Button(top_bar, text=" + ", bg="#2d2d2d", fg="#007acc", font=("Segoe UI", 12, "bold"), borderwidth=0, command=nowa_zakladka)
plus_btn.pack(side="left", padx=10)

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

label_status = tk.Label(root, text="Gotowy", bg="#007acc", fg="white", font=("Segoe UI", 9), anchor="e", padx=10)
label_status.pack(side="bottom", fill="x")

notebook.bind("<Button-1>", obsluga_klikniecia_zakladki)
root.bind("<Control-n>", lambda e: nowa_zakladka())
root.bind("<Control-o>", otworz_plik)
root.bind("<Control-s>", zapisz_plik)
root.bind("<Control-w>", zamknij_zakladke)
root.bind("<Control-z>", cofnij_zmiane)
root.bind("<Control-BackSpace>", usun_slowo)
root.bind("<Alt-BackSpace>", usun_wers)

nowa_zakladka()
root.protocol("WM_DELETE_WINDOW", zamknij_aplikacje)
root.mainloop()