"""
GUI main interface
Provides graphical interface for NWN tools
"""

import sys
import logging
from pathlib import Path
import os

# Ensure package-relative imports work reliably when run as module
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    print("GUI requires tkinter, which is not available")
    sys.exit(1)

# Robust relative imports
from .widgets import ToolSelector, ConfigPanel, OutputPanel
try:
    from core import __version__
except Exception:
    __version__ = "1.0.0"

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

        # Install global Tk error handler so UI never closes on exceptions
        def _report_callback_exception(exc, val, tb):
            import traceback
            msg = "".join(traceback.format_exception(exc, val, tb))
            logger.error("Tk callback exception:\n" + msg)
            try:
                messagebox.showerror("Unhandled error", msg)
                self.output_panel.append_text(msg + "\n")
            except Exception:
                pass
        self.root.report_callback_exception = _report_callback_exception
        
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

            # Basic guard: if no args, inform user instead of crashing
            if not command_args or len(command_args) == 0:
                logger.error("No command arguments provided.")
                messagebox.showwarning("Missing arguments", "Please configure the tool before running.")
                return

            # Auto-insert default subcommands where applicable to avoid CLI errors
            if command_args[0] == "tlk" and (len(command_args) == 1 or command_args[1] not in ("convert", "info")):
                command_args = ["tlk", "convert"] + command_args[1:]
            if command_args[0] == "gff" and (len(command_args) == 1 or command_args[1] not in ("convert", "info")):
                command_args = ["gff", "convert"] + command_args[1:]
            if command_args[0] == "twoda" and (len(command_args) == 1 or command_args[1] not in ("convert", "info")):
                command_args = ["twoda", "convert"] + command_args[1:]

            # Debug: Show the exact command being run
            debug_msg = f"Debug: Command args = {command_args}"
            logger.info(debug_msg)
            print(debug_msg)  # Also print to console

            # Import and run the appropriate CLI command
            from cli.main import main as cli_main

            # Save original sys.argv
            original_argv = sys.argv[:]

            try:
                # Set argv for the CLI command
                sys.argv = ['nwpy'] + command_args
                logger.info(f"Debug: sys.argv = {sys.argv}")

                # Run command
                result = cli_main()

                if result == 0:
                    logger.info("Command completed successfully")
                else:
                    # result may be None if the command raised and was caught inside CLI
                    logger.error(f"Command failed with exit code {result if result is not None else 'unknown'}")

            finally:
                # Restore original argv
                sys.argv = original_argv

        except Exception as e:
            # Do not crash the GUI; surface the error
            import traceback
            error_msg = f"{e}\n" + traceback.format_exc()
            logger.error(f"Error executing command: {e}")
            self.output_panel.append_text(error_msg)
            messagebox.showerror("Execution error", str(e))
        
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
