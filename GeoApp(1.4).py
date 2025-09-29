import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import re
import platform
import os
from glob import glob
import sys

# Conditional import for Windows console minimization
if platform.system() == "Windows":
    import ctypes

# --- Configuration ---
LAUNCHER_FOLDER_NAME = "Program Launcher"

# --- Styling & Colors ---
PRIMARY_COLOR = "#007BFF"       # Blue for Launch button / Convert button
SECONDARY_COLOR = "#28A745"     # Green for Copy button
BACKGROUND_COLOR = "#F5F5F5"    # Light gray background
CARD_COLOR = "white"            # White cards for sections
TEXT_COLOR = "#333333"          # Dark text

# --- Utility Functions for App Launcher (NEW/MODIFIED) ---

def clean_file_path_logic(relative_path):
    """
    Processes the relative file path to extract cleaned name and folder structure.
    
    Args:
        relative_path (str): The path relative to the LAUNCHER_FOLDER_NAME.
    
    Returns: 
        tuple: (cleaned_name, folder_structure_display)
    """
    # Extensions that should be kept in the suggested name
    DISPLAY_EXTENSIONS = ['.txt', '.bat', '.ini', '.py']
    
    # Split path by OS separator, removing empty segments
    segments = [s.strip() for s in relative_path.split(os.sep) if s.strip()]

    # Separate folder and file name
    folder_segments = segments[:-1]
    file_name = segments[-1] if segments else ""
    
    # 1. Clean File Name
    cleaned_name = file_name
    
    if cleaned_name:
        # Remove .lnk suffix (case-insensitive)
        if cleaned_name.lower().endswith('.lnk'):
            cleaned_name = cleaned_name[:-4]

        # Handle other extensions
        parts = cleaned_name.split('.')
        if len(parts) > 1:
            extension = '.' + parts[-1].lower()
            if extension not in DISPLAY_EXTENSIONS:
                # Remove extension if it's not one of the allowed ones
                cleaned_name = '.'.join(parts[:-1])
            
    # 2. Format Folder Structure
    # Filter out an initial 'sw' segment if it's present (for robustness)
    structure_filtered = [s for s in folder_segments if s.lower() != 'sw']
    folder_structure_display = ' > '.join(structure_filtered)
    
    return cleaned_name, folder_structure_display

def load_launcher_apps(script_dir):
    """
    Scans the designated folder recursively for files and stores them 
    using their cleaned names as keys.
    """
    launcher_path = os.path.join(script_dir, LAUNCHER_FOLDER_NAME)
    # New structure: {cleaned_name: {'path': full_path, 'folder_structure': folder_structure}}
    app_data = {} 
    
    if not os.path.exists(launcher_path):
        return app_data, f"Error: '{LAUNCHER_FOLDER_NAME}' folder not found at {launcher_path}"

    # Search patterns
    search_patterns = ['*.exe', '*.lnk', '*.bat', '*.com', '*.cmd', 
                       '*.txt', '*.py', '*.ini']
    
    for pattern in search_patterns:
        # glob.glob with recursive=True scans the subfolders
        for full_path in glob(os.path.join(launcher_path, '**', pattern), recursive=True):
            # Get the path relative to the launcher folder
            relative_path = os.path.relpath(full_path, launcher_path)
            
            # Use the new path cleaning logic
            cleaned_name, folder_structure = clean_file_path_logic(relative_path)

            if cleaned_name and cleaned_name not in app_data:
                 app_data[cleaned_name] = {
                     'path': full_path,
                     'folder_structure': folder_structure
                 }

    return app_data, None

# --- Utility Functions for Network Information (Unchanged) ---

def get_network_info():
    """
    Retrieves IPv4 and MAC addresses for ALL active adapters by running 'ipconfig /all'.
    Returns a dictionary keyed by adapter name.
    """
    # Use different commands for different OS
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

    # Dictionary to hold all adapter data: {adapter_name: {ipv4, mac}}
    all_adapters = {}
    current_adapter_name = "N/A"
    
    # Windows/ipconfig parsing
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
    
    # Filter and return results
    filtered_adapters = {name: data for name, data in all_adapters.items() 
                         if name != "N/A" and (data.get("ipv4") != "Not Found" or data.get("mac") != "Not Found")}
                         
    return filtered_adapters if filtered_adapters else {"No Active Connection": {"ipv4": "N/A", "mac": "N/A"}}

def run_command(command):
    """Executes a shell command and returns the output."""
    try:
        # Use subprocess.run for safer and simpler execution if we don't need real-time streaming
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=False,
            # Suppress window creation on Windows if possible
            **({'creationflags': subprocess.CREATE_NO_WINDOW} if platform.system() == "Windows" else {})
        )
        
        if result.returncode != 0:
            # Return error if command failed
            return None, result.stderr.strip()
        
        return result.stdout, None
    except Exception as e:
        return None, f"Error executing command: {e}"

# --- Main Application Class ---

class SystemUtilityApp:
    def __init__(self, master):
        self.master = master
        master.title("Windows System, Utility & Color Picker")
        master.config(padx=10, pady=10, bg=BACKGROUND_COLOR)
        
        # Style variables
        self.font_large = ('Segoe UI', 12, 'bold')
        self.font_normal = ('Segoe UI', 10)
        self.font_normal_small = ('Segoe UI', 9)

        # Directory where the script is running
        self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        # Data storage
        self.adapter_data = {}
        # Stores all found applications: {cleaned_name: {'path': full_path, 'folder_structure': folder_structure}}
        self.app_data = {} 
        
        # Base Converter mapping: Removed numbers from display names
        self.base_map = {"Binary": 2, "Octal": 8, "Decimal": 10, "Hex": 16}

        # --- CRITICAL: Initialize status_var and is_updating BEFORE setup functions ---
        self.status_var = tk.StringVar(value="Ready.")
        # Flag to prevent infinite loops between RGB and HEX updates
        self.is_updating = False 
        # --- End Critical Fix ---

        # --- Create Notebook (Tabbed Interface) ---
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, fill='both', expand=True)

        # --- Tab Frames ---
        self.system_tab = tk.Frame(self.notebook, bg=BACKGROUND_COLOR)
        self.converter_tab = tk.Frame(self.notebook, bg=BACKGROUND_COLOR)
        self.color_tab = tk.Frame(self.notebook, bg=BACKGROUND_COLOR) 

        self.notebook.add(self.system_tab, text='System & Launcher')
        self.notebook.add(self.converter_tab, text='Base Converter')
        self.notebook.add(self.color_tab, text='Color Picker') 

        # --- Setup Sections ---
        self.setup_network_info_section(self.system_tab)
        self.setup_launcher_section(self.system_tab) 
        self.setup_converter_section(self.converter_tab)
        self.setup_color_picker_section(self.color_tab) 
        
        # Status Label: Keep outside the notebook (packed to master)
        tk.Label(master, textvariable=self.status_var, font=('Segoe UI', 9, 'italic'), 
                 bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(pady=(10, 0), anchor="w", padx=10)

        # Initial data load
        self.load_initial_data()

    def setup_network_info_section(self, parent_frame):
        """Builds the GUI elements for the network display."""
        net_frame = tk.LabelFrame(parent_frame, text="Network Adapter Details", 
                                  font=self.font_large, bg=CARD_COLOR, fg=TEXT_COLOR,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        net_frame.pack(pady=15, fill="x", padx=10)
        
        # Dropdown Label
        tk.Label(net_frame, text="Select Adapter:", font=self.font_normal, 
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Dropdown Variable
        self.selected_adapter = tk.StringVar(net_frame)
        self.adapter_options = tk.OptionMenu(net_frame, self.selected_adapter, 'Loading...')
        self.adapter_options.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        self.adapter_options["menu"].config(font=self.font_normal)
        self.adapter_options.grid(row=0, column=1, sticky="ew", padx=5, pady=5, columnspan=2)
        
        # Display Labels (Initialized as 'N/A')
        # IPv4 - Row 1
        self.ipv4_label = self._create_info_label(net_frame, "IPv4 Address:", "N/A", row=1)
        
        # Copy Button for IPv4
        tk.Button(net_frame, text="Copy", command=self.copy_ipv4,
                  font=self.font_normal_small, bg=SECONDARY_COLOR, fg="white", bd=0, 
                  padx=5, pady=1, relief=tk.GROOVE, # Smoother button look
                  activebackground="#4db850", activeforeground="white").grid(row=1, column=2, sticky="w", padx=5)
        
        # MAC Address - Row 2 (IPv6 removed)
        self.mac_label = self._create_info_label(net_frame, "MAC Address:", "N/A", row=2)
        
        # Configure grid weight for the content column
        net_frame.grid_columnconfigure(1, weight=1)

    def _create_info_label(self, parent, key_text, initial_value, row):
        """Helper to create formatted key/value label pairs."""
        # Key Label (Left, bold)
        tk.Label(parent, text=key_text, font=('Segoe UI', 10, 'bold'), 
                 bg=CARD_COLOR, fg=TEXT_COLOR, anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        
        # Value Label (Right, standard font)
        value_label = tk.Label(parent, text=initial_value, font=self.font_normal, 
                               bg=CARD_COLOR, fg="#000000", anchor="w")
        value_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        return value_label

    def load_initial_data(self):
        """Loads network and app data on startup."""
        self.update_network_data()
        self.update_app_launcher_dropdown()

    # --- Network Methods (Unchanged) ---
    
    def update_network_data(self):
        """Fetches network data, updates adapter_data, and populates the dropdown."""
        self.status_var.set("Fetching network information...")
        self.master.update()
        
        self.adapter_data = get_network_info()
        adapter_names = list(self.adapter_data.keys())
        
        # Clear existing menu
        menu = self.adapter_options["menu"]
        menu.delete(0, "end")

        # Repopulate the menu
        if adapter_names and adapter_names != ['Error']:
            for name in adapter_names:
                # Command=lambda is needed to pass the argument 'name' to the function
                menu.add_command(label=name, command=lambda value=name: self.display_selected_adapter(value))
            
            # Set initial selection to the first active adapter
            self.selected_adapter.set(adapter_names[0])
            self.display_selected_adapter(adapter_names[0])
            self.status_var.set("Network adapters loaded.")
        else:
            self.selected_adapter.set(adapter_names[0] if 'Error' in adapter_names else "No Adapters Found")
            menu.add_command(label="No Adapters Found", command=lambda: None)
            self.status_var.set("Could not find any active network adapters.")

    def display_selected_adapter(self, adapter_name):
        """Updates the display labels based on the selected adapter."""
        if adapter_name not in self.adapter_data:
            return
            
        data = self.adapter_data[adapter_name]
        
        self.ipv4_label.config(text=data["ipv4"])
        self.mac_label.config(text=data["mac"])
        
        # Update the StringVar for the OptionMenu to show the currently selected item
        self.selected_adapter.set(adapter_name)
        self.status_var.set(f"Displaying details for: {adapter_name}")
        
    def copy_ipv4(self):
        """Copies the currently displayed IPv4 address to the system clipboard."""
        ip = self.adapter_data.get(self.selected_adapter.get(), {}).get("ipv4", "Not Found")
        
        if ip in ("Not Found", "N/A"):
            self.status_var.set("Copy failed: No valid IPv4 address available.")
            return
            
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(ip)
            self.master.update() # Update clipboard content
            self.status_var.set(f"Copied IPv4: {ip} to clipboard.")
            messagebox.showinfo("Copied", f"IPv4 Address copied to clipboard:\n{ip}")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy address: {e}")


    # --- Launcher Methods (UPDATED FOR PATH CLEANING/DISPLAY) ---

    def setup_launcher_section(self, parent_frame):
        """Builds the GUI elements for the application launcher with search/autocomplete."""
        launcher_frame = tk.LabelFrame(parent_frame, text=f"Program Launcher (Search files in '{LAUNCHER_FOLDER_NAME}')", 
                                       font=self.font_large, bg=CARD_COLOR, fg=TEXT_COLOR,
                                       padx=15, pady=15, bd=1, relief=tk.RIDGE)
        launcher_frame.pack(pady=15, fill="x", padx=10)
        
        # Search Label
        tk.Label(launcher_frame, text="Search App (type name):", font=self.font_normal, 
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Search Entry Field
        self.search_app_var = tk.StringVar(launcher_frame)
        self.search_app_entry = tk.Entry(launcher_frame, textvariable=self.search_app_var, 
                                         font=self.font_normal, bg="#EFEFEF", fg="#000000", 
                                         bd=1, relief=tk.FLAT)
        self.search_app_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Bind key release event to update suggestions
        self.search_app_entry.bind('<KeyRelease>', self.update_app_suggestions)

        # Launch Button
        tk.Button(launcher_frame, text="Launch Selected", command=self.launch_application,
                  font=self.font_normal, bg=PRIMARY_COLOR, fg="white", bd=0, padx=10, pady=5,
                  relief=tk.GROOVE, activebackground="#0056b3", activeforeground="white").grid(row=1, column=1, sticky="e", padx=5, pady=5)
        
        # Listbox for Suggestions (Made smaller)
        self.suggestion_listbox = tk.Listbox(launcher_frame, height=4, font=self.font_normal, 
                                            bg="#EFEFEF", fg=TEXT_COLOR, relief=tk.SUNKEN, highlightthickness=0)
        self.suggestion_listbox.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=2)
        
        # Bind single-click to select from the list
        self.suggestion_listbox.bind('<<ListboxSelect>>', self.select_app_from_list)
        
        # --- Display Sections for Selected App ---
        
        # Suggested Name (Box 1)
        tk.Label(launcher_frame, text="Suggested Name:", font=('Segoe UI', 10, 'bold'), 
                 bg=CARD_COLOR, fg="#000000", anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=5)
                 
        self.suggested_name_var = tk.StringVar(value="Select an app above...")
        self.suggested_name_label = tk.Label(launcher_frame, textvariable=self.suggested_name_var, 
                                             font=('Segoe UI', 12, 'bold'), fg="#0056b3", 
                                             bg="#E0F7FA", anchor="w", padx=5, pady=5, relief=tk.FLAT, bd=1)
        self.suggested_name_label.grid(row=4, column=0, sticky="ew", padx=5, pady=2, columnspan=2)

        # Folder Structure (Box 2)
        tk.Label(launcher_frame, text="Folder Structure:", font=('Segoe UI', 10, 'bold'), 
                 bg=CARD_COLOR, fg="#000000", anchor="w").grid(row=5, column=0, sticky="w", padx=5, pady=5)
                 
        self.folder_structure_var = tk.StringVar(value="...")
        self.folder_structure_label = tk.Label(launcher_frame, textvariable=self.folder_structure_var, 
                                               font=('Consolas', 9), fg="#666666", 
                                               bg="#F0F0F0", anchor="w", padx=5, pady=5, relief=tk.FLAT, bd=1)
        self.folder_structure_label.grid(row=6, column=0, sticky="ew", padx=5, pady=2, columnspan=2)


        launcher_frame.grid_columnconfigure(0, weight=1)
        launcher_frame.grid_columnconfigure(1, weight=0) # Launch button is fixed width


    def update_app_launcher_dropdown(self):
        """Scans the designated folder and populates the app data dictionary."""
        app_data, error = load_launcher_apps(self.script_dir)
        self.app_data = app_data
        
        if error:
            self.status_var.set(error)
            return

        app_names = list(self.app_data.keys())
        if app_names:
            self.search_app_var.set("") # Clear prompt in search box
            self.update_app_suggestions() # Initial population of the listbox
            self.status_var.set(f"Loaded {len(app_names)} files. Start typing to search.")
        else:
            self.search_app_var.set(f"No files found in '{LAUNCHER_FOLDER_NAME}' or its subfolders.")
            self.status_var.set(f"No files found in '{LAUNCHER_FOLDER_NAME}' or its subfolders.")


    def update_app_suggestions(self, event=None):
        """Filters the app list based on the search entry (using cleaned names)."""
        search_term = self.search_app_var.get().strip().lower()
        
        self.suggestion_listbox.delete(0, tk.END) # Clear current list

        # Filter the list of cleaned names
        filtered_apps = []
        all_cleaned_names = sorted(self.app_data.keys())
        
        for name in all_cleaned_names:
            if search_term in name.lower():
                filtered_apps.append(name)

        # Populate the listbox with filtered results
        if filtered_apps:
            for name in filtered_apps:
                self.suggestion_listbox.insert(tk.END, name)
            # Auto-select the first item if the list is filtered
            if len(filtered_apps) > 0:
                self.suggestion_listbox.select_set(0)
                self.select_app_from_list(None) # Manually call update display
        else:
            self.suggestion_listbox.insert(tk.END, "No matching files found...")
            self.suggested_name_var.set("No selection.")
            self.folder_structure_var.set("...")


    def select_app_from_list(self, event):
        """Updates the Suggested Name and Folder Structure displays based on listbox selection."""
        selection = self.suggestion_listbox.curselection()
        
        if selection:
            selected_cleaned_name = self.suggestion_listbox.get(selection[0])
            
            if selected_cleaned_name in self.app_data:
                app_details = self.app_data[selected_cleaned_name]
                
                # Update the Search Entry Field to match the selection
                self.search_app_var.set(selected_cleaned_name)
                
                # Update the Display Boxes
                self.suggested_name_var.set(selected_cleaned_name)
                self.folder_structure_var.set(app_details['folder_structure'] or "Root folder.")
                self.status_var.set(f"Selected: {selected_cleaned_name}")

            else:
                 # Should not happen if app_data and listbox are synced
                self.suggested_name_var.set("Invalid selection.")
                self.folder_structure_var.set("...")
        else:
            # Handle case where user types and list is filtered but nothing is explicitly selected
            pass


    def launch_application(self):
        """Launches the application selected in the search entry/display."""
        cleaned_app_name = self.suggested_name_var.get().strip()

        if cleaned_app_name in self.app_data:
            path = self.app_data[cleaned_app_name]['path']
        else:
            messagebox.showerror("Error", f"File '{cleaned_app_name}' not found. Please select a suggestion.")
            self.status_var.set("Launch failed: Invalid selection.")
            return

        self.status_var.set(f"Attempting to launch: {cleaned_app_name}...")
        self.master.update()

        try:
            # os.startfile is the preferred way to launch files on Windows
            if platform.system() == "Windows":
                 os.startfile(path)
            else:
                 # Generic open command for other OS (may vary)
                 subprocess.Popen(['open', path] if platform.system() == "Darwin" else ['xdg-open', path])
                 
            self.status_var.set(f"Successfully launched: {cleaned_app_name}")
        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found at path: {path}")
            self.status_var.set("Launch failed: File not found.")
        except OSError as e:
            messagebox.showerror("Error", f"OS Error: Could not launch app.\nDetails: {e}")
            self.status_var.set("Launch failed: OS Error.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred.\nDetails: {e}")
            self.status_var.set("Launch failed: Unexpected error.")


    # --- Base Converter Methods (Unchanged) ---
    
    def setup_converter_section(self, parent_frame):
        """Builds the GUI elements for the number base converter."""
        converter_frame = tk.LabelFrame(parent_frame, text="Number Base Converter (Binary, Octal, Decimal, Hex)", 
                                  font=self.font_large, bg=CARD_COLOR, fg=TEXT_COLOR,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        converter_frame.pack(pady=15, fill="x", padx=10)

        # Base Options for Dropdowns (Simplified names)
        base_names = list(self.base_map.keys())

        # Row 0: Labels for Input Value, Input Base, Output Base
        tk.Label(converter_frame, text="Input Value:", font=self.font_normal, 
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Label(converter_frame, text="Input Base:", font=self.font_normal, 
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        tk.Label(converter_frame, text="Output Base:", font=self.font_normal, 
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        # Row 1: Input Field, Dropdowns, Button
        
        # Input Field
        self.input_value_var = tk.StringVar()
        tk.Entry(converter_frame, textvariable=self.input_value_var, font=self.font_normal, 
                 bg="#EFEFEF", fg="#000000", bd=1, relief=tk.FLAT).grid(row=1, column=0, sticky="ew", padx=5)

        # Input Base Selector (Default Decimal)
        self.input_base_name_var = tk.StringVar(converter_frame, value=base_names[2])
        input_menu = tk.OptionMenu(converter_frame, self.input_base_name_var, *base_names)
        input_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        input_menu["menu"].config(font=self.font_normal)
        input_menu.grid(row=1, column=1, sticky="ew", padx=5)
        
        # Output Base Selector (Default Binary)
        self.output_base_name_var = tk.StringVar(converter_frame, value=base_names[0])
        output_menu = tk.OptionMenu(converter_frame, self.output_base_name_var, *base_names)
        output_menu.config(font=self.font_normal, bg="#E0E0E0", activebackground="#D0D0D0", relief=tk.FLAT)
        output_menu["menu"].config(font=self.font_normal)
        output_menu.grid(row=1, column=2, sticky="ew", padx=5)

        # Conversion Button
        tk.Button(converter_frame, text="Convert", command=self.convert_number,
                  font=self.font_normal, bg=PRIMARY_COLOR, fg="white", bd=0, padx=10, pady=5,
                  relief=tk.GROOVE, activebackground="#0056b3", activeforeground="white").grid(row=1, column=3, sticky="e", padx=5)

        # Row 2 & 3: Result and Copy Button
        tk.Label(converter_frame, text="Output Value:", font=self.font_normal, 
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, sticky="w", padx=5, pady=5) # Label updated
                 
        self.result_value_var = tk.StringVar(value="Result will appear here.")
        # Span the result label across three columns to make room for the copy button
        self.result_label = tk.Label(converter_frame, textvariable=self.result_value_var, font=('Consolas', 10, 'bold'), 
                 bg="#DEDEDE", fg="#000000", anchor="w", padx=5, pady=5, relief=tk.SUNKEN)
        self.result_label.grid(row=3, column=0, sticky="ew", padx=5, columnspan=3) 

        # Copy Button for Converter Output
        tk.Button(converter_frame, text="Copy", command=self.copy_converted_value,
                  font=self.font_normal_small, bg=SECONDARY_COLOR, fg="white", bd=0, 
                  padx=5, pady=1, relief=tk.GROOVE, 
                  activebackground="#4db850", activeforeground="white").grid(row=3, column=3, sticky="w", padx=5)

        converter_frame.grid_columnconfigure(0, weight=1)
        converter_frame.grid_columnconfigure(1, weight=1)
        converter_frame.grid_columnconfigure(2, weight=1)
        converter_frame.grid_columnconfigure(3, weight=0) # Button column

    def convert_number(self):
        """Converts the input number from the selected input base to the selected output base."""
        # Convert input to uppercase to handle hexadecimal letters (A-F)
        input_str = self.input_value_var.get().strip().upper() 
        
        self.result_label.config(relief=tk.SUNKEN, bg="#DEDEDE")
        
        if not input_str:
            self.result_value_var.set("Error: Please enter a value to convert.")
            self.result_label.config(bg="#FFCCCC") # Light red error background
            self.status_var.set("Conversion failed: Empty input.")
            return

        try:
            input_base_name = self.input_base_name_var.get()
            output_base_name = self.output_base_name_var.get()
            
            input_base = self.base_map[input_base_name]
            output_base = self.base_map[output_base_name]
            
            # Step 1: Convert Input (Base X) to Decimal (Base 10)
            decimal_val = int(input_str, input_base)
            
            # Step 2: Convert Decimal Value to Target Base (using built-in functions)
            converted_val = ""
            
            if output_base == 10:
                converted_val = str(decimal_val)
            elif output_base == 2:
                converted_val = bin(decimal_val)[2:]
            elif output_base == 8:
                converted_val = oct(decimal_val)[2:]
            elif output_base == 16:
                converted_val = hex(decimal_val)[2:].upper()
            else:
                converted_val = "CONVERSION LOGIC ERROR"

            # Step 3: Display ONLY the output value
            self.result_value_var.set(converted_val)
            self.status_var.set(f"Conversion successful: {input_base_name} to {output_base_name}.")

        except ValueError:
            error_msg = f"Error: Input '{input_str}' is invalid for {input_base_name}."
            self.result_value_var.set(error_msg)
            self.result_label.config(bg="#FFCCCC")
            self.status_var.set("Conversion failed: Invalid number format.")
        except Exception as e:
            self.result_value_var.set(f"An unexpected error occurred: {e}")
            self.result_label.config(bg="#FFCCCC")
            self.status_var.set("Conversion failed: Unexpected error.")
            
    def copy_converted_value(self):
        """Copies the currently displayed converted value to the system clipboard."""
        output = self.result_value_var.get()
        
        if "Error" in output or output == "Result will appear here.":
            self.status_var.set("Copy failed: No valid output to copy.")
            return
            
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(output)
            self.master.update() 
            self.status_var.set(f"Copied output: {output} to clipboard.")
            messagebox.showinfo("Copied", f"Converted value copied to clipboard:\n{output}")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy output: {e}")

    # --- COLOR PICKER METHODS (Unchanged) ---

    def setup_color_picker_section(self, parent_frame):
        """Builds the GUI elements for the RGB to HEX color picker."""
        color_frame = tk.LabelFrame(parent_frame, text="Color Converter (RGB <-> HEX)",
                                  font=self.font_large, bg=CARD_COLOR, fg=TEXT_COLOR,
                                  padx=15, pady=15, bd=1, relief=tk.RIDGE)
        color_frame.pack(pady=15, fill="x", padx=10)

        # Variables for R, G, B inputs and HEX output/input
        self.r_var = tk.StringVar(value="0")
        self.g_var = tk.StringVar(value="0")
        self.b_var = tk.StringVar(value="0")
        # This variable is now used for BOTH HEX input and HEX output display
        self.hex_var = tk.StringVar(value="#000000") 

        # --- RGB Input Section ---
        rgb_input_frame = tk.Frame(color_frame, bg=CARD_COLOR)
        rgb_input_frame.pack(fill='x', pady=10)

        # Validation command for live RGB input checking
        validate_rgb_cmd = rgb_input_frame.register(self.validate_rgb_input)

        def create_color_input(parent, label_text, var, column):
            """Helper to create R/G/B label and constrained entry field."""
            tk.Label(parent, text=label_text, font=('Segoe UI', 10, 'bold'),
                     bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=column * 2, sticky="w", padx=5)
            
            entry = tk.Entry(parent, textvariable=var, font=self.font_normal,
                             bg="#EFEFEF", fg="#000000", bd=1, relief=tk.FLAT, width=5,
                             validate='key', 
                             # When R/G/B changes, call update_rgb_to_hex
                             validatecommand=(validate_rgb_cmd, '%P')) 
            entry.grid(row=0, column=column * 2 + 1, sticky="ew", padx=(0, 15))
            
            # Use trace to automatically call update_rgb_to_hex whenever the variable changes
            var.trace_add("write", lambda *args: self.update_rgb_to_hex())
            
            return entry

        # R, G, B fields
        self.r_entry = create_color_input(rgb_input_frame, "R (0-255):", self.r_var, 0)
        self.g_entry = create_color_input(rgb_input_frame, "G (0-255):", self.g_var, 1)
        self.b_entry = create_color_input(rgb_input_frame, "B (0-255):", self.b_var, 2)

        # Configure input_frame weights for spacing
        rgb_input_frame.grid_columnconfigure(1, weight=1)
        rgb_input_frame.grid_columnconfigure(3, weight=1)
        rgb_input_frame.grid_columnconfigure(5, weight=1)
        
        # --- HEX Input Section ---
        hex_input_frame = tk.Frame(color_frame, bg=CARD_COLOR)
        hex_input_frame.pack(fill='x', pady=10)

        tk.Label(hex_input_frame, text="HEX Input Value:", font=('Segoe UI', 10, 'bold'),
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=5)

        # Validation command for HEX input
        validate_hex_cmd = hex_input_frame.register(self.validate_hex_input)
        
        # Hex Input Field (uses the same self.hex_var as output)
        self.hex_input_entry = tk.Entry(hex_input_frame, textvariable=self.hex_var, 
                                        font=self.font_normal, 
                                        bg="#EFEFEF", fg="#000000", bd=1, relief=tk.FLAT, width=8,
                                        validate='key', validatecommand=(validate_hex_cmd, '%P'))
        self.hex_input_entry.grid(row=0, column=1, sticky="w", padx=5)
        
        # Link HEX input var to its update function
        self.hex_var.trace_add("write", lambda *args: self.update_hex_to_rgb())


        # --- Output Section (Color Box and RGB Output Value) ---
        output_frame = tk.Frame(color_frame, bg=CARD_COLOR)
        output_frame.pack(fill='x', pady=10)

        # 1. Color Display Box
        tk.Label(output_frame, text="Current Color Preview:", font=('Segoe UI', 10, 'bold'),
                 bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.color_box = tk.Label(output_frame, bg="#000000", width=8, height=3, relief=tk.SUNKEN)
        self.color_box.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        # 2. Copy Button
        tk.Button(output_frame, text="Copy HEX", command=self.copy_hex_value,
                  font=self.font_normal_small, bg=SECONDARY_COLOR, fg="white", bd=0,
                  padx=5, pady=1, relief=tk.GROOVE,
                  activebackground="#4db850", activeforeground="white").grid(row=0, column=2, sticky="w", padx=5)

        output_frame.grid_columnconfigure(1, weight=1)

        # Initial update (calls the function that is linked to RGB changes)
        self.update_rgb_to_hex()

    def validate_rgb_input(self, new_value):
        """Validation command to ensure input is a number between 0 and 255."""
        if new_value == "":
            return True # Allow empty string momentarily (e.g., during deletion)
        try:
            val = int(new_value)
            # Only allow typing if the value is 0-255 and not longer than 3 digits
            return 0 <= val <= 255 and len(new_value) <= 3
        except ValueError:
            return False # Reject non-numeric input

    def validate_hex_input(self, new_value):
        """Validation command to ensure input is a valid HEX string (0-6 characters, a-f, 0-9, optional #)."""
        value = new_value.strip().upper()
        
        # Allow empty or just a '#'
        if value == "" or value == "#":
            return True
            
        # Check for optional leading '#'
        if value.startswith('#'):
            value = value[1:]
        
        # Check length (max 6 characters after removing #)
        if len(value) > 6:
            return False
            
        # Check if all characters are valid hexadecimal digits
        return all(c in '0123456789ABCDEF' for c in value)


    def update_rgb_to_hex(self):
        """Reads R, G, B inputs, converts to HEX, updates the box color and HEX label."""
        if self.is_updating:
            return # Prevent loop

        try:
            self.is_updating = True # Lock to prevent triggering HEX update
            
            # Get values, handling temporary empty states by defaulting to 0
            r_val = int(self.r_var.get() or "0")
            g_val = int(self.g_var.get() or "0")
            b_val = int(self.b_var.get() or "0")

            # Clamp values to the 0-255 range
            r = max(0, min(255, r_val))
            g = max(0, min(255, g_val))
            b = max(0, min(255, b_val))
            
            # Convert to HEX format: "#RRGGBB". :02X ensures two hex digits, padding with 0 if necessary.
            hex_color = f"#{r:02X}{g:02X}{b:02X}"

            # Update UI elements
            self.hex_var.set(hex_color) # This triggers update_hex_to_rgb, but it's locked out by the flag
            self.color_box.config(bg=hex_color)
            self.status_var.set(f"RGB converted: ({r},{g},{b}) -> {hex_color}")

        except Exception as e:
            # Set error state visually
            self.status_var.set(f"RGB update error: {e}")
            self.color_box.config(bg="#FFCCCC")
            self.hex_var.set("Error")
        finally:
            self.is_updating = False # Unlock


    def update_hex_to_rgb(self):
        """Reads HEX input, converts to RGB, and updates R, G, B variables."""
        if self.is_updating:
            return # Prevent loop

        hex_code = self.hex_var.get().strip().upper()

        # Sanitize hex_code: ensure it's a 6-digit hex string
        if hex_code.startswith('#'):
            hex_code = hex_code[1:]

        # We only process a full 6-character input to update RGB fields
        if len(hex_code) != 6:
            # Only update the color preview if the partial hex is valid
            if len(hex_code) > 0 and self.validate_hex_input("#"+hex_code):
                 # Try to display partial valid color (e.g. #FF)
                 try:
                     padding = '0' * (6 - len(hex_code))
                     partial_hex = hex_code + padding
                     self.color_box.config(bg=f"#{partial_hex}")
                 except Exception:
                     pass
                     
            self.status_var.set("HEX input is incomplete. (Need 6 digits)")
            return

        try:
            r_hex = hex_code[0:2]
            g_hex = hex_code[2:4]
            b_hex = hex_code[4:6]

            r = int(r_hex, 16)
            g = int(g_hex, 16)
            b = int(b_hex, 16)

            self.is_updating = True # Lock to prevent triggering RGB update
            
            # Update R, G, B variables. This would normally trigger update_rgb_to_hex, but is blocked by the flag.
            self.r_var.set(str(r))
            self.g_var.set(str(g))
            self.b_var.set(str(b))
            
            # Since update_rgb_to_hex is blocked, we must update the color box here.
            final_hex = f"#{hex_code}"
            self.color_box.config(bg=final_hex)
            
            self.status_var.set(f"HEX converted: {final_hex} -> RGB({r},{g},{b})")

        except ValueError:
            self.status_var.set(f"Error: Invalid full HEX value: #{hex_code}")
            self.color_box.config(bg="#FFCCCC")
        finally:
            self.is_updating = False # Unlock


    def copy_hex_value(self):
        """Copies the currently displayed HEX value to the system clipboard."""
        hex_output = self.hex_var.get()

        if hex_output in ("#000000", "Error") or len(hex_output) != 7:
            self.status_var.set("Copy failed: No valid HEX value available.")
            return

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(hex_output)
            self.master.update()
            self.status_var.set(f"Copied HEX: {hex_output} to clipboard.")
            messagebox.showinfo("Copied", f"HEX Color copied to clipboard:\n{hex_output}")
        except Exception as e:
            self.status_var.set(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy address: {e}")

# --- OS Specific Functions (Unchanged) ---
def minimize_console_window():
    """Minimizes the command prompt/terminal window used to launch the script."""
    if platform.system() == "Windows":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                # SW_MINIMIZE (6) minimizes the window
                ctypes.windll.user32.ShowWindow(hwnd, 6)
        except Exception:
            pass

if __name__ == "__main__":
    minimize_console_window()
    
    # Check for general OS compatibility warning on start
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        messagebox.showwarning("OS Warning", "This application relies on OS-specific commands (for network and launcher) and may not function fully on this operating system.")
        
    root = tk.Tk()
    app = SystemUtilityApp(root)
    root.mainloop()
