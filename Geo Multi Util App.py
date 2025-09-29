import tkinter as tk
from tkinter import messagebox, ttk, colorchooser
import subprocess
import re
import platform
import os
from glob import glob
import sys
import random
import time

# Conditional import for Windows console minimization
if platform.system() == "Windows":
    import ctypes

# --- Configuration ---
LAUNCHER_FOLDER_NAME = "Program Launcher"

# --- Utility Functions for App Launcher (Unchanged) ---

def clean_file_path_logic(relative_path):
    """
    Processes the relative file path to extract ONLY the cleaned file name.
    """
    DISPLAY_EXTENSIONS = ['.txt', '.bat', '.ini', '.py', '.url', '.website'] 
    segments = [s.strip() for s in relative_path.split(os.sep) if s.strip()]
    file_name = segments[-1] if segments else ""
    cleaned_name = file_name
    
    if cleaned_name:
        if cleaned_name.lower().endswith('.lnk'):
            cleaned_name = cleaned_name[:-4]
        
        parts = cleaned_name.split('.')
        if len(parts) > 1:
            extension = '.' + parts[-1].lower()
            if extension not in DISPLAY_EXTENSIONS:
                cleaned_name = '.'.join(parts[:-1])
            
    return cleaned_name

def load_launcher_apps(script_dir):
    """
    Scans the designated folder recursively for files and stores them 
    using their cleaned names as keys.
    """
    launcher_path = os.path.join(script_dir, LAUNCHER_FOLDER_NAME)
    app_data = {} 
    
    if not os.path.exists(launcher_path):
        return app_data, f"Error: '{LAUNCHER_FOLDER_NAME}' folder not found at {launcher_path}"

    search_patterns = ['*.exe', '*.lnk', '*.bat', '*.com', '*.cmd', 
                       '*.txt', '*.py', '*.ini', 
                       '*.url', '*.website']
    
    for pattern in search_patterns:
        for full_path in glob(os.path.join(launcher_path, '**', pattern), recursive=True):
            relative_path = os.path.relpath(full_path, launcher_path)
            cleaned_name = clean_file_path_logic(relative_path)
            full_directory_path = os.path.dirname(full_path)
            display_path = full_directory_path.replace(os.sep, '\\')
            if not display_path.endswith('\\'):
                display_path += '\\'

            if cleaned_name and cleaned_name not in app_data:
                 app_data[cleaned_name] = {
                     'path': full_path,
                     'folder_structure': display_path
                 }

    return app_data, None

# --- Utility Functions for Network Information (Unchanged) ---

def get_network_info():
    """Retrieves network information."""
    if platform.system() == "Windows":
        command = "ipconfig /all"
    elif platform.system() == "Linux":
        command = "ip a"
    elif platform.system() == "Darwin": # macOS
        command = "ifconfig"
    else:
        return {"Error": {"ipv4": "OS Not Supported", "mac": "OS Not Supported"}}
        
    output, error = run_command(command)
    
    if error:
        return {"Error": {"ipv4": f"Command Failed: {error}", "mac": ""}}

    all_adapters = {}
    current_adapter_name = "N/A"
    
    if platform.system() == "Windows":
        adapter_name_pattern = re.compile(r"adapter ([^:]+):") 
        ipv4_pattern = re.compile(r"IPv4 Address[.\s]*: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
        mac_pattern = re.compile(r"Physical Address[.\s]*: ([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})")
        
        lines = output.split('\n')
        all_adapters[current_adapter_name] = {"ipv4": "Not Found", "mac": "Not Found"}

        for line in lines:
            line = line.strip()

            adapter_match = adapter_name_pattern.search(line)
            if adapter_match:
                current_adapter_name = adapter_match.group(1).strip()
                all_adapters[current_adapter_name] = {"ipv4": "Not Found", "mac": "Not Found"}
                continue

            if current_adapter_name in all_adapters:
                data = all_adapters[current_adapter_name]
                
                ipv4_match = ipv4_pattern.search(line)
                if ipv4_match and data["ipv4"] == "Not Found":
                     ip = ipv4_match.group(1)
                     if ip != '0.0.0.0' and ip != '127.0.0.1':
                        data["ipv4"] = ip

                mac_match = mac_pattern.search(line)
                if mac_match and data["mac"] == "Not Found":
                    data["mac"] = mac_match.group(1).replace(':', '-')
    
    filtered_adapters = {name: data for name, data in all_adapters.items() 
                         if name != "N/A" and (data.get("ipv4") != "Not Found" or data.get("mac") != "Not Found")}
                         
    return filtered_adapters if filtered_adapters else {"No Active Connection": {"ipv4": "N/A", "mac": "N/A"}}

def run_command(command):
    """Executes a shell command and returns the output."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=False,
            **({'creationflags': subprocess.CREATE_NO_WINDOW} if platform.system() == "Windows" else {})
        )
        
        if result.returncode != 0:
            return None, result.stderr.strip()
        
        return result.stdout, None
    except Exception as e:
        return None, f"Error executing command: {e}"

# --- Measurement Conversion Constants ---

LENGTH_CONVERSIONS = {
    "Meter (m)": 1.0, "Kilometer (km)": 1000.0, "Centimeter (cm)": 0.01,
    "Millimeter (mm)": 0.001, "Mile (mi)": 1609.34, "Yard (yd)": 0.9144,
    "Foot (ft)": 0.3048, "Inch (in)": 0.0254
}

LIQUID_CONVERSIONS = {
    "Liter (L)": 1.0, "Milliliter (mL)": 0.001, "Cubic Meter (m³)": 1000.0,
    "US Gallon (gal)": 3.78541, "Imperial Gallon (gal)": 4.54609,
    "US Quart (qt)": 0.946353, "US Pint (pt)": 0.473176
}

WEIGHT_CONVERSIONS = {
    "Kilogram (kg)": 1.0, "Gram (g)": 0.001, "Milligram (mg)": 0.000001,
    "Metric Ton (t)": 1000.0, "Pound (lb)": 0.453592, "Ounce (oz)": 0.0283495
}

SPEED_CONVERSIONS = {
    "Meter/second (m/s)": 1.0, 
    "Kilometer/hour (km/h)": 1 / 3.6, 
    "Miles/hour (mph)": 0.44704,      
    "Foot/second (ft/s)": 0.3048,
    "Knot (kn)": 0.514444
}

TEMPERATURE_UNITS = ["Celsius (°C)", "Fahrenheit (°F)", "Kelvin (K)"]

CONVERSION_MAP = {
    "Length": LENGTH_CONVERSIONS,
    "Liquid Volume": LIQUID_CONVERSIONS,
    "Weight": WEIGHT_CONVERSIONS, 
    "Speed": SPEED_CONVERSIONS,   
    "Temperature": TEMPERATURE_UNITS
}


# --- Main Application Class ---

class SystemUtilityApp:
    def __init__(self, master):
        self.master = master
        master.title("System Utility, Converter, Customizer, and Pong")
        
        # --- Configurable Style Variables (Default) ---
        # These are used by the Customization Tab and the style application logic
        self.primary_color = "#007BFF"       # Blue for Launch/Convert buttons
        self.secondary_color = "#28A745"     # Green for Copy buttons
        self.background_color = "#F5F5F5"    # Light gray background
        self.card_color = "white"            # White cards for sections
        self.text_color = "#333333"          # Dark text
        self.font_family = 'Segoe UI'       # Default font family

        # Set initial styling on the root window
        self.master.config(padx=10, pady=10, bg=self.background_color)
        
        # Font variables derived from the family
        self.font_large = (self.font_family, 12, 'bold')
        self.font_normal = (self.font_family, 10)
        self.font_normal_small = (self.font_family, 9)

        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        # Data storage
        self.adapter_data = {}
        self.app_data = {} 
        self.base_map = {"Binary": 2, "Octal": 8, "Decimal": 10, "Hex": 16}

        # --- CRITICAL: Initialize status_var and is_updating BEFORE setup functions ---
        self.status_var = tk.StringVar(value="Ready.")
        self.is_updating = False # Flag for color picker to prevent infinite loops
        
        # Measurement Converter Variables
        self.conversion_type_var = tk.StringVar(value=list(CONVERSION_MAP.keys())[0])
        self.input_unit_menu = None
        self.output_unit_menu = None
        self.measure_result_value_var = tk.StringVar(value="Select type and units, then enter value.") 
        
        # Pong Game Variables
        self.is_game_running = False
        self.pong_canvas = None
        self.ball = None
        self.paddle_left = None
        self.paddle_right = None
        self.score_left = 0
        self.score_right = 0
        self.score_var = tk.StringVar(value="Player: 0 | CPU: 0")
        self.ball_dir_x = 3
        self.ball_dir_y = 3
        self.ball_speed_multiplier = 1.0

        # Color Picker Variables
        self.rgb_r_var = tk.StringVar(value="0")
        self.rgb_g_var = tk.StringVar(value="0")
        self.rgb_b_var = tk.StringVar(value="0")
        self.hex_var = tk.StringVar(value="#000000")
        
        # --- Create Notebook (Tabbed Interface) ---
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, fill='both', expand=True)

        # --- Tab Frames ---
        # Note: Using tk.Frame ensures background color is controllable by self.background_color
        self.system_tab = tk.Frame(self.notebook, bg=self.background_color)
        self.converter_tab = tk.Frame(self.notebook, bg=self.background_color)
        self.measurement_tab = tk.Frame(self.notebook, bg=self.background_color) 
        self.color_tab = tk.Frame(self.notebook, bg=self.background_color) 
        self.customization_tab = tk.Frame(self.notebook, bg=self.background_color) 
        self.pong_tab = tk.Frame(self.notebook, bg=self.background_color) 

        self.notebook.add(self.system_tab, text='IP-Check & AppLauncher')
        self.notebook.add(self.converter_tab, text='Base Converter')
        self.notebook.add(self.measurement_tab, text='Unit Converter') 
        self.notebook.add(self.color_tab, text='Color Picker') 
        self.notebook.add(self.customization_tab, text='App Customization') 
        self.notebook.add(self.pong_tab, text='Pong Game') 

        # --- Setup Sections ---
        self.setup_network_info_section(self.system_tab)
        self.setup_launcher_section(self.system_tab) 
        self.setup_converter_section(self.converter_tab)
        self.setup_measurement_converter_section(self.measurement_tab)
        self.setup_color_picker_section(self.color_tab) 
        self.setup_customization_section(self.customization_tab)
        self.setup_pong_game(self.pong_tab)
        
        # Status Label: Keep outside the notebook (packed to master)
        tk.Label(master, textvariable=self.status_var, font=(self.font_family, 9, 'italic'), 
                 bg=self.background_color, fg=self.text_color).pack(pady=(10, 0), anchor="w", padx=10)

        # Apply initial styles to ensure all widgets have the current theme
        self.apply_styles()
        
        # Initial data load
        self.load_initial_data()
        
        # Stop game loop if the app is closed
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Clean up game loop on closing the app."""
        if self.is_game_running:
            try:
                self.master.after_cancel(self.pong_game_id)
            except AttributeError:
                pass
        self.master.destroy()
        
    def _get_font(self, size, style='normal'):
        """Helper to dynamically generate font tuples."""
        if style == 'bold':
            return (self.font_family, size, 'bold')
        elif style == 'italic':
            return (self.font_family, size, 'italic')
        return (self.font_family, size)

    # --- Style Application (CRITICAL FIX IMPLEMENTED HERE) ---

    def apply_styles(self):
        """
        Applies current theme settings (colors and font) to all relevant widgets.
        """
        # Update root and notebook backgrounds
        self.master.config(bg=self.background_color)
        
        # Configure Ttk styles for the Notebook (tabs and frames)
        s = ttk.Style()
        s.theme_use('default')
        s.configure('TNotebook', background=self.background_color, borderwidth=0)
        s.configure('TNotebook.Tab', background=self.card_color, foreground=self.text_color, 
                    font=self._get_font(10))
        s.map('TNotebook.Tab', background=[('selected', self.primary_color)], 
              foreground=[('selected', 'white')])
              
        s.configure('TCombobox', fieldbackground=self.card_color, foreground=self.text_color, 
                    selectbackground=self.primary_color, selectforeground='white')

        # Update internal font definitions
        self.font_large = self._get_font(12, 'bold')
        self.font_normal = self._get_font(10)
        self.font_normal_small = self._get_font(9)

        # Iterate through all widgets and update their appearance
        for widget in self.master.winfo_children():
            self._update_widget_style(widget)

    def _update_widget_style(self, widget):
        """
        Recursively applies styles to a widget and its children, safely handling 
        the difference between standard tk and ttk widgets by using try/except.
        """
        
        # Use a try-except block to safely attempt configuration.
        try:
            # Generic updates for common widget types (tk widgets support bg/fg)
            if isinstance(widget, (tk.Frame, tk.LabelFrame, tk.Canvas)):
                # Frame/Canvas/LabelFrame backgrounds
                widget.config(bg=self.background_color)
                if isinstance(widget, tk.LabelFrame):
                    # LabelFrame specific styling
                    widget.config(font=self.font_large, fg=self.text_color, bg=self.card_color)
            
            elif isinstance(widget, tk.Label):
                # Standard Label styling
                if widget.master == self.master: # Status bar
                    widget.config(font=self._get_font(9, 'italic'), bg=self.background_color, fg=self.text_color)
                else:
                    widget.config(font=self.font_normal, bg=self.card_color, fg=self.text_color)
                    
            elif isinstance(widget, tk.Button):
                # Standard Button styling
                button_text = widget.cget('text')
                if button_text in ["Launch Selected", "Convert", "Apply Styles"]:
                    # Primary Buttons
                    widget.config(font=self.font_normal, bg=self.primary_color, fg="white", 
                                activebackground=self.primary_color, activeforeground="white")
                elif button_text in ["Copy", "Start/Restart Game"]:
                    # Secondary Buttons
                    widget.config(font=self.font_normal_small, bg=self.secondary_color, fg="white", 
                                activebackground=self.secondary_color, activeforeground="white")
                else:
                    # Default button styling (like the color pickers)
                    widget.config(font=self.font_normal, bg="#C0C0C0", fg=self.text_color, 
                                activebackground="#A0A0A0")
                                
            elif isinstance(widget, (tk.Entry, tk.Listbox)):
                # Input fields
                widget.config(font=self.font_normal, bg="#EFEFEF", fg=self.text_color)
                
            elif isinstance(widget, tk.OptionMenu):
                # OptionMenu widget and its internal menu button
                widget.config(font=self.font_normal, bg="#E0E0E0", fg=self.text_color, activebackground="#D0D0D0", bd=1, relief=tk.FLAT)
                if 'menu' in widget.config():
                    menu = widget["menu"]
                    menu.config(font=self.font_normal)

        except tk.TclError:
            # CRITICAL FIX: The widget does not support the 'bg', 'fg', or other tk options. 
            # This is expected for ttk widgets (TNotebook, TCombobox, etc.). We safely ignore the error.
            pass
        except Exception as e:
            # Catch other potential configuration errors if necessary
            # print(f"Warning: Could not configure {widget} due to unexpected error: {e}")
            pass

        # Recursive call to handle children
        for child in widget.winfo_children():
            self._update_widget_style(child)
    
    # --- Network Info Methods ---
    
    def setup_network_info_section(self, parent_frame):
        # Frame for Network Info
        net_frame = tk.LabelFrame(parent_frame, text="Network Details", 
                                  font=self.font_large, bg=self.card_color, fg=self.text_color,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        net_frame.pack(pady=15, fill="x", padx=10)
        
        # Data container for labels
        self.network_labels = {}
        
        # Row 0: Adapter Selector
        tk.Label(net_frame, text="Select Adapter:", font=self._get_font(10, 'bold'), 
                 bg=self.card_color, fg=self.text_color).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.adapter_var = tk.StringVar(net_frame)
        self.adapter_var.trace_add("write", lambda *args: self.display_selected_adapter(self.adapter_var.get()))
        
        self.adapter_menu = tk.OptionMenu(net_frame, self.adapter_var, "No Adapters Found")
        self.adapter_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        self.adapter_menu["menu"].config(font=self.font_normal)
        self.adapter_menu.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Row 1: Refresh Button
        tk.Button(net_frame, text="Refresh", command=self.update_network_data,
                  font=self.font_normal_small, bg=self.primary_color, fg="white", bd=0, 
                  padx=5, pady=1, relief=tk.GROOVE, 
                  activebackground="#0056b3", activeforeground="white").grid(row=0, column=2, sticky="e", padx=5)

        # Row 2 & 3: Info Labels (Placeholder creation)
        self.network_labels["ipv4"] = self._create_info_label(net_frame, "IPv4 Address:", "Retrieving...", 2)
        self.network_labels["mac"] = self._create_info_label(net_frame, "MAC Address:", "Retrieving...", 3)

        # Row 4: Copy Button
        tk.Button(net_frame, text="Copy IP", command=self.copy_ipv4,
                  font=self.font_normal_small, bg=self.secondary_color, fg="white", bd=0, 
                  padx=5, pady=1, relief=tk.GROOVE, 
                  activebackground="#4db850", activeforeground="white").grid(row=4, column=0, sticky="w", padx=5, pady=5)
                  
        net_frame.grid_columnconfigure(1, weight=1)

    def _create_info_label(self, parent, key_text, initial_value, row):
        # Key Label (Left, bold)
        tk.Label(parent, text=key_text, font=self._get_font(10, 'bold'), 
                 bg=self.card_color, fg=self.text_color, anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        
        # Value Label (Right, standard font)
        value_label = tk.Label(parent, text=initial_value, font=self.font_normal, 
                               bg=self.card_color, fg=self.text_color, anchor="w")
        value_label.grid(row=row, column=1, sticky="w", padx=5, pady=2, columnspan=2)
        
        return value_label

    def load_initial_data(self):
        """Loads network and launcher data on app startup."""
        self.update_network_data()
        self.app_data, error = load_launcher_apps(self.script_dir)
        if error:
            self.status_var.set(f"Launcher Error: {error}")
        else:
            self.update_app_launcher_dropdown()

    def update_network_data(self):
        """Fetches network data and updates adapter dropdown."""
        self.status_var.set("Fetching network information...")
        self.adapter_data = get_network_info()
        
        adapters = list(self.adapter_data.keys())
        
        # Clear existing menu options
        menu = self.adapter_menu["menu"]
        menu.delete(0, "end")
        
        if adapters:
            for adapter in adapters:
                menu.add_command(label=adapter, 
                                 command=lambda value=adapter: self.adapter_var.set(value))
            
            self.adapter_var.set(adapters[0])
            self.display_selected_adapter(adapters[0])
            self.status_var.set(f"Network data refreshed. Found {len(adapters)} adapters.")
        else:
            self.adapter_var.set("No Adapters Found")
            self.network_labels["ipv4"].config(text="N/A")
            self.network_labels["mac"].config(text="N/A")
            self.status_var.set("Network data refreshed. No active connections found.")


    def display_selected_adapter(self, adapter_name):
        """Updates IPv4 and MAC labels based on selected adapter."""
        data = self.adapter_data.get(adapter_name, {"ipv4": "N/A", "mac": "N/A"})
        
        self.network_labels["ipv4"].config(text=data.get("ipv4", "N/A"))
        self.network_labels["mac"].config(text=data.get("mac", "N/A"))
        self.status_var.set(f"Displaying details for adapter: {adapter_name}")
        
    def copy_ipv4(self):
        """Copies the currently displayed IPv4 address."""
        ipv4 = self.network_labels["ipv4"].cget("text")
        if ipv4 in ["Retrieving...", "N/A"]:
            self.status_var.set("Copy failed: No valid IPv4 address available.")
            return

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(ipv4)
            self.master.update()
            self.status_var.set(f"Copied IPv4: {ipv4} to clipboard.")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy address: {e}")


    # --- Launcher Methods ---

    def setup_launcher_section(self, parent_frame):
        # Frame for Launcher
        launcher_frame = tk.LabelFrame(parent_frame, text=f"Program Launcher (Search for files in '{LAUNCHER_FOLDER_NAME}')", 
                                       font=self.font_large, bg=self.card_color, fg=self.text_color,
                                       padx=15, pady=15, bd=1, relief=tk.RIDGE)
        launcher_frame.pack(pady=15, fill="x", padx=10)
        
        # Row 0: Search/Select
        tk.Label(launcher_frame, text="Search/Select App:", font=self._get_font(10, 'bold'), 
                 bg=self.card_color, fg=self.text_color).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.app_search_var = tk.StringVar()
        self.app_search_var.trace_add("write", self.update_app_suggestions)
        
        # Entry for searching
        self.app_entry = tk.Entry(launcher_frame, textvariable=self.app_search_var, font=self.font_normal, 
                                  bg="#EFEFEF", fg=self.text_color, bd=1, relief=tk.FLAT)
        self.app_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Row 1: Suggestions Listbox
        self.suggestion_listbox = tk.Listbox(launcher_frame, height=5, font=self.font_normal_small,
                                             bg="#EFEFEF", fg=self.text_color, bd=1, relief=tk.FLAT,
                                             exportselection=False)
        self.suggestion_listbox.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.suggestion_listbox.bind('<<ListboxSelect>>', self.select_app_from_list)
        
        # Row 2: Selected App Info
        tk.Label(launcher_frame, text="Selected App Path:", font=self._get_font(10, 'bold'), 
                 bg=self.card_color, fg=self.text_color).grid(row=2, column=0, sticky="w", padx=5, pady=5)
                 
        self.selected_app_folder_var = tk.StringVar(value="N/A")
        self.path_label = tk.Label(launcher_frame, textvariable=self.selected_app_folder_var, 
                                   font=self.font_normal_small, bg=self.card_color, fg=self.text_color, 
                                   anchor="w", wraplength=400)
        self.path_label.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        
        # Row 4: Buttons
        button_frame = tk.Frame(launcher_frame, bg=self.card_color)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="Launch Selected", command=self.launch_application,
                  font=self.font_normal, bg=self.primary_color, fg="white", bd=0, padx=10, pady=5,
                  relief=tk.GROOVE, activebackground="#0056b3", activeforeground="white").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Copy", command=self.copy_folder_structure,
                  font=self.font_normal_small, bg=self.secondary_color, fg="white", bd=0, 
                  padx=5, pady=1, relief=tk.GROOVE, 
                  activebackground="#4db850", activeforeground="white").pack(side=tk.LEFT, padx=5)

        launcher_frame.grid_columnconfigure(1, weight=1)

    def update_app_launcher_dropdown(self):
        """Initial population of the listbox."""
        app_names = sorted(list(self.app_data.keys()))
        self.suggestion_listbox.delete(0, tk.END)
        for name in app_names:
            self.suggestion_listbox.insert(tk.END, name)

    def update_app_suggestions(self, *args):
        """Filters the listbox based on the entry text."""
        search_term = self.app_search_var.get().lower()
        app_names = sorted(list(self.app_data.keys()))
        
        self.suggestion_listbox.delete(0, tk.END)
        for name in app_names:
            if search_term in name.lower():
                self.suggestion_listbox.insert(tk.END, name)

    def select_app_from_list(self, event):
        """Updates the selected app path when an item in the listbox is clicked."""
        selected_indices = self.suggestion_listbox.curselection()
        if not selected_indices:
            return

        selected_name = self.suggestion_listbox.get(selected_indices[0])
        app_info = self.app_data.get(selected_name)
        
        if app_info:
            self.selected_app_folder_var.set(app_info['folder_structure'] + selected_name)
            self.status_var.set(f"Selected: {selected_name}")
        else:
            self.selected_app_folder_var.set("N/A")

    def copy_folder_structure(self):
        """Copies the selected app's full path."""
        full_path = self.selected_app_folder_var.get()
        if full_path in ["N/A", ""]:
            self.status_var.set("Copy failed: No app selected or path unavailable.")
            return

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(full_path)
            self.master.update()
            self.status_var.set(f"Copied Path: {full_path} to clipboard.")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy path: {e}")

    def launch_application(self):
        """Launches the currently selected application."""
        selected_name = self.suggestion_listbox.get(self.suggestion_listbox.curselection()) if self.suggestion_listbox.curselection() else None
        
        if not selected_name:
            messagebox.showwarning("Launch Error", "Please select an application from the list.")
            return
            
        app_info = self.app_data.get(selected_name)
        if not app_info:
            messagebox.showwarning("Launch Error", f"Details for '{selected_name}' not found.")
            return

        try:
            full_path = app_info['path']
            # Using Popen to launch without waiting
            subprocess.Popen([full_path], 
                             **({'creationflags': subprocess.CREATE_NO_WINDOW} if platform.system() == "Windows" else {}))
            self.status_var.set(f"Successfully launched: {selected_name}")
        except FileNotFoundError:
            self.status_var.set(f"Launch failed: File not found at {full_path}")
            messagebox.showerror("Launch Error", f"File not found: {full_path}")
        except Exception as e:
            self.status_var.set(f"Launch failed: {e}")
            messagebox.showerror("Launch Error", f"An error occurred during launch: {e}")

    # --- Base Converter Methods ---
    
    def setup_converter_section(self, parent_frame):
        # Frame for Base Converter
        converter_frame = tk.LabelFrame(parent_frame, text="Number Base Converter (Binary, Octal, Decimal, Hex)", 
                                  font=self.font_large, bg=self.card_color, fg=self.text_color,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        converter_frame.pack(pady=15, fill="x", padx=10)

        # Variables
        self.input_value_var = tk.StringVar()
        self.input_base_var = tk.StringVar(value="Decimal")
        self.output_base_var = tk.StringVar(value="Hex")
        self.converted_value_var = tk.StringVar(value="Result will appear here.")
        
        bases = list(self.base_map.keys())

        # Row 0: Input Value & Input Base
        tk.Label(converter_frame, text="Input Value:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        tk.Entry(converter_frame, textvariable=self.input_value_var, font=self.font_normal, 
                 bg="#EFEFEF", fg=self.text_color, bd=1, relief=tk.FLAT).grid(row=1, column=0, sticky="ew", padx=5)

        tk.Label(converter_frame, text="Input Base:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color).grid(row=0, column=1, sticky="w", padx=5, pady=5)
                 
        input_base_menu = tk.OptionMenu(converter_frame, self.input_base_var, *bases)
        input_base_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        input_base_menu["menu"].config(font=self.font_normal)
        input_base_menu.grid(row=1, column=1, sticky="ew", padx=5)

        # Row 0/1: Output Base & Convert Button
        tk.Label(converter_frame, text="Output Base:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        output_base_menu = tk.OptionMenu(converter_frame, self.output_base_var, *bases)
        output_base_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        output_base_menu["menu"].config(font=self.font_normal)
        output_base_menu.grid(row=1, column=2, sticky="ew", padx=5)
        
        tk.Button(converter_frame, text="Convert", command=self.convert_number,
                  font=self.font_normal, bg=self.primary_color, fg="white", bd=0, padx=10, pady=5,
                  relief=tk.GROOVE, activebackground="#0056b3", activeforeground="white").grid(row=1, column=3, sticky="e", padx=5)

        # Row 2/3: Result & Copy Button
        tk.Label(converter_frame, text="Converted Value:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color).grid(row=2, column=0, sticky="w", padx=5, pady=5)
                 
        self.result_label = tk.Label(converter_frame, textvariable=self.converted_value_var, 
                                     font=('Consolas', 10, 'bold'), 
                                     bg="#DEDEDE", fg="#000000", anchor="w", padx=5, pady=5, relief=tk.SUNKEN)
        self.result_label.grid(row=3, column=0, sticky="ew", padx=5, columnspan=3) 

        tk.Button(converter_frame, text="Copy", command=self.copy_converted_value,
                  font=self.font_normal_small, bg=self.secondary_color, fg="white", bd=0, 
                  padx=5, pady=1, relief=tk.GROOVE, 
                  activebackground="#4db850", activeforeground="white").grid(row=3, column=3, sticky="w", padx=5)


        converter_frame.grid_columnconfigure(0, weight=1)
        converter_frame.grid_columnconfigure(1, weight=1)
        converter_frame.grid_columnconfigure(2, weight=1)
        converter_frame.grid_columnconfigure(3, weight=0)
        
    def convert_number(self):
        """Converts the input number between the selected bases."""
        input_str = self.input_value_var.get().strip()
        input_base_name = self.input_base_var.get()
        output_base_name = self.output_base_var.get()
        
        self.result_label.config(relief=tk.SUNKEN, bg="#DEDEDE")

        if not input_str:
            self.converted_value_var.set("Error: Please enter a value.")
            self.result_label.config(bg="#FFCCCC")
            self.status_var.set("Base conversion failed: Empty input.")
            return

        input_base = self.base_map[input_base_name]
        output_base = self.base_map[output_base_name]

        try:
            # 1. Convert input to decimal (base 10)
            decimal_value = int(input_str, input_base)
            
            # 2. Convert from decimal to the output base
            if output_base == 10:
                converted_value = str(decimal_value)
            elif output_base == 2:
                converted_value = bin(decimal_value)[2:] # Remove '0b' prefix
            elif output_base == 8:
                converted_value = oct(decimal_value)[2:] # Remove '0o' prefix
            elif output_base == 16:
                converted_value = hex(decimal_value)[2:].upper() # Remove '0x' prefix and make uppercase
            else:
                raise ValueError("Unsupported output base.")

            self.converted_value_var.set(converted_value)
            self.status_var.set(f"Conversion successful: {input_base_name} to {output_base_name}.")

        except ValueError:
            self.converted_value_var.set(f"Error: Invalid input for base {input_base}.")
            self.result_label.config(bg="#FFCCCC")
            self.status_var.set("Base conversion failed: Invalid input.")
        except Exception as e:
            self.converted_value_var.set(f"An unexpected error occurred: {e}")
            self.result_label.config(bg="#FFCCCC")
            self.status_var.set("Base conversion failed: Unexpected error.")
            
    def copy_converted_value(self):
        """Copies the converted base value to the clipboard."""
        output_value = self.converted_value_var.get()
        
        if "Error" in output_value or "Result will appear here" in output_value:
            self.status_var.set("Copy failed: No valid conversion result available.")
            messagebox.showwarning("Copy Failed", "Cannot copy error message or placeholder text.")
            return

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(output_value)
            self.master.update()
            self.status_var.set(f"Copied '{output_value}' to clipboard.")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy value: {e}")


    # --- Measurement Converter Methods ---

    def setup_measurement_converter_section(self, parent_frame):
        """Builds the GUI elements for the measurement converter, now supporting all types."""
        measure_frame = tk.LabelFrame(parent_frame, text="Unit Converter (Length, Liquid, Weight, Speed, Temp)", 
                                  font=self.font_large, bg=self.card_color, fg=self.text_color,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        measure_frame.pack(pady=15, fill="x", padx=10)

        # Row 0: Conversion Type Selector
        tk.Label(measure_frame, text="Conversion Type:", font=self._get_font(10, 'bold'), 
                 bg=self.card_color, fg=self.text_color).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        conversion_types = list(CONVERSION_MAP.keys())
        self.conversion_type_var.trace_add("write", lambda *args: self.update_units_dropdowns())
        
        conversion_type_menu = tk.OptionMenu(measure_frame, self.conversion_type_var, *conversion_types)
        conversion_type_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        conversion_type_menu["menu"].config(font=self.font_normal)
        conversion_type_menu.grid(row=0, column=1, sticky="ew", padx=5, pady=5, columnspan=3)
        
        # Row 1: Labels for Input Value, Input Unit, Output Unit
        tk.Label(measure_frame, text="Input Value:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.input_unit_label = tk.Label(measure_frame, text="Input Unit:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color)
        self.input_unit_label.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.output_unit_label = tk.Label(measure_frame, text="Output Unit:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color)
        self.output_unit_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        # Row 2: Input Field, Dropdowns, Button
        self.measure_input_value_var = tk.StringVar()
        tk.Entry(measure_frame, textvariable=self.measure_input_value_var, font=self.font_normal, 
                 bg="#EFEFEF", fg="#000000", bd=1, relief=tk.FLAT).grid(row=2, column=0, sticky="ew", padx=5)

        self.input_unit_var = tk.StringVar(measure_frame)
        self.input_unit_menu = tk.OptionMenu(measure_frame, self.input_unit_var, "None")
        self.input_unit_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        self.input_unit_menu["menu"].config(font=self.font_normal)
        self.input_unit_menu.grid(row=2, column=1, sticky="ew", padx=5)
        
        self.output_unit_var = tk.StringVar(measure_frame)
        self.output_unit_menu = tk.OptionMenu(measure_frame, self.output_unit_var, "None")
        self.output_unit_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        self.output_unit_menu["menu"].config(font=self.font_normal)
        self.output_unit_menu.grid(row=2, column=2, sticky="ew", padx=5)

        tk.Button(measure_frame, text="Convert", command=self.convert_measurement,
                  font=self.font_normal, bg=self.primary_color, fg="white", bd=0, padx=10, pady=5,
                  relief=tk.GROOVE, activebackground="#0056b3", activeforeground="white").grid(row=2, column=3, sticky="e", padx=5)

        # Row 3 & 4: Result and Copy Button
        tk.Label(measure_frame, text="Output Value:", font=self.font_normal, 
                 bg=self.card_color, fg=self.text_color).grid(row=3, column=0, sticky="w", padx=5, pady=5)
                 
        self.measure_result_label = tk.Label(measure_frame, textvariable=self.measure_result_value_var, 
                                             font=('Consolas', 10, 'bold'), 
                                             bg="#DEDEDE", fg="#000000", anchor="w", padx=5, pady=5, relief=tk.SUNKEN)
        self.measure_result_label.grid(row=4, column=0, sticky="ew", padx=5, columnspan=3) 

        tk.Button(measure_frame, text="Copy", command=self.copy_converted_measurement, 
                  font=self.font_normal_small, bg=self.secondary_color, fg="white", bd=0, 
                  padx=5, pady=1, relief=tk.GROOVE, 
                  activebackground="#4db850", activeforeground="white").grid(row=4, column=3, sticky="w", padx=5)

        measure_frame.grid_columnconfigure(0, weight=1)
        measure_frame.grid_columnconfigure(1, weight=1)
        measure_frame.grid_columnconfigure(2, weight=1)
        measure_frame.grid_columnconfigure(3, weight=0)
        
        self.update_units_dropdowns()

    def copy_converted_measurement(self):
        """Copies the converted measurement value to the clipboard."""
        output_value = self.measure_result_value_var.get()
        
        if "Error" in output_value or "Select type" in output_value or "Ready to convert" in output_value:
            self.status_var.set("Copy failed: No valid conversion result available.")
            messagebox.showwarning("Copy Failed", "Cannot copy error message or placeholder text.")
            return

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(output_value)
            self.master.update()
            self.status_var.set(f"Copied '{output_value}' to clipboard.")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy value: {e}")


    def convert_measurement(self):
        """Converts the input value based on the selected conversion type and units."""
        input_str = self.measure_input_value_var.get().strip()
        self.measure_result_label.config(relief=tk.SUNKEN, bg="#DEDEDE")

        if not input_str:
            self.measure_result_value_var.set("Error: Please enter a value to convert.")
            self.measure_result_label.config(bg="#FFCCCC")
            self.status_var.set("Measurement conversion failed: Empty input.")
            return

        try:
            input_val = float(input_str)
            input_unit_name = self.input_unit_var.get()
            output_unit_name = self.output_unit_var.get()
            conversion_type = self.conversion_type_var.get()

            if conversion_type in ["Length", "Liquid Volume", "Weight", "Speed"]:
                unit_map = CONVERSION_MAP[conversion_type]
                
                # Convert input to the base unit (Meter, Liter, Kilogram, Meter/second)
                input_factor = unit_map[input_unit_name]
                base_value = input_val * input_factor

                # Convert from the base unit to the output unit
                output_factor = unit_map[output_unit_name]
                converted_val = base_value / output_factor

            elif conversion_type == "Temperature":
                # Handle Temperature conversion (base unit is Celsius)
                
                if input_unit_name == "Celsius (°C)":
                    base_celsius = input_val
                elif input_unit_name == "Fahrenheit (°F)":
                    base_celsius = (input_val - 32) * 5/9
                elif input_unit_name == "Kelvin (K)":
                    base_celsius = input_val - 273.15
                else:
                    raise ValueError("Unknown input temperature unit.")

                # Convert from Celsius (C) to the output unit
                if output_unit_name == "Celsius (°C)":
                    converted_val = base_celsius
                elif output_unit_name == "Fahrenheit (°F)":
                    converted_val = (base_celsius * 9/5) + 32
                elif output_unit_name == "Kelvin (K)":
                    converted_val = base_celsius + 273.15
                else:
                    raise ValueError("Unknown output temperature unit.")
            else:
                raise ValueError("Unknown conversion type.")

            # Display with reasonable precision
            self.measure_result_value_var.set(f"{converted_val:.6f}")
            self.status_var.set(f"Conversion successful: {input_unit_name} to {output_unit_name}.")

        except ValueError as ve:
            error_msg = f"Error: Input '{input_str}' must be a valid number or unit error: {ve}"
            self.measure_result_value_var.set(error_msg)
            self.measure_result_label.config(bg="#FFCCCC")
            self.status_var.set("Measurement conversion failed: Invalid number or unit.")
        except Exception as e:
            self.measure_result_value_var.set(f"An unexpected error occurred: {e}")
            self.measure_result_label.config(bg="#FFCCCC")
            self.status_var.set("Measurement conversion failed: Unexpected error.")


    def update_units_dropdowns(self):
        """Updates the unit dropdown options when the conversion type changes."""
        conversion_type = self.conversion_type_var.get()
        units_data = CONVERSION_MAP.get(conversion_type, {})
        
        if isinstance(units_data, dict):
            unit_names = list(units_data.keys())
        elif isinstance(units_data, list):
            unit_names = units_data
        else:
            unit_names = ["Error"]

        if not unit_names:
            unit_names = ["None Available"]
            
        # Clear existing menu options
        input_menu = self.input_unit_menu["menu"]
        output_menu = self.output_unit_menu["menu"]
        input_menu.delete(0, "end")
        output_menu.delete(0, "end")
        
        # Populate new options
        for unit in unit_names:
            input_menu.add_command(label=unit, 
                                   command=lambda value=unit: self.input_unit_var.set(value))
            output_menu.add_command(label=unit, 
                                    command=lambda value=unit: self.output_unit_var.set(value))
                                    
        # Set default selection
        default_unit = unit_names[0]
        self.input_unit_var.set(default_unit)
        self.output_unit_var.set(default_unit)
        
        # Update labels to provide context for the current conversion type
        self.input_unit_label.config(text=f"Input Unit ({conversion_type}):")
        self.output_unit_label.config(text=f"Output Unit ({conversion_type}):")
        
        # Reset result display
        self.measure_result_value_var.set("Ready to convert...")
        self.measure_result_label.config(bg="#DEDEDE")


    # --- Color Picker Methods ---

    def setup_color_picker_section(self, parent_frame):
        # Frame for Color Picker
        color_frame = tk.LabelFrame(parent_frame, text="Color Converter (RGB <-> HEX)",
                                  font=self.font_large, bg=self.card_color, fg=self.text_color,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        color_frame.pack(pady=15, fill="x", padx=10)
        
        # Variables defined in __init__
        self.color_box = tk.Label(color_frame, text="Preview", width=10, height=3, bg="#000000", fg="white", bd=1, relief=tk.SUNKEN)
        self.color_box.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=5)
        
        # Helper function for RGB rows
        def create_rgb_entry(label_text, var, row):
            tk.Label(color_frame, text=label_text, font=self.font_normal, bg=self.card_color, fg=self.text_color).grid(row=row, column=1, sticky="w", padx=5)
            entry = tk.Entry(color_frame, textvariable=var, width=5, font=self.font_normal, bg="#EFEFEF", fg=self.text_color, bd=1, relief=tk.FLAT)
            entry.grid(row=row, column=2, sticky="w", padx=5, pady=2)
            return entry

        # RGB Input
        self.entry_r = create_rgb_entry("R:", self.rgb_r_var, 0)
        self.entry_g = create_rgb_entry("G:", self.rgb_g_var, 1)
        self.entry_b = create_rgb_entry("B:", self.rgb_b_var, 2)

        # HEX Input
        tk.Label(color_frame, text="HEX:", font=self.font_normal, bg=self.card_color, fg=self.text_color).grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.hex_entry = tk.Entry(color_frame, textvariable=self.hex_var, width=8, font=('Consolas', 10, 'bold'), bg="#EFEFEF", fg=self.text_color, bd=1, relief=tk.FLAT)
        self.hex_entry.grid(row=3, column=2, sticky="w", padx=5, pady=2)
        
        # Buttons
        tk.Button(color_frame, text="RGB -> HEX", command=self.rgb_to_hex, font=self.font_normal_small, bg=self.primary_color, fg="white", bd=0, padx=5, pady=1, relief=tk.GROOVE).grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(color_frame, text="HEX -> RGB", command=self.hex_to_rgb, font=self.font_normal_small, bg=self.primary_color, fg="white", bd=0, padx=5, pady=1, relief=tk.GROOVE).grid(row=4, column=2, sticky="ew", padx=5, pady=5)

        tk.Button(color_frame, text="Pick Color", command=self.choose_color_dialog, font=self.font_normal_small, bg="#C0C0C0", fg=self.text_color, bd=0, padx=5, pady=1, relief=tk.GROOVE).grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        tk.Button(color_frame, text="Copy HEX", command=self.copy_hex_color, font=self.font_normal_small, bg=self.secondary_color, fg="white", bd=0, padx=5, pady=1, relief=tk.GROOVE).grid(row=5, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        color_frame.grid_columnconfigure(3, weight=1)

    def update_color_box(self, hex_color):
        """Updates the color preview box and ensures visibility of text."""
        self.color_box.config(bg=hex_color)
        
        # Simple heuristic to ensure text visibility
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            # Calculate luminance (Y = 0.2126*R + 0.7152*G + 0.0722*B)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            text_color = "black" if luminance > 0.5 else "white"
            self.color_box.config(fg=text_color)
        except:
            self.color_box.config(fg="white") # Default safe color

    def rgb_to_hex(self):
        """Converts RGB values from entries to a HEX code."""
        if self.is_updating: return
        self.is_updating = True
        
        try:
            r = int(self.rgb_r_var.get())
            g = int(self.rgb_g_var.get())
            b = int(self.rgb_b_var.get())
            
            if not all(0 <= val <= 255 for val in [r, g, b]):
                raise ValueError("RGB values must be between 0 and 255.")
                
            hex_output = f'#{r:02x}{g:02x}{b:02x}'.upper()
            self.hex_var.set(hex_output)
            self.update_color_box(hex_output)
            self.status_var.set(f"Converted RGB({r},{g},{b}) to {hex_output}.")
        except ValueError as e:
            self.status_var.set(f"RGB conversion error: {e}")
            messagebox.showerror("Conversion Error", "Invalid RGB input. Must be integers between 0-255.")
        finally:
            self.is_updating = False

    def hex_to_rgb(self):
        """Converts a HEX code to RGB values."""
        if self.is_updating: return
        self.is_updating = True
        
        hex_input = self.hex_var.get().strip().upper()
        if not re.match(r'^#?([0-9A-F]{3}){1,2}$', hex_input):
            self.status_var.set("HEX conversion error: Invalid format.")
            messagebox.showerror("Conversion Error", "Invalid HEX code format.")
            self.is_updating = False
            return
            
        hex_input = hex_input.lstrip('#')
        if len(hex_input) == 3:
            hex_input = ''.join([c*2 for c in hex_input])

        try:
            r = int(hex_input[0:2], 16)
            g = int(hex_input[2:4], 16)
            b = int(hex_input[4:6], 16)
            
            self.rgb_r_var.set(str(r))
            self.rgb_g_var.set(str(g))
            self.rgb_b_var.set(str(b))
            self.hex_var.set(f"#{hex_input}")
            self.update_color_box(f"#{hex_input}")
            self.status_var.set(f"Converted HEX to RGB({r},{g},{b}).")
        except ValueError as e:
            self.status_var.set(f"HEX conversion error: {e}")
        finally:
            self.is_updating = False

    def choose_color_dialog(self):
        """Opens the system color chooser and updates inputs."""
        color_code = colorchooser.askcolor(title="Choose Color")
        if color_code:
            rgb_tuple = color_code[0]
            hex_code = color_code[1]
            
            self.rgb_r_var.set(str(int(rgb_tuple[0])))
            self.rgb_g_var.set(str(int(rgb_tuple[1])))
            self.rgb_b_var.set(str(int(rgb_tuple[2])))
            self.hex_var.set(hex_code.upper())
            self.update_color_box(hex_code)
            self.status_var.set(f"Color chosen: {hex_code.upper()}")

    def copy_hex_color(self):
        """Copies the HEX value to the clipboard."""
        hex_output = self.hex_var.get()
        if len(hex_output) != 7:
            self.status_var.set("Copy failed: No valid HEX value available.")
            return

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(hex_output)
            self.master.update()
            self.status_var.set(f"Copied HEX: {hex_output} to clipboard.")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy address: {e}")
            
    # --- App Customization Tab ---

    def setup_customization_section(self, parent_frame):
        """Builds the GUI elements for dynamic app style customization."""
        custom_frame = tk.LabelFrame(parent_frame, text="Application Style Customization",
                                  font=self.font_large, bg=self.card_color, fg=self.text_color,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        custom_frame.pack(pady=15, fill="x", padx=10)

        # 1. Font Family Selector
        tk.Label(custom_frame, text="1. Select Font Family:", font=self._get_font(10, 'bold'),
                 bg=self.card_color, fg=self.text_color).grid(row=0, column=0, sticky="w", padx=5, pady=5)
                 
        available_fonts = sorted(list(set(['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana', 'Tahoma', 'Segoe UI'])))
        self.font_var = tk.StringVar(value=self.font_family)
        
        # Using ttk.Combobox here is why the original bug occurred, but now it's handled by the fixed _update_widget_style
        font_menu = ttk.Combobox(custom_frame, textvariable=self.font_var, values=available_fonts,
                                 font=self.font_normal, state='readonly')
        font_menu.grid(row=0, column=1, sticky="ew", padx=5, pady=5, columnspan=2)


        # 2. Color Pickers
        
        # Helper function to create color picker row
        def create_color_picker(parent, label_text, color_attr, row):
            tk.Label(parent, text=f"2. {label_text}:", font=self._get_font(10, 'bold'),
                     bg=self.card_color, fg=self.text_color).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            
            # Color preview box
            color_preview = tk.Label(parent, bg=getattr(self, color_attr), width=5, relief=tk.SUNKEN)
            color_preview.grid(row=row, column=1, sticky="w", padx=5)

            # Button to open color dialog
            def choose_color():
                color_code = colorchooser.askcolor(title=f"Choose {label_text}")
                if color_code:
                    setattr(self, color_attr, color_code[1])
                    color_preview.config(bg=color_code[1])

            tk.Button(parent, text=f"Pick {label_text}", command=choose_color, 
                      font=self.font_normal, bg="#C0C0C0", fg=self.text_color, bd=1, 
                      relief=tk.GROOVE, activebackground="#A0A0A0").grid(row=row, column=2, sticky="w", padx=5)
            
            return color_preview

        self.preview_background = create_color_picker(custom_frame, "Background Color", 'background_color', 1)
        self.preview_card = create_color_picker(custom_frame, "Card/Tab Background", 'card_color', 2)
        self.preview_primary = create_color_picker(custom_frame, "Primary Button Color", 'primary_color', 3)
        self.preview_secondary = create_color_picker(custom_frame, "Secondary Button Color", 'secondary_color', 4)
        self.preview_text = create_color_picker(custom_frame, "Text Color", 'text_color', 5)

        # 3. Apply Button
        tk.Button(custom_frame, text="Apply Styles", command=self.apply_custom_styles,
                  font=self._get_font(12, 'bold'), bg=self.primary_color, fg="white", bd=0, padx=15, pady=8,
                  relief=tk.GROOVE, activebackground="#0056b3", activeforeground="white").grid(row=6, column=0, columnspan=3, pady=20)

        custom_frame.grid_columnconfigure(1, weight=1)

    def apply_custom_styles(self):
        """Applies the font variable and calls the master style update method."""
        
        # Update the internal font family variable
        self.font_family = self.font_var.get()
        
        # Update preview boxes to match the currently set colors
        self.preview_background.config(bg=self.background_color)
        self.preview_card.config(bg=self.card_color)
        self.preview_primary.config(bg=self.primary_color)
        self.preview_secondary.config(bg=self.secondary_color)
        self.preview_text.config(bg=self.text_color)
        
        # Apply changes across the whole application
        self.apply_styles()
        self.status_var.set(f"Styles applied! Font: {self.font_family}, Primary Color: {self.primary_color}")

    # --- Pong Game Tab ---

    def setup_pong_game(self, parent_frame):
        """Builds the GUI elements for the Pong game."""
        game_frame = tk.LabelFrame(parent_frame, text="2D Pong Game (Use W/S or UP/DOWN keys to move)",
                                  font=self.font_large, bg=self.card_color, fg=self.text_color,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        game_frame.pack(pady=10, fill="both", expand=True, padx=10)

        # Score Display
        score_label = tk.Label(game_frame, textvariable=self.score_var, font=self._get_font(14, 'bold'),
                               bg=self.card_color, fg=self.text_color)
        score_label.pack(pady=5)
        
        # Start/Restart Button
        tk.Button(game_frame, text="Start/Restart Game", command=self.start_pong_game,
                  font=self.font_normal, bg=self.primary_color, fg="white", bd=0, padx=10, pady=5,
                  relief=tk.GROOVE, activebackground="#0056b3", activeforeground="white").pack(pady=5)

        # Canvas for the game
        self.pong_canvas = tk.Canvas(game_frame, bg="black", width=600, height=400, highlightthickness=0)
        self.pong_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # Bind key events to the canvas
        self.master.bind('w', lambda event: self.move_paddle(self.paddle_left, -15))
        self.master.bind('s', lambda event: self.move_paddle(self.paddle_left, 15))
        self.master.bind('<Up>', lambda event: self.move_paddle(self.paddle_right, -15))
        self.master.bind('<Down>', lambda event: self.move_paddle(self.paddle_right, 15))
        
        self.reset_pong_objects()

    def reset_pong_objects(self):
        """Sets up the initial state of the game objects (paddles and ball)."""
        if not self.pong_canvas: return

        self.pong_canvas.delete("all")
        
        # Dimensions
        W = self.pong_canvas.winfo_width() or 600
        H = self.pong_canvas.winfo_height() or 400
        
        PAD_W, PAD_H = 10, 80
        BALL_SIZE = 15

        # Paddles (Player Left, CPU Right)
        self.paddle_left = self.pong_canvas.create_rectangle(
            20, H/2 - PAD_H/2, 20 + PAD_W, H/2 + PAD_H/2, fill="white"
        )
        self.paddle_right = self.pong_canvas.create_rectangle(
            W - 20 - PAD_W, H/2 - PAD_H/2, W - 20, H/2 + PAD_H/2, fill="white"
        )

        # Ball
        self.ball = self.pong_canvas.create_oval(
            W/2 - BALL_SIZE/2, H/2 - BALL_SIZE/2, W/2 + BALL_SIZE/2, H/2 + BALL_SIZE/2, fill="white"
        )
        
        # Center Line
        self.pong_canvas.create_line(W/2, 0, W/2, H, fill="gray", dash=(5, 5))
        
        self.score_left = 0
        self.score_right = 0
        self.score_var.set("Player: 0 | CPU: 0")
        self.ball_speed_multiplier = 1.0


    def start_pong_game(self):
        """Starts or restarts the game loop."""
        if self.is_game_running:
            # Stop existing loop if running
            try:
                self.master.after_cancel(self.pong_game_id)
            except AttributeError:
                pass

        self.reset_pong_objects()
        
        # Random initial direction
        self.ball_dir_x = random.choice([-1, 1]) * 3
        self.ball_dir_y = random.choice([-1, 1]) * 3
        
        self.is_game_running = True
        self.status_var.set("Pong game started! Use W/S (Left) or UP/DOWN (Right).")
        self.pong_game_loop()

    def move_paddle(self, paddle, direction):
        """Moves a paddle up or down, constrained by the canvas height."""
        if not self.is_game_running: return
        
        coords = self.pong_canvas.coords(paddle)
        H = self.pong_canvas.winfo_height() or 400
        
        new_y1 = coords[1] + direction
        new_y2 = coords[3] + direction
        
        # Check bounds
        if new_y1 >= 0 and new_y2 <= H:
            self.pong_canvas.move(paddle, 0, direction)

    def cpu_ai(self):
        """Simple AI for the right paddle."""
        if not self.is_game_running: return
        
        ball_coords = self.pong_canvas.coords(self.ball)
        paddle_coords = self.pong_canvas.coords(self.paddle_right)
        
        # Center of ball
        ball_center_y = (ball_coords[1] + ball_coords[3]) / 2
        # Center of paddle
        paddle_center_y = (paddle_coords[1] + paddle_coords[3]) / 2
        
        # Simple tracking logic: move towards the ball's Y position
        if ball_center_y < paddle_center_y - 10:
            self.move_paddle(self.paddle_right, -5) # Move up
        elif ball_center_y > paddle_center_y + 10:
            self.move_paddle(self.paddle_right, 5) # Move down


    def pong_game_loop(self):
        """The main game loop, responsible for movement, collision, and scoring."""
        if not self.is_game_running:
            return

        W = self.pong_canvas.winfo_width() or 600
        H = self.pong_canvas.winfo_height() or 400
        
        ball_coords = self.pong_canvas.coords(self.ball)
        ball_x1, ball_y1, ball_x2, ball_y2 = ball_coords
        
        # --- 1. Ball Movement ---
        
        # Apply speed multiplier to direction
        dx = self.ball_dir_x * self.ball_speed_multiplier
        dy = self.ball_dir_y * self.ball_speed_multiplier
        self.pong_canvas.move(self.ball, dx, dy)
        
        # Re-get coordinates after movement
        ball_coords = self.pong_canvas.coords(self.ball)
        ball_x1, ball_y1, ball_x2, ball_y2 = ball_coords

        # --- 2. Wall Collision (Top/Bottom) ---
        if ball_y1 <= 0 or ball_y2 >= H:
            self.ball_dir_y *= -1
            
        # --- 3. Paddle Collision ---
        
        # Left Paddle
        left_coords = self.pong_canvas.coords(self.paddle_left)
        if ball_x1 <= left_coords[2] and ball_y2 >= left_coords[1] and ball_y1 <= left_coords[3] and self.ball_dir_x < 0:
            self.ball_dir_x *= -1
            self.ball_speed_multiplier *= 1.05 # Increase speed slightly
            self.status_var.set("Ball hit left paddle! Speed increased.")

        # Right Paddle (CPU)
        right_coords = self.pong_canvas.coords(self.paddle_right)
        if ball_x2 >= right_coords[0] and ball_y2 >= right_coords[1] and ball_y1 <= right_coords[3] and self.ball_dir_x > 0:
            self.ball_dir_x *= -1
            self.ball_speed_multiplier *= 1.05 # Increase speed slightly
            self.status_var.set("Ball hit right paddle! Speed increased.")

        # --- 4. Scoring (Left/Right Boundaries) ---
        if ball_x1 < 0:
            # CPU (Right) scores
            self.score_right += 1
            self.score_var.set(f"Player: {self.score_left} | CPU: {self.score_right}")
            self.reset_ball()
            
        elif ball_x2 > W:
            # Player (Left) scores
            self.score_left += 1
            self.score_var.set(f"Player: {self.score_left} | CPU: {self.score_right}")
            self.reset_ball()

        # --- 5. CPU AI ---
        self.cpu_ai()

        # --- 6. Next Frame ---
        # The game speed is controlled by this delay (milliseconds)
        delay = 15
        self.pong_game_id = self.master.after(delay, self.pong_game_loop)


    def reset_ball(self):
        """Resets the ball to the center with a reversed X direction and resets speed."""
        W = self.pong_canvas.winfo_width() or 600
        H = self.pong_canvas.winfo_height() or 400
        BALL_SIZE = 15
        
        # Stop the current loop before resetting
        try:
            self.master.after_cancel(self.pong_game_id)
        except AttributeError:
            pass

        # Move ball to center
        self.pong_canvas.coords(self.ball, 
            W/2 - BALL_SIZE/2, H/2 - BALL_SIZE/2, W/2 + BALL_SIZE/2, H/2 + BALL_SIZE/2
        )
        
        # Reverse X direction
        self.ball_dir_x *= -1
        self.ball_dir_y = random.choice([-1, 1]) * random.uniform(2, 4) # Add randomness to Y direction
        self.ball_speed_multiplier = 1.0 # Reset speed
        
        self.status_var.set("Score! Resetting ball position.")
        
        # Pause for a moment, then restart the loop
        self.pong_game_id = self.master.after(1000, self.pong_game_loop)


# --- OS Specific Functions (Unchanged) ---
def minimize_console_window():
    """Minimizes the command prompt/terminal window used to launch the script."""
    if platform.system() == "Windows":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 6)
        except Exception:
            pass

if __name__ == "__main__":
    minimize_console_window()
    
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        messagebox.showwarning("OS Warning", "This application relies on OS-specific commands (for network and launcher) and may not function fully on this operating system.")
        
    root = tk.Tk()
    app = SystemUtilityApp(root)
    root.mainloop()
