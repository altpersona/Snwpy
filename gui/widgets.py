"""
GUI widgets for the NWN tools interface
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class ToolSelector(ttk.LabelFrame):
    """Widget for selecting which NWN tool to use"""
    
    def __init__(self, parent):
        super().__init__(parent, text="Tool Selection", padding=10)
        
        self.on_tool_changed = None
        
        # Available tools
        self.tools = {
            "NWSync Tools": [
                ("nwsync write", "Create NWSync manifests - ✅ Implemented"),
                ("nwsync print", "Print manifest contents - ✅ Implemented"),
                ("nwsync fetch", "Fetch NWSync data - ⚠️ Placeholder"),
                ("nwsync prune", "Prune NWSync repository - ⚠️ Placeholder"),
            ],
            "Archive Tools": [
                ("erf pack", "Pack ERF archives - ✅ Implemented"),
                ("erf unpack", "Unpack ERF archives - ✅ Implemented"),
                ("key pack", "Pack KEY files - ✅ Framework ready"),
                ("key unpack", "Unpack KEY files - ✅ Framework ready"),
                ("key list", "List KEY contents - ✅ Framework ready"),
                ("key shadows", "Show KEY shadows - ✅ Framework ready"),
            ],
            "Format Tools": [
                ("gff convert", "Convert GFF files - ✅ Framework ready"),
                ("gff info", "Display GFF information - ✅ Framework ready"),
                ("tlk convert", "Convert TLK files - ✅ Framework ready"),
                ("tlk info", "Display TLK information - ✅ Framework ready"),
                ("twoda convert", "Convert 2DA files - ✅ Framework ready (with --minify)"),
                ("twoda info", "Display 2DA information - ✅ Framework ready"),
            ],
            "Resource Manager": [
                ("resman extract", "Extract resources - ✅ Framework ready"),
                ("resman stats", "Show resource statistics - ✅ Framework ready"),
                ("resman grep", "Search resources - ✅ Framework ready"),
                ("resman cat", "Print resource contents - ✅ Framework ready"),
                ("resman diff", "Compare resource containers - ✅ Framework ready"),
            ],
            "Development": [
                ("script compile", "Compile NWScript - ✅ Framework ready"),
                ("script decompile", "Decompile NWScript - ✅ Framework ready"),
                ("script disasm", "Disassemble NWScript - ✅ Framework ready"),
            ]
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the tool selector UI"""
        # Tool category dropdown
        ttk.Label(self, text="Category:").pack(anchor=tk.W)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            self, 
            textvariable=self.category_var,
            values=list(self.tools.keys()),
            state="readonly"
        )
        self.category_combo.pack(fill=tk.X, pady=(0, 10))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_changed)
        
        # Tool dropdown
        ttk.Label(self, text="Tool:").pack(anchor=tk.W)
        
        self.tool_var = tk.StringVar()
        self.tool_combo = ttk.Combobox(
            self,
            textvariable=self.tool_var,
            state="readonly"
        )
        self.tool_combo.pack(fill=tk.X, pady=(0, 10))
        self.tool_combo.bind('<<ComboboxSelected>>', self.on_tool_selected)
        
        # Tool description
        self.description_var = tk.StringVar()
        self.description_label = ttk.Label(
            self,
            textvariable=self.description_var,
            wraplength=300,
            foreground="gray"
        )
        self.description_label.pack(anchor=tk.W)
        
        # Set default selection
        if self.tools:
            first_category = list(self.tools.keys())[0]
            self.category_var.set(first_category)
            self.on_category_changed(None)
            
    def on_category_changed(self, event):
        """Handle category selection change"""
        category = self.category_var.get()
        if category in self.tools:
            tools = self.tools[category]
            tool_names = [f"{tool[0]} - {tool[1]}" for tool in tools]
            self.tool_combo['values'] = tool_names
            
            if tools:
                self.tool_combo.current(0)
                self.on_tool_selected(None)
                
    def on_tool_selected(self, event):
        """Handle tool selection change"""
        selection = self.tool_var.get()
        if selection:
            # Extract tool name (before the ' - ')
            tool_name = selection.split(' - ')[0]
            
            # Find description
            category = self.category_var.get()
            if category in self.tools:
                for tool, desc in self.tools[category]:
                    if tool == tool_name:
                        self.description_var.set(desc)
                        break
            
            # Notify callback
            if self.on_tool_changed:
                self.on_tool_changed(tool_name)
                
    def get_selected_tool(self):
        """Get the currently selected tool name"""
        selection = self.tool_var.get()
        if selection:
            return selection.split(' - ')[0]
        return None


class ConfigPanel(ttk.LabelFrame):
    """Widget for configuring tool options"""
    
    def __init__(self, parent):
        super().__init__(parent, text="Configuration", padding=10)
        
        self.on_run_command = None
        self.current_tool = None
        self.config_widgets = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the configuration UI"""
        # Scrollable frame for config options
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Button frame at bottom
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Run button
        self.run_button = ttk.Button(
            button_frame,
            text="Run Command",
            command=self.run_command
        )
        self.run_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Help button
        self.help_button = ttk.Button(
            button_frame,
            text="Show Help",
            command=self.show_help
        )
        self.help_button.pack(side=tk.LEFT)
        
    def set_tool(self, tool_name):
        """Set the current tool and update configuration options"""
        self.current_tool = tool_name
        self.clear_config()
        
        if tool_name:
            self.create_config_for_tool(tool_name)
            
    def clear_config(self):
        """Clear all configuration widgets"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.config_widgets.clear()
        
    def create_config_for_tool(self, tool_name):
        """Create configuration widgets for a specific tool"""
        row = 0
        
        if tool_name == 'nwsync write':
            self.add_file_input("Storage Directory", "root", row, is_directory=True)
            row += 1
            self.add_file_input("Module/ERF Files", "specs", row, multiple=True)
            row += 1
            self.add_text_input("Name", "name", row)
            row += 1
            self.add_text_input("Description", "description", row)
            row += 1
            self.add_checkbox("Include Module Contents", "with_module", row)
            row += 1
            self.add_number_input("Group ID", "group_id", row, default=0)
            
        elif tool_name == 'nwsync print':
            self.add_file_input("Manifest File", "manifest", row)
            row += 1
            self.add_checkbox("Verify Files", "verify", row)
            
        elif tool_name == 'erf pack':
            self.add_file_input("Input Directory", "input_dir", row, is_directory=True)
            row += 1
            self.add_file_input("Output ERF", "output_erf", row, save=True)
            
        elif tool_name == 'erf unpack':
            self.add_file_input("Input ERF", "input_erf", row)
            row += 1
            self.add_file_input("Output Directory", "output_dir", row, is_directory=True)
            
        elif tool_name == 'gff convert':
            self.add_file_input("Input GFF File", "input", row)
            row += 1
            self.add_file_input("Output File", "output", row, save=True)
            row += 1
            self.add_checkbox("Convert to JSON", "to_json", row, default=True)
            
        elif tool_name == 'gff info':
            self.add_file_input("Input GFF File", "input", row)
            row += 1
            self.add_checkbox("Verbose Output", "verbose", row)
            
        elif tool_name == 'tlk convert':
            self.add_file_input("Input TLK File", "input", row)
            row += 1
            self.add_file_input("Output File", "output", row, save=True)
            row += 1
            self.add_checkbox("Convert to JSON", "to_json", row, default=True)
            
        elif tool_name == 'tlk info':
            self.add_file_input("Input TLK File", "input", row)
            row += 1
            self.add_checkbox("Verbose Output", "verbose", row)
            
        elif tool_name == 'twoda convert':
            self.add_file_input("Input 2DA File", "input", row)
            row += 1
            self.add_file_input("Output File", "output", row, save=True)
            row += 1
            self.add_checkbox("Convert to CSV", "to_csv", row)
            row += 1
            self.add_checkbox("Convert to JSON", "to_json", row)
            row += 1
            self.add_checkbox("Minify Output", "minify", row)
            
        elif tool_name == 'twoda info':
            self.add_file_input("Input 2DA File", "input", row)
            row += 1
            self.add_checkbox("Verbose Output", "verbose", row)
            
        elif tool_name == 'key pack':
            self.add_file_input("Input Directory", "input", row, is_directory=True)
            row += 1
            self.add_file_input("Output KEY File", "output", row, save=True)
            
        elif tool_name == 'key unpack':
            self.add_file_input("Input KEY File", "input", row)
            row += 1
            self.add_file_input("Output Directory", "output", row, is_directory=True)
            
        elif tool_name == 'key list':
            self.add_file_input("Input KEY File", "input", row)
            
        elif tool_name == 'key shadows':
            self.add_file_input("Input KEY File", "input", row)
            
        elif tool_name == 'resman extract':
            self.add_file_input("Output Directory", "output", row, is_directory=True)
            row += 1
            self.add_text_input("Pattern Filter", "pattern", row)
            row += 1
            self.add_text_input("Resource Type", "type", row)
            
        elif tool_name == 'resman cat':
            self.add_text_input("Resource Name", "resource", row)
            
        elif tool_name == 'resman grep':
            self.add_text_input("Search Pattern", "pattern", row)
            row += 1
            self.add_text_input("Resource Type", "type", row)
            
        elif tool_name == 'resman diff':
            self.add_file_input("First Container", "first", row)
            row += 1
            self.add_file_input("Second Container", "second", row)
            
        elif tool_name == 'script compile':
            self.add_file_input("Input NSS File", "input", row)
            row += 1
            self.add_file_input("Output NCS File", "output", row, save=True)
            row += 1
            self.add_file_input("Includes Directory", "includes", row, is_directory=True)
            row += 1
            self.add_checkbox("Verbose Output", "verbose", row)
            row += 1
            self.add_checkbox("Create Dummy Output (for testing)", "dummy", row)
            
        elif tool_name == 'script decompile':
            self.add_file_input("Input NCS File", "input", row)
            row += 1
            self.add_file_input("Output NSS File", "output", row, save=True)
            
        elif tool_name == 'script disasm':
            self.add_file_input("Input NCS File", "input", row)
            
        else:
            # Fallback for unknown tools
            ttk.Label(
                self.scrollable_frame,
                text=f"✅ {tool_name} command is available.\nConfiguration panel will be added in future updates."
            ).grid(row=row, column=0, columnspan=3, pady=10)
            
    def add_file_input(self, label, key, row, is_directory=False, save=False, multiple=False):
        """Add a file input widget"""
        ttk.Label(self.scrollable_frame, text=f"{label}:").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2
        )
        
        var = tk.StringVar()
        entry = ttk.Entry(self.scrollable_frame, textvariable=var, width=40)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=2)
        
        def browse():
            if is_directory:
                path = filedialog.askdirectory()
            elif save:
                path = filedialog.asksaveasfilename()
            elif multiple:
                path = filedialog.askopenfilenames()
                if path:
                    path = ';'.join(path)  # Join multiple files
            else:
                path = filedialog.askopenfilename()
            
            if path:
                var.set(path)
                
        browse_btn = ttk.Button(self.scrollable_frame, text="Browse...", command=browse)
        browse_btn.grid(row=row, column=2, padx=(5, 0), pady=2)
        
        self.config_widgets[key] = var
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        
    def add_text_input(self, label, key, row, default=""):
        """Add a text input widget"""
        ttk.Label(self.scrollable_frame, text=f"{label}:").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2
        )
        
        var = tk.StringVar(value=default)
        entry = ttk.Entry(self.scrollable_frame, textvariable=var, width=40)
        entry.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=2)
        
        self.config_widgets[key] = var
        
    def add_number_input(self, label, key, row, default=0):
        """Add a number input widget"""
        ttk.Label(self.scrollable_frame, text=f"{label}:").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2
        )
        
        var = tk.StringVar(value=str(default))
        entry = ttk.Entry(self.scrollable_frame, textvariable=var, width=20)
        entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        
        self.config_widgets[key] = var
        
    def add_checkbox(self, label, key, row, default=False):
        """Add a checkbox widget"""
        var = tk.BooleanVar(value=default)
        checkbox = ttk.Checkbutton(self.scrollable_frame, text=label, variable=var)
        checkbox.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        self.config_widgets[key] = var
        
    def run_command(self):
        """Build and execute the command"""
        if not self.current_tool:
            messagebox.showwarning("No Tool", "Please select a tool first")
            return
            
        # Build command arguments - split tool name into separate arguments
        tool_parts = self.current_tool.split()
        args = tool_parts[:]  # Start with the tool command parts
        
        # Add arguments based on tool and configuration
        for key, var in self.config_widgets.items():
            value = var.get()
            
            if isinstance(var, tk.BooleanVar):
                if value:
                    args.append(f"--{key.replace('_', '-')}")
            elif value:  # Non-empty string/number
                if key in ['root', 'manifest', 'input_dir', 'input_erf', 'output_dir', 'output_erf', 'input', 'output', 'first', 'second', 'resource', 'pattern']:
                    # Positional arguments
                    args.append(value)
                elif key == 'specs':
                    # Multiple files
                    if ';' in value:
                        args.extend(value.split(';'))
                    else:
                        args.append(value)
                else:
                    # Named arguments
                    args.extend([f"--{key.replace('_', '-')}", value])
        
        # Execute command
        if self.on_run_command:
            self.on_run_command(args)
            
    def show_help(self):
        """Show help for the current tool"""
        if not self.current_tool:
            messagebox.showinfo("Help", "Please select a tool first")
            return
            
        # This would show tool-specific help
        messagebox.showinfo("Help", f"Help for {self.current_tool} not yet implemented")


class OutputPanel(ttk.LabelFrame):
    """Widget for displaying command output"""
    
    def __init__(self, parent):
        super().__init__(parent, text="Output", padding=10)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the output UI"""
        # Text widget with scrollbar
        self.text_widget = tk.Text(
            self,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="black",
            fg="white"
        )
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Clear button
        clear_btn = ttk.Button(button_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.RIGHT)
        
    def append_text(self, text):
        """Append text to the output"""
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)  # Scroll to bottom
        
    def clear(self):
        """Clear the output"""
        self.text_widget.delete(1.0, tk.END)
