"""
GUI main interface
Provides graphical interface for NWN tools
"""

import sys
import logging
from pathlib import Path
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    print("GUI requires tkinter, which is not available")
    sys.exit(1)

from .widgets import ToolSelector, ConfigPanel, OutputPanel
from core import __version__

logger = logging.getLogger(__name__)


class MainWindow:
    """Main GUI window"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"NeverWinter Python Tools v{__version__}")
        self.root.geometry("1000x700")
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.setup_ui()
        self.setup_logging()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for tool selection and configuration
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Tool selector
        self.tool_selector = ToolSelector(left_frame)
        self.tool_selector.pack(fill=tk.X, padx=5, pady=5)
        
        # Configuration panel
        self.config_panel = ConfigPanel(left_frame)
        self.config_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel for output
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Output panel
        self.output_panel = OutputPanel(right_frame)
        self.output_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setup callbacks
        self.tool_selector.on_tool_changed = self.on_tool_changed
        self.config_panel.on_run_command = self.on_run_command
        
    def setup_logging(self):
        """Setup logging to GUI"""
        # Create a custom handler that writes to the output panel
        class GUILogHandler(logging.Handler):
            def __init__(self, output_panel):
                super().__init__()
                self.output_panel = output_panel
                
            def emit(self, record):
                msg = self.format(record)
                self.output_panel.append_text(msg + '\n')
        
        # Add GUI handler
        gui_handler = GUILogHandler(self.output_panel)
        gui_handler.setFormatter(logging.Formatter(
            '%(levelname)s [%(asctime)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(gui_handler)
        root_logger.setLevel(logging.INFO)
        
    def on_tool_changed(self, tool_name):
        """Handle tool selection change"""
        self.config_panel.set_tool(tool_name)
        
    def on_run_command(self, command_args):
        """Handle command execution"""
        try:
            self.output_panel.clear()
            logger.info(f"Executing: {' '.join(command_args)}")
            
            # Import and run the appropriate CLI command
            from cli.main import main as cli_main
            
            # Save original sys.argv
            original_argv = sys.argv[:]
            
            try:
                # Set argv for the CLI command
                sys.argv = ['nwpy'] + command_args
                
                # Run command
                result = cli_main()
                
                if result == 0:
                    logger.info("Command completed successfully")
                else:
                    logger.error(f"Command failed with exit code {result}")
                    
            finally:
                # Restore original argv
                sys.argv = original_argv
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            import traceback
            self.output_panel.append_text(traceback.format_exc())
        
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def main():
    """Main GUI entry point"""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
