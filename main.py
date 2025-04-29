from tkinter import filedialog, messagebox, ttk
import tkinter as tk
import pyodbc
import threading
import csv
import re
import platform
import os
from thread_login import LoginDialog

class SQLApp:
    def __init__(self, root,creds):
        self.root = root
        self.root.title("🎯 Multi-DB SQL Runner")
        self.root.geometry("900x700")

        # Load environment variables
        self.SQL_SERVER = creds["SQL_SERVER"]
        self.USERNAME = creds["USERNAME"]
        self.PASSWORD = creds["PASSWORD"]
        self.DRIVER = creds["DRIVER"]

        self.USE_WINDOWS_AUTH = False

        if not self.SQL_SERVER or not self.PASSWORD or not self.DRIVER:
            raise ValueError("Missing necessary environment variables.")

        # UI themes configuration
        self.themes = {
            "light": {
                "bg": "#f2f2f2", "fg": "black", "btn": "#e0e0e0", "text": "#ffffff", "highlight": "#007acc"
            },
            "dark": {
                "bg": "#2b2b2b", "fg": "#ffffff", "btn": "#444", "text": "#1e1e1e", "highlight": "#00bfff"
            }
        }
        self.theme = "light"
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.grid(row=0, column=0, sticky="nsew")

        self.log_tab = ttk.Frame(self.tab_control)
        self.result_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.log_tab, text="📝 Output Log")
        self.tab_control.add(self.result_tab, text="📊 Query Results")

        self.db_vars = {}
        self.all_databases = []
        self.last_results = []
        self.last_columns = []

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.build_ui()
        self.apply_theme()
        threading.Thread(target=self.load_databases, daemon=True).start()

    def bind_mousewheel(self, widget, target_canvas):
        os_name = platform.system()

        def _on_mousewheel(event):
            if os_name == 'Windows':
                target_canvas.yview_scroll(-1 * int(event.delta / 120), "units")
            elif os_name == 'Darwin':  # macOS
                target_canvas.yview_scroll(-1 * int(event.delta), "units")
            return "break"

        def _on_linux_scroll(event):
            if event.num == 4:
                target_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                target_canvas.yview_scroll(1, "units")
            return "break"

        if os_name in ['Windows', 'Darwin']:
            widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", _on_mousewheel))
            widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))
        else:
            widget.bind("<Enter>", lambda e: (
                widget.bind_all("<Button-4>", _on_linux_scroll),
                widget.bind_all("<Button-5>", _on_linux_scroll)
            ))
            widget.bind("<Leave>", lambda e: (
                widget.unbind_all("<Button-4>"),
                widget.unbind_all("<Button-5>")
            ))

    def build_ui(self):
        # === Main Layout (Notebook) ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # === Create Tabs ===
        self.tab_databases = ttk.Frame(self.notebook)
        self.tab_script = ttk.Frame(self.notebook)
        self.tab_output = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_databases, text="Databases")
        self.notebook.add(self.tab_script, text="SQL Script")
        self.notebook.add(self.tab_output, text="Output")

        self.build_databases_tab()
        self.build_script_tab()
        self.build_output_tab()

    def build_databases_tab(self):
        # Header
        self.title_label = tk.Label(self.tab_databases, text="SQL Script Runner on Multiple Databases", font=("Helvetica", 16, "bold"), pady=10)
        self.title_label.pack(fill=tk.X, padx=10)

        # Top Controls (search, buttons)
        top_frame = tk.Frame(self.tab_databases)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Search DB
        tk.Label(top_frame, text="Search DB:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.update_checkboxes())
        search_entry = tk.Entry(top_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=5)


        # DB List
        db_frame = tk.LabelFrame(self.tab_databases, text="Select Databases", padx=10, pady=10)
        db_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(db_frame)
        scrollbar = ttk.Scrollbar(db_frame, orient="vertical", command=canvas.yview)
        self.checkbox_frame = tk.Frame(canvas)

        self.checkbox_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)


        self.loading_label = tk.Label(self.checkbox_frame, text="🔄 Loading databases...", font=("Helvetica", 12))
        self.loading_label.pack(pady=20)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.bind_mousewheel(canvas, canvas)

    def build_script_tab(self):
        # Script Input Area
        script_frame = tk.LabelFrame(self.tab_script, text="SQL Query / Script", padx=10, pady=10)
        script_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.script_text = tk.Text(script_frame, height=10, wrap="word", font=("Courier New", 10))
        self.script_text.pack(fill=tk.BOTH, expand=True)

        script_btn_frame = tk.Frame(script_frame)
        script_btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(script_btn_frame, text="📁 Upload SQL File", command=self.load_script_file).pack(side=tk.LEFT)
        tk.Button(script_btn_frame, text="🚀 Execute Script", command=self.execute_script, bg="#5cb85c", fg="white").pack(side=tk.RIGHT)
       
    def build_output_tab(self):
        # === Progress & Status ===
        self.progress = ttk.Progressbar(self.tab_output, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        self.status_box = tk.Text(self.tab_output, height=6, state='disabled')
        self.status_box.pack(fill=tk.X, padx=10)

        # === Results Table ===
        result_frame = tk.Frame(self.tab_output)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        vsb = ttk.Scrollbar(result_frame, orient="vertical")
        hsb = ttk.Scrollbar(result_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            result_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        vsb.pack(side=tk.RIGHT, fill='y')
        hsb.pack(side=tk.BOTTOM, fill='x')

        tk.Button(self.tab_output, text="💾 Export Results", command=self.export_results).pack(pady=10)

    def apply_theme(self):
        t = self.themes[self.theme]
        self.root.configure(bg=t["bg"])
        self.title_label.configure(bg=t["highlight"], fg="white")

    def log(self, message):
        self.status_box.configure(state='normal')
        self.status_box.insert(tk.END, message + "\n")
        self.status_box.configure(state='disabled')
        self.status_box.see(tk.END)

    def get_connection_string(self, db_name):
        if self.USE_WINDOWS_AUTH:
            return f'DRIVER={self.DRIVER};SERVER={self.SQL_SERVER};Trusted_Connection=yes;DATABASE={db_name}'
        else:
            return f'DRIVER={self.DRIVER};SERVER={self.SQL_SERVER};UID={self.USERNAME};PWD={self.PASSWORD};DATABASE={db_name}'

    def load_databases(self):
        try:
            conn = pyodbc.connect(self.get_connection_string("master"))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")
            self.all_databases = [row[0] for row in cursor.fetchall()]
            conn.close()
            self.root.after(0, self.update_checkboxes)  
            self.root.after(0, lambda: self.loading_label.destroy()) 
            self.update_checkboxes()
        except Exception as e:
            self.log(f"❌ Error loading DBs: {e}")
            messagebox.showerror("DB Load Error", str(e))

    def update_checkboxes(self):
        search = self.search_var.get().lower()
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.db_vars.clear()

        for db in sorted(self.all_databases):
            if search in db.lower():
                var = tk.BooleanVar()
                self.db_vars[db] = var
                cb = tk.Checkbutton(self.checkbox_frame, text=db, variable=var, anchor='w')
                cb.pack(fill=tk.BOTH, expand=True, anchor='w')

    def load_script_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("SQL files", "*.sql")])
        if file_path:
            with open(file_path, 'r') as file:
                self.script_text.delete(1.0, tk.END)
                self.script_text.insert(tk.END, file.read())
            self.log(f"📁 Loaded script from {file_path}")

    def select_all(self):
        for var in self.db_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.db_vars.values():
            var.set(False)

    def execute_script(self):
        script = self.script_text.get("1.0", tk.END).strip()
        selected_dbs = [db for db, var in self.db_vars.items() if var.get()]

        if not selected_dbs:
            messagebox.showwarning("Select Databases", "Please select at least one database.")
            return
        if not script:
            messagebox.showwarning("Empty Script", "Please write or load a SQL script.")
            return

        self.progress['value'] = 0
        self.progress['maximum'] = len(selected_dbs)
        self.log(f"🚀 Executing on {len(selected_dbs)} DB(s)...")

        threading.Thread(target=self.run_script_on_dbs, args=(selected_dbs, script), daemon=True).start()

    def clear_treeview(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ()
        self.tree["show"] = ""

    def show_results_table(self, columns, rows):
        # Clear previous Treeview content
        self.tree.delete(*self.tree.get_children())

        # Set up new columns
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def export_results(self):
        if not self.last_results:
            messagebox.showinfo("No Data", "There is no data to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.last_columns)
                for row in self.last_results:
                    writer.writerow(row)
            self.log(f"💾 Results exported to {file_path}")

    def run_script_on_dbs(self, dbs, script):
        self.last_results.clear()
        self.last_columns.clear()
        self.clear_treeview()

        # Split script into individual statements using GO delimiter
        statements = [s.strip() for s in re.split(r"\bGO\b", script, flags=re.IGNORECASE) if s.strip()]

        for i, db in enumerate(dbs):
            self.log(f"\n🟦========== Executing on database: {db} ==========")

            try:
                conn = pyodbc.connect(self.get_connection_string(db))
                cursor = conn.cursor()

                for stmt_index, stmt in enumerate(statements, start=1):
                    lower_stmt = stmt.lower()

                    try:
                        cursor.execute(stmt)

                        if lower_stmt.startswith("select"):
                            rows = cursor.fetchall()
                            columns = [desc[0] for desc in cursor.description]

                            # Add 'dbname' to columns once
                            if not self.last_columns:
                                self.last_columns.extend(['dbname']+columns )

                            db_rows = [(db,) + tuple(row)  for row in rows]
                            self.last_results.extend(db_rows)

                            self.log(f"  📊 SELECT returned {len(rows)} row(s)")

                            # Optional: update view after each SELECT
                            self.show_results_table(self.last_columns, self.last_results)

                        else:
                            affected = cursor.rowcount
                            conn.commit()
                            keyword = stmt.strip().split()[0].upper()
                            self.log(f"  🔄 {keyword} affected {affected} row(s)")

                    except Exception as stmt_err:
                        self.log(f"  ⚠️ Statement error:\n    {stmt_err}")

                conn.close()
                self.log(f"\n✅ Finished execution on {db}")

            except Exception as db_err:
                self.log(f"\n❌ Failed on {db}:\n   {db_err}")

            self.log(f"🟨========== Done with {db} ==========\n")
            self.progress['value'] = i + 1
            self.root.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() 

    login = LoginDialog(root)
    root.wait_window(login.top)

    if login.result:
        app = SQLApp(root, login.result)  
        root.deiconify()  
        root.mainloop()
    else:
        root.destroy()
