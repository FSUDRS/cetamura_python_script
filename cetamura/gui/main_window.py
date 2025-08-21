"""
Main application window for Cetamura Batch Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Label, Button
from pathlib import Path
import logging
import threading

from ..core import find_photo_sets, batch_process_with_safety_nets
from ..utils import configure_logging_level, log_user_friendly
from .components import ProcessingOptionsDialog, InstructionsWindow, LogViewers


class MainApplication:
    """Main application window for Cetamura Batch Tool"""
    
    def __init__(self):
        self.root = tk.Tk()
        self._setup_window()
        self._create_widgets()
        
    def _setup_window(self):
        """Setup main window properties"""
        self.root.title("Cetamura Batch Ingest Tool")
        self.root.geometry("600x500")
        
    def _create_widgets(self):
        """Create main window widgets"""
        # Title
        title_label = Label(self.root, 
                           text="Cetamura Batch Ingest Tool", 
                           font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=20)
        
        # Folder selection
        self.folder_label = Label(self.root, 
                                text="No folder selected!", 
                                font=('Helvetica', 12))
        self.folder_label.pack(pady=10)
        
        # Select folder button
        self.select_btn = Button(self.root, 
                               text="Select Folder", 
                               command=self._select_folder,
                               font=('Helvetica', 12))
        self.select_btn.pack(pady=10)
        
        # Process button
        self.process_btn = Button(self.root, 
                                text="Start Processing", 
                                command=self._start_batch_process,
                                state="disabled",
                                bg='#8B2E2E', fg='white',
                                font=('Helvetica', 12))
        self.process_btn.pack(pady=20)
        
        # Status label
        self.status_label = Label(self.root, 
                                text="Status: Ready", 
                                font=('Helvetica', 10))
        self.status_label.pack(pady=10)
        
        # Menu bar
        self._create_menu()
        
    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Instructions", command=self._show_instructions)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Technical Log", command=LogViewers.view_technical_log)
        view_menu.add_command(label="Summary Log", command=LogViewers.view_summary_log)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Instructions", command=self._show_instructions)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _select_folder(self):
        """Handle folder selection"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            if not Path(folder_selected).exists():
                messagebox.showerror("Error", "Selected folder does not exist.")
                return
            
            # Check for photo sets and update UI accordingly
            try:
                photo_sets = find_photo_sets(folder_selected)
                if not photo_sets:
                    self.folder_label.config(text=f"Selected: {folder_selected} - No photo sets found")
                    self.process_btn.config(state="disabled")
                    self.status_label.config(text="Status: No valid photo sets found in selected folder")
                    logging.warning(f"No photo sets found in selected folder: {folder_selected}")
                else:
                    self.folder_label.config(text=f"Selected: {folder_selected}")
                    self.process_btn.config(state="normal")
                    self.status_label.config(text=f"Status: Ready - Found {len(photo_sets)} photo set(s)")
                    logging.info(f"Found {len(photo_sets)} photo sets in selected folder")
            except Exception as e:
                self.folder_label.config(text=f"Selected: {folder_selected} - Error scanning folder")
                self.process_btn.config(state="disabled")
                self.status_label.config(text="Status: Error scanning selected folder")
                logging.error(f"Error scanning folder {folder_selected}: {e}")
        else:
            self.folder_label.config(text="No folder selected!")
            self.process_btn.config(state="disabled")
    
    def _start_batch_process(self):
        """Handle start processing button click"""
        folder_text = self.folder_label.cget("text")
        if not folder_text.startswith("Selected:"):
            messagebox.showerror("Error", "Please select a valid parent folder.")
            return
            
        folder = folder_text.replace("Selected: ", "").split(" - ")[0]  # Extract clean folder path
        if not Path(folder).is_dir():
            messagebox.showerror("Error", "Please select a valid parent folder.")
            return

        # Show processing options dialog
        options_dialog = ProcessingOptionsDialog(self.root)
        options = options_dialog.show()
        
        if options['cancelled']:
            return
            
        dry_run = options.get('dry_run', False)
        staging = options.get('staging', False)
        advanced_logs = options.get('advanced_logs', False)
        
        # Configure logging level based on user preference
        configure_logging_level(advanced_logs)
        
        mode_text = "Dry Run" if dry_run else "Staging" if staging else "Processing"
        self.status_label.config(text=f"{mode_text}...")
        self.select_btn.config(state="disabled")
        self.process_btn.config(state="disabled")
        logging.info(f"Batch processing started for folder: {folder} (dry_run={dry_run}, staging={staging})")

        def run_process():
            try:
                # Determine output directory
                base_folder = Path(folder)
                if staging:
                    output_dir = base_folder.parent / f"staging_output"
                else:
                    output_dir = base_folder.parent / f"output"
                
                # Use the enhanced batch processing function
                success_count, error_count, csv_path = batch_process_with_safety_nets(
                    folder, str(output_dir), dry_run, staging)
                
                # Prepare success message
                mode_desc = "DRY RUN - " if dry_run else "STAGING - " if staging else ""
                
                if dry_run:
                    success_message = f"{mode_desc}Processing simulation completed!\n\n"
                    success_message += f"Would process: {success_count} items\n"
                    success_message += f"Issues found: {error_count} items\n\n"
                    success_message += f"Review the report: {csv_path}\n\n"
                    success_message += "No files were actually modified."
                else:
                    success_message = f"{mode_desc}Processing completed!\n\n"
                    success_message += f"Successfully processed: {success_count} items\n"
                    success_message += f"Errors: {error_count} items\n\n"
                    if staging:
                        success_message += f"Output saved to staging folder\n"
                    success_message += f"Detailed report: {csv_path}"
                
                self.root.after(0, lambda: self.status_label.config(text=f"{mode_desc}Completed successfully!"))
                logging.info(f"Batch processing completed - Success: {success_count}, Errors: {error_count}")
                self.root.after(0, lambda: messagebox.showinfo("Success", success_message))
                
            except Exception as e:
                error_msg = f"An error occurred during processing:\n{str(e)}"
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                self.root.after(0, lambda: self.status_label.config(text="Processing failed."))
                logging.error(f"Error during batch processing: {e}")
            finally:
                self.root.after(0, lambda: self.select_btn.config(state="normal"))
                self.root.after(0, lambda: self.process_btn.config(state="normal"))

        threading.Thread(target=run_process, daemon=True).start()
    
    def _show_instructions(self):
        """Show instructions window"""
        InstructionsWindow.show(self.root)
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
                          "Cetamura Batch Ingest Tool\n"
                          "Version 2024.08.19\n\n"
                          "Enhanced with modular architecture\n"
                          "and comprehensive safety nets.")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
