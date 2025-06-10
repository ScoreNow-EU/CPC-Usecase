#!/usr/bin/env python3
"""
Network Drive Manager
Manages network drive mappings for Cloud PC use case
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import string
import re
import os
import sys

class NetworkDriveManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Drive Manager")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Store original mappings for restoration
        self.original_mappings = {}
        
        self.setup_ui()
        self.refresh_drive_list()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Network Drive Manager", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Operation selection
        operation_frame = ttk.LabelFrame(main_frame, text="Wählen Sie eine Option", padding="10")
        operation_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        operation_frame.columnconfigure(1, weight=1)
        
        self.operation_var = tk.StringVar(value="alternative")
        
        ttk.Radiobutton(operation_frame, text="Alternativen Benutzer mit Netzlaufwerk verbinden", 
                       variable=self.operation_var, value="alternative",
                       command=self.on_operation_change).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Radiobutton(operation_frame, text="Primären Benutzer mit Netzlaufwerk verbinden", 
                       variable=self.operation_var, value="primary",
                       command=self.on_operation_change).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Configuration frame
        self.config_frame = ttk.LabelFrame(main_frame, text="Konfiguration", padding="10")
        self.config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        self.config_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Current mapped drives (for alternative user option)
        self.current_drive_label = ttk.Label(self.config_frame, text="Aktuell gemapptes Laufwerk:")
        self.current_drive_var = tk.StringVar()
        self.current_drive_combo = ttk.Combobox(self.config_frame, textvariable=self.current_drive_var, 
                                               state="readonly", width=10)
        
        # Network path
        ttk.Label(self.config_frame, text="Netzlaufwerk Pfad:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.network_path_var = tk.StringVar()
        self.network_path_entry = ttk.Entry(self.config_frame, textvariable=self.network_path_var)
        self.network_path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # Drive letter selection
        ttk.Label(self.config_frame, text="Laufwerksbuchstabe:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.drive_letter_var = tk.StringVar()
        self.drive_letter_combo = ttk.Combobox(self.config_frame, textvariable=self.drive_letter_var, 
                                              values=[f"{letter}:" for letter in string.ascii_uppercase[2:]], 
                                              state="readonly", width=10)
        self.drive_letter_combo.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Alternative user fields (shown only for alternative user option)
        self.alt_user_label = ttk.Label(self.config_frame, text="Alternativer Benutzer (KID):")
        self.alt_user_var = tk.StringVar()
        self.alt_user_entry = ttk.Entry(self.config_frame, textvariable=self.alt_user_var)
        
        self.password_label = ttk.Label(self.config_frame, text="Passwort:")
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.config_frame, textvariable=self.password_var, show="*")
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.execute_button = ttk.Button(buttons_frame, text="Ausführen", command=self.execute_operation)
        self.execute_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Laufwerke aktualisieren", 
                  command=self.refresh_drive_list).pack(side=tk.LEFT, padx=5)
        
        self.restore_button = ttk.Button(buttons_frame, text="Original wiederherstellen", 
                                        command=self.restore_original, state="disabled")
        self.restore_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Beenden", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_text = tk.Text(status_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        status_frame.rowconfigure(0, weight=1)
        
        # Initialize UI state
        self.on_operation_change()
        
    def on_operation_change(self):
        """Handle operation selection change"""
        is_alternative = self.operation_var.get() == "alternative"
        
        if is_alternative:
            # Show current drive selection
            self.current_drive_label.grid(row=0, column=0, sticky=tk.W, pady=2)
            self.current_drive_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
            
            # Show alternative user fields
            self.alt_user_label.grid(row=3, column=0, sticky=tk.W, pady=2)
            self.alt_user_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
            
            self.password_label.grid(row=4, column=0, sticky=tk.W, pady=2)
            self.password_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
            
            self.execute_button.config(text="Mit alternativem Benutzer verbinden")
        else:
            # Hide current drive selection
            self.current_drive_label.grid_remove()
            self.current_drive_combo.grid_remove()
            
            # Hide alternative user fields
            self.alt_user_label.grid_remove()
            self.alt_user_entry.grid_remove()
            self.password_label.grid_remove()
            self.password_entry.grid_remove()
            
            self.execute_button.config(text="Mit primärem Benutzer verbinden")
    
    def get_mapped_drives(self):
        """Get currently mapped network drives"""
        try:
            result = subprocess.run(['net', 'use'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                drives = {}
                lines = result.stdout.split('\n')
                for line in lines:
                    # Parse net use output
                    match = re.search(r'([A-Z]):.*?\\\\([^\s]+)', line)
                    if match:
                        drive_letter = match.group(1) + ':'
                        network_path = '\\\\' + match.group(2)
                        drives[drive_letter] = network_path
                return drives
            else:
                self.log_status(f"Fehler beim Abrufen der Laufwerke: {result.stderr}")
                return {}
        except Exception as e:
            self.log_status(f"Fehler beim Abrufen der Laufwerke: {str(e)}")
            return {}
    
    def refresh_drive_list(self):
        """Refresh the list of mapped drives"""
        drives = self.get_mapped_drives()
        drive_letters = list(drives.keys())
        self.current_drive_combo['values'] = drive_letters
        
        if drive_letters and not self.current_drive_var.get():
            self.current_drive_var.set(drive_letters[0])
        
        self.log_status(f"Gefundene Netzlaufwerke: {', '.join(drive_letters) if drive_letters else 'Keine'}")
    
    def disconnect_drive(self, drive_letter):
        """Disconnect a network drive"""
        try:
            self.log_status(f"Trenne Laufwerk {drive_letter}...")
            result = subprocess.run(['net', 'use', drive_letter, '/delete'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                self.log_status(f"Laufwerk {drive_letter} erfolgreich getrennt")
                return True
            else:
                self.log_status(f"Fehler beim Trennen von {drive_letter}: {result.stderr}")
                return False
        except Exception as e:
            self.log_status(f"Fehler beim Trennen von {drive_letter}: {str(e)}")
            return False
    
    def connect_drive(self, drive_letter, network_path, username=None, password=None, persistent=True):
        """Connect a network drive"""
        try:
            cmd = ['net', 'use', drive_letter, network_path]
            
            if username and password:
                cmd.extend(['/user:' + username, password])
            
            if persistent:
                cmd.append('/persistent:Yes')
            else:
                cmd.append('/persistent:No')
            
            self.log_status(f"Verbinde {drive_letter} mit {network_path}...")
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                self.log_status(f"Laufwerk {drive_letter} erfolgreich verbunden")
                return True
            else:
                self.log_status(f"Fehler beim Verbinden: {result.stderr}")
                return False
        except Exception as e:
            self.log_status(f"Fehler beim Verbinden: {str(e)}")
            return False
    
    def execute_operation(self):
        """Execute the selected operation"""
        if self.operation_var.get() == "alternative":
            self.execute_alternative_user_connection()
        else:
            self.execute_primary_user_connection()
    
    def execute_alternative_user_connection(self):
        """Execute connection with alternative user"""
        # Validate inputs
        current_drive = self.current_drive_var.get()
        network_path = self.network_path_var.get().strip()
        drive_letter = self.drive_letter_var.get()
        username = self.alt_user_var.get().strip()
        password = self.password_var.get()
        
        if not all([network_path, drive_letter, username, password]):
            messagebox.showerror("Fehler", "Bitte füllen Sie alle Felder aus.")
            return
        
        # Store original mapping for restoration
        if current_drive:
            current_mappings = self.get_mapped_drives()
            if current_drive in current_mappings:
                self.original_mappings[current_drive] = current_mappings[current_drive]
        
        # Disconnect current drive if selected
        if current_drive:
            if not self.disconnect_drive(current_drive):
                return
        
        # Connect with alternative user
        if self.connect_drive(drive_letter, network_path, username, password, persistent=False):
            self.restore_button.config(state="normal")
            self.log_status("✓ Verbindung mit alternativem Benutzer erfolgreich hergestellt!")
            
            # Clear password field for security
            self.password_var.set("")
        else:
            messagebox.showerror("Fehler", "Verbindung fehlgeschlagen. Überprüfen Sie die Eingaben.")
    
    def execute_primary_user_connection(self):
        """Execute connection with primary user"""
        # Validate inputs
        network_path = self.network_path_var.get().strip()
        drive_letter = self.drive_letter_var.get()
        
        if not all([network_path, drive_letter]):
            messagebox.showerror("Fehler", "Bitte füllen Sie alle Felder aus.")
            return
        
        # Disconnect current drive if it exists
        current_mappings = self.get_mapped_drives()
        if drive_letter in current_mappings:
            if not self.disconnect_drive(drive_letter):
                return
        
        # Connect with primary user (persistent)
        if self.connect_drive(drive_letter, network_path, persistent=True):
            self.log_status("✓ Verbindung mit primärem Benutzer erfolgreich hergestellt!")
        else:
            messagebox.showerror("Fehler", "Verbindung fehlgeschlagen. Überprüfen Sie die Eingaben.")
    
    def restore_original(self):
        """Restore original drive mappings"""
        if not self.original_mappings:
            messagebox.showinfo("Information", "Keine ursprünglichen Zuordnungen zum Wiederherstellen vorhanden.")
            return
        
        success = True
        for drive_letter, network_path in self.original_mappings.items():
            # Disconnect current mapping
            self.disconnect_drive(drive_letter)
            
            # Restore original mapping
            if not self.connect_drive(drive_letter, network_path, persistent=True):
                success = False
        
        if success:
            self.log_status("✓ Ursprüngliche Zuordnungen wiederhergestellt!")
            self.original_mappings.clear()
            self.restore_button.config(state="disabled")
        else:
            messagebox.showerror("Fehler", "Fehler beim Wiederherstellen einiger Zuordnungen.")
    
    def log_status(self, message):
        """Log a status message"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

def main():
    # Check if running on Windows
    if os.name != 'nt':
        print("Diese Anwendung ist nur für Windows-Systeme geeignet.")
        sys.exit(1)
    
    root = tk.Tk()
    app = NetworkDriveManager(root)
    root.mainloop()

if __name__ == "__main__":
    main() 