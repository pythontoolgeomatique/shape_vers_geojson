import tkinter as tk
from tkinter import filedialog, ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

import geopandas as gpd
import fiona
import pandas as pd # Nécessaire pour la conversion de type
import threading
import os
import re # Pour nettoyer les noms de fichiers

class ShpMultiToolApp(ttk.Window):

    def __init__(self):
        super().__init__(themename="litera")
        self.title("Convertisseur et Extracteur Shapefile")
        self.geometry("800x850") # Augmenté la hauteur

        # Données en mémoire
        self.input_path = tk.StringVar()
        self.output_file = tk.StringVar() # Onglet simple
        self.output_folder = tk.StringVar() # Onglet requête
        self.available_attributes = []
        # La liste stocke maintenant des tuples: (nom_fichier, requete)
        self.queries_list = [] 

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=BOTH, expand=YES)
        self.create_input_frame(main_frame)

        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill=BOTH, expand=YES, pady=10)
        tab_simple = ttk.Frame(tab_control, padding="15")
        tab_query = ttk.Frame(tab_control, padding="15")
        tab_control.add(tab_simple, text='  Conversion Simple  ')
        tab_control.add(tab_query, text='  Extraction par Requête  ')

        self.create_simple_tab(tab_simple)
        self.create_query_tab(tab_query)

        self.create_status_frame(main_frame)

    def create_input_frame(self, parent):
        in_frame = ttk.Labelframe(parent, text="1. Fichier Shapefile d'entrée (Commun)", padding="10")
        in_frame.pack(fill=X, pady=10)
        in_entry = ttk.Entry(in_frame, textvariable=self.input_path, state="readonly")
        in_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        in_btn_browse = ttk.Button(in_frame, text="Parcourir...", command=self.select_input_file, bootstyle="secondary")
        in_btn_browse.pack(side=LEFT, padx=(0, 5))
        in_btn_load = ttk.Button(in_frame, text="Charger les attributs (pour les requêtes)", command=self.load_attributes, bootstyle="info")
        in_btn_load.pack(side=LEFT)

    def create_simple_tab(self, parent):
        out_frame = ttk.Labelframe(parent, text="2. Fichier GeoJSON de sortie", padding="10")
        out_frame.pack(fill=X, pady=20)
        out_entry = ttk.Entry(out_frame, textvariable=self.output_file, state="readonly")
        out_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        out_btn = ttk.Button(out_frame, text="Enregistrer sous...", command=self.select_output_file, bootstyle="secondary")
        out_btn.pack(side=LEFT)
        self.simple_convert_button = ttk.Button(parent, text="Lancer la Conversion Simple", command=self.start_simple_conversion_thread, bootstyle="primary")
        self.simple_convert_button.pack(pady=20, fill=X, ipady=15)

    def create_query_tab(self, parent):
        # --- 2. Constructeur de requêtes ---
        builder_frame = ttk.Labelframe(parent, text="2. Constructeur de requêtes", padding="10")
        builder_frame.pack(fill=X, pady=5)
        
        helper_row = ttk.Frame(builder_frame)
        helper_row.pack(fill=X, pady=2)
        self.attr_combo = ttk.Combobox(helper_row, state="readonly", width=25)
        self.attr_combo.pack(side=LEFT, padx=5, fill=X, expand=YES)
        self.attr_combo.set("Attribut (Chargez un fichier)")
        operators = ['==', '!=', '>', '>=', '<', '<=', 'in', 'not in', 'str.contains']
        self.op_combo = ttk.Combobox(helper_row, values=operators, state="readonly", width=10)
        self.op_combo.pack(side=LEFT, padx=5)
        self.op_combo.current(0)
        self.val_entry = ttk.Entry(helper_row, width=30)
        self.val_entry.pack(side=LEFT, padx=5, fill=X, expand=YES)
        
        button_row = ttk.Frame(builder_frame)
        button_row.pack(fill=X, pady=5)
        append_btn = ttk.Button(button_row, text="Ajouter ce critère 🔽", command=self.append_criteria, bootstyle="success-outline")
        append_btn.pack(side=LEFT, padx=5, fill=X, expand=YES)
        and_btn = ttk.Button(button_row, text="AND", command=lambda: self.append_logic(" and "), bootstyle="info-outline")
        and_btn.pack(side=LEFT, padx=5, fill=X, expand=YES)
        or_btn = ttk.Button(button_row, text="OR", command=lambda: self.append_logic(" or "), bootstyle="info-outline")
        or_btn.pack(side=LEFT, padx=5, fill=X, expand=YES)
        paren_open_btn = ttk.Button(button_row, text="(", command=lambda: self.append_logic(" ( "), bootstyle="secondary-outline")
        paren_open_btn.pack(side=LEFT, padx=5)
        paren_close_btn = ttk.Button(button_row, text=")", command=lambda: self.append_logic(" ) "), bootstyle="secondary-outline")
        paren_close_btn.pack(side=LEFT, padx=5)
        clear_btn = ttk.Button(button_row, text="Effacer", command=self.clear_staged_query, bootstyle="danger-outline")
        clear_btn.pack(side=LEFT, padx=5)
        
        self.staged_query_entry = ttk.Entry(builder_frame, font=("Courier", 10))
        self.staged_query_entry.pack(fill=X, pady=5, ipady=5)
        
        # --- NOUVEAU WIDGET (Nom de Fichier) ---
        filename_frame = ttk.Labelframe(builder_frame, text="Nom du Fichier (optionnel)", padding="5")
        filename_frame.pack(fill=X, pady=5)
        self.filename_entry = ttk.Entry(filename_frame, font=("Calibri", 10))
        self.filename_entry.pack(fill=X, ipady=2)
        # --- FIN NOUVEAU WIDGET ---

        add_btn = ttk.Button(builder_frame, text="Ajouter la requête complète à la liste ⬇️", command=self.add_query_to_list, bootstyle="success")
        add_btn.pack(fill=X, pady=5, ipady=5)

        # --- 3. Liste des requêtes ---
        list_frame = ttk.Labelframe(parent, text="3. Fichiers GeoJSON à générer", padding="10")
        list_frame.pack(fill=BOTH, expand=YES, pady=5)
        cols = ('id', 'query')
        self.query_tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=4)
        self.query_tree.heading('id', text='Fichier') # Le nom est maintenant personnalisable
        self.query_tree.heading('query', text='Requête')
        self.query_tree.column('id', width=150, anchor=tk.W)
        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.query_tree.yview)
        self.query_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.query_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        remove_btn = ttk.Button(list_frame, text="Retirer", command=self.remove_selected_query, bootstyle="danger")
        remove_btn.pack(side=RIGHT, padx=5, fill=Y)

        # --- 4. Dossier de sortie ---
        out_folder_frame = ttk.Labelframe(parent, text="4. Dossier de sortie", padding="10")
        out_folder_frame.pack(fill=X, pady=5)
        out_entry = ttk.Entry(out_folder_frame, textvariable=self.output_folder, state="readonly")
        out_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        out_btn = ttk.Button(out_folder_frame, text="Parcourir...", command=self.select_output_folder, bootstyle="secondary")
        out_btn.pack(side=LEFT)

        # --- 5. Bouton de lancement ---
        self.query_convert_button = ttk.Button(parent, text="Générer les Fichiers par Requête", command=self.start_query_conversion_thread, bootstyle="primary")
        self.query_convert_button.pack(pady=10, fill=X, ipady=15)

    def create_status_frame(self, parent):
        self.progress_bar = ttk.Progressbar(parent, mode="indeterminate")
        self.progress_bar.pack(fill=X, pady=(5, 0))
        self.status_label = ttk.Label(parent, text="Prêt. Sélectionnez un fichier et un mode.", bootstyle="info")
        self.status_label.pack(fill=X, pady=5)

    # --- Logique de base (commune) ---

    def select_input_file(self):
        filepath = filedialog.askopenfilename(title="Ouvrir un Shapefile", filetypes=[("Fichiers Shapefile", "*.shp")])
        if filepath:
            self.input_path.set(filepath)
            self.status_label.config(text="Fichier chargé. Vous pouvez lancer une conversion simple ou charger les attributs.", bootstyle="info")
            out_path = os.path.splitext(filepath)[0] + ".geojson"
            self.output_file.set(out_path)
            self.attr_combo.set("Attribut (Cliquez sur 'Charger')")
            self.available_attributes = []
            self.queries_list = [] # Réinitialise la liste de tuples
            self.query_tree.delete(*self.query_tree.get_children())

    def load_attributes(self):
        in_path = self.input_path.get()
        if not in_path:
            Messagebox.show_error("Aucun fichier", "Veuillez d'abord sélectionner un fichier Shapefile.")
            return
        try:
            self.status_label.config(text="Lecture des attributs...", bootstyle="info")
            with fiona.open(in_path) as src:
                self.available_attributes = list(src.schema['properties'].keys())
            self.attr_combo['values'] = self.available_attributes
            self.attr_combo.current(0)
            self.status_label.config(text=f"{len(self.available_attributes)} attributs chargés. Prêt pour les requêtes.", bootstyle="success")
        except Exception as e:
            Messagebox.show_error("Erreur de lecture", f"Impossible de lire les attributs du fichier : {e}")

    # --- Logique Onglet 1: Conversion Simple ---

    def select_output_file(self):
        filepath = filedialog.asksaveasfilename(title="Enregistrer en GeoJSON", filetypes=[("Fichiers GeoJSON", "*.geojson")], defaultextension=".geojson")
        if filepath:
            self.output_file.set(filepath)

    def start_simple_conversion_thread(self):
        in_path = self.input_path.get()
        out_path = self.output_file.get()
        if not in_path or not out_path:
            Messagebox.show_error("Champs manquants", "Veuillez spécifier un fichier d'entrée ET un fichier de sortie.")
            return
        self.start_feedback()
        threading.Thread(target=self.run_simple_conversion, args=(in_path, out_path), daemon=True).start()

    def run_simple_conversion(self, in_path, out_path):
        try:
            self.after(0, self.update_status, f"Lecture de {os.path.basename(in_path)}...")
            gdf = gpd.read_file(in_path)
            self.after(0, self.update_status, f"Écriture de {os.path.basename(out_path)}...")
            gdf.to_file(out_path, driver='GeoJSON')
            self.after(0, self.on_conversion_success, f"Conversion simple terminée !\nFichier : {out_path}")
        except Exception as e:
            self.after(0, self.on_conversion_error, str(e))

    # --- Logique Onglet 2: Extraction par Requête (MODIFIÉE) ---

    def _format_criteria(self):
        attr = self.attr_combo.get()
        op = self.op_combo.get()
        val = self.val_entry.get()
        if not attr or not op or not val or attr == "Attribut (Chargez un fichier)":
            Messagebox.show_warning("Champs requis", "Veuillez charger les attributs et remplir les 3 champs (attribut, opérateur, valeur).")
            return None
        if op in ('in', 'not in'):
            items = [f'"{item.strip()}"' for item in val.split(',')]
            val_formatted = f"[{', '.join(items)}]"
            return f"(`{attr}` {op} {val_formatted})"
        else:
            return f"(`{attr}` {op} {val})"

    def append_criteria(self):
        criteria_string = self._format_criteria()
        if criteria_string:
            self.staged_query_entry.insert(tk.END, criteria_string)

    def append_logic(self, logic_string):
        self.staged_query_entry.insert(tk.END, logic_string)

    def clear_staged_query(self):
        self.staged_query_entry.delete(0, tk.END)

    def add_query_to_list(self):
        """Prend la requête ET le nom de fichier et les ajoute à la liste."""
        query_string = self.staged_query_entry.get()
        if not query_string:
            Messagebox.show_warning("Requête vide", "Veuillez construire une requête avant de l'ajouter.")
            return
        
        filename = self.filename_entry.get().strip()
        existing_files = {f for f, q in self.queries_list}

        if not filename:
            # Nom de fichier vide : numérotation automatique
            file_id = 1
            while f"{file_id}.geojson" in existing_files:
                file_id += 1
            filename = f"{file_id}.geojson"
        else:
            # Nom de fichier fourni : nettoyer et valider
            if not filename.endswith('.geojson'):
                filename += ".geojson"
            # Enlever les caractères invalides pour un nom de fichier
            filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
            
            if filename in existing_files:
                Messagebox.show_error("Nom dupliqué", f"Le nom de fichier '{filename}' est déjà dans la liste.")
                return

        # Ajouter le tuple (nom_fichier, requete)
        self.queries_list.append((filename, query_string))
        self.query_tree.insert('', END, values=(filename, query_string))
        
        # Vider les champs
        self.staged_query_entry.delete(0, tk.END)
        self.filename_entry.delete(0, tk.END)

    def remove_selected_query(self):
        """Retire la requête de la liste et de l'arbre (logique modifiée)."""
        selected_items = self.query_tree.selection()
        if not selected_items: return
        
        # On doit supprimer de la fin vers le début pour ne pas fausser les indices
        indices_to_remove = sorted([self.query_tree.index(item) for item in selected_items], reverse=True)
        
        for index in indices_to_remove:
            self.queries_list.pop(index) # Retirer le tuple (nom, requete) de la liste
            
        # Reconstruire l'arbre à partir de la liste (plus simple)
        self.query_tree.delete(*self.query_tree.get_children())
        for (filename, query_string) in self.queries_list:
            self.query_tree.insert('', END, values=(filename, query_string))

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Choisir un dossier de sortie pour les requêtes")
        if folder:
            self.output_folder.set(folder)

    def start_query_conversion_thread(self):
        in_path = self.input_path.get()
        out_folder = self.output_folder.get()
        if not in_path or not out_folder:
            Messagebox.show_error("Champs manquants", "Veuillez spécifier un fichier d'entrée ET un dossier de sortie.")
            return
        if not self.queries_list:
            Messagebox.show_error("Aucune requête", "Veuillez ajouter au moins une requête.")
            return
        
        self.start_feedback()
        # On passe une copie de la liste de tuples
        queries_to_run = list(self.queries_list)
        threading.Thread(target=self.run_query_conversion, args=(in_path, out_folder, queries_to_run), daemon=True).start()

    def run_query_conversion(self, in_path, out_folder, queries_to_run):
        """Exécute la liste de requêtes (logique modifiée)."""
        try:
            self.after(0, self.update_status, f"Lecture de {os.path.basename(in_path)} (peut être long)...")
            gdf = gpd.read_file(in_path)
            
            # Conversion de type (basée sur la solution précédente)
            colonnes_a_convertir = set()
            for (filename, q) in queries_to_run:
                if '>' in q or '<' in q:
                    try:
                        col = re.findall(r'`([^`]+)`', q) # Trouve tous les noms entre backticks
                        colonnes_a_convertir.update(col)
                    except Exception: pass # Ignore les erreurs de regex
            
            for col_name in colonnes_a_convertir:
                if col_name in gdf.columns and gdf[col_name].dtype == 'object':
                    print(f"Conversion de la colonne '{col_name}' en numérique...")
                    gdf[col_name] = pd.to_numeric(gdf[col_name], errors='coerce')

            fichiers_crees = 0
            
            # Boucle sur la liste de tuples (nom_fichier, requete)
            for i, (filename, query_string) in enumerate(queries_to_run, start=1):
                self.after(0, self.update_status, f"Exécution {i}/{len(queries_to_run)}: {filename}...")
                try:
                    gdf_filtre = gdf.query(query_string) 
                    if gdf_filtre.empty: 
                        print(f"Avertissement : La requête '{query_string}' n'a retourné aucun résultat.")
                        continue
                    
                    # Utilise le nom de fichier personnalisé
                    output_path = os.path.join(out_folder, filename) 
                    gdf_filtre.to_file(output_path, driver='GeoJSON')
                    fichiers_crees += 1
                except Exception as e_query:
                    print(f"Erreur requête '{query_string}' (Fichier: {filename}): {e_query}")

            msg_succes = f"Extraction terminée. {fichiers_crees} fichiers créés dans :\n{out_folder}"
            self.after(0, self.on_conversion_success, msg_succes)
            
        except Exception as e:
            self.after(0, self.on_conversion_error, str(e))

    # --- Logique de Feedback (commune) ---

    def start_feedback(self):
        self.progress_bar.start()
        self.status_label.config(text="Traitement en cours...", bootstyle="warning")
        self.simple_convert_button.config(state="disabled")
        self.query_convert_button.config(state="disabled")

    def stop_feedback(self):
        self.progress_bar.stop()
        self.simple_convert_button.config(state="normal")
        self.query_convert_button.config(state="normal")

    def update_status(self, text):
        self.status_label.config(text=text)

    def on_conversion_success(self, success_message):
        self.stop_feedback()
        self.status_label.config(text="Opération terminée.", bootstyle="success")
        Messagebox.show_info("Conversion terminée", success_message)

    def on_conversion_error(self, error_message):
        self.stop_feedback()
        self.status_label.config(text="Échec de l'opération.", bootstyle="danger")
        Messagebox.show_error("Erreur de conversion", f"Une erreur est survenue :\n\n{error_message}")


if __name__ == "__main__":
    app = ShpMultiToolApp()
    app.mainloop()