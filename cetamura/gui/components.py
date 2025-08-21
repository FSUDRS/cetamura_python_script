"""
GUI components for Cetamura Batch Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel, Text, Scrollbar, Button, BooleanVar, Frame, Label
from pathlib import Path
import logging
import threading
import os
import platform
import subprocess

from ..core import find_photo_sets, batch_process_with_safety_nets
from ..utils import configure_logging_level, log_user_friendly, open_file_with_system_app


class ProcessingOptionsDialog:
    """Dialog for selecting processing options with mode conflict detection"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = {'cancelled': True}
        self.dialog = None
        
    def show(self):
        """Show the processing options dialog and return user selection"""
        self.dialog = Toplevel(self.parent)
        self.dialog.title("Processing Options")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Variables
        self.dry_run_var = BooleanVar()
        self.staging_var = BooleanVar()
        self.advanced_logs_var = BooleanVar()
        
        self._create_widgets()
        self._setup_event_handlers()
        
        # Wait for dialog to close
        self.dialog.wait_window()
        return self.result
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = Frame(self.dialog)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Title
        title_label = Label(main_frame, text="Select Processing Mode", 
                           font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Mode selection frame
        mode_frame = Frame(main_frame)
        mode_frame.pack(fill='x', pady=(0, 20))
        
        # Dry run option
        self.dry_run_cb = tk.Checkbutton(
            mode_frame, 
            text="🔍 Dry Run Mode", 
            variable=self.dry_run_var,
            font=('Helvetica', 12),
            command=self._check_mode_conflict
        )
        self.dry_run_cb.pack(anchor='w', pady=5)
        
        dry_run_desc = Label(mode_frame, 
                           text="Preview processing without making changes", 
                           font=('Helvetica', 9), fg='gray')
        dry_run_desc.pack(anchor='w', padx=20)
        
        # Staging option
        self.staging_cb = tk.Checkbutton(
            mode_frame, 
            text="📋 Staging Mode", 
            variable=self.staging_var,
            font=('Helvetica', 12),
            command=self._check_mode_conflict
        )
        self.staging_cb.pack(anchor='w', pady=(15, 5))
        
        staging_desc = Label(mode_frame, 
                           text="Process to staging directory for review", 
                           font=('Helvetica', 9), fg='gray')
        staging_desc.pack(anchor='w', padx=20)
        
        # Production note
        prod_label = Label(mode_frame, 
                          text="⚡ Production Mode (default if neither above is selected)", 
                          font=('Helvetica', 10), fg='#2E5C8B')
        prod_label.pack(anchor='w', pady=(15, 5))
        
        # Conflict warning frame
        self.conflict_frame = Frame(main_frame, bg='#FFEEEE', relief='ridge', bd=2)
        self.conflict_label = Label(self.conflict_frame, 
                                  text="⚠️ Mode Conflict Detected",
                                  font=('Helvetica', 10, 'bold'), 
                                  fg='#B22222', bg='#FFEEEE')
        
        # Advanced options
        advanced_frame = Frame(main_frame)
        advanced_frame.pack(fill='x', pady=(20, 20))
        
        advanced_title = Label(advanced_frame, text="Advanced Options", 
                             font=('Helvetica', 12, 'bold'))
        advanced_title.pack(anchor='w')
        
        self.advanced_logs_cb = tk.Checkbutton(
            advanced_frame, 
            text="Enable detailed technical logging", 
            variable=self.advanced_logs_var,
            font=('Helvetica', 10)
        )
        self.advanced_logs_cb.pack(anchor='w', pady=5)
        
        # Button frame
        button_frame = Frame(main_frame)
        button_frame.pack(side='bottom', fill='x', pady=(20, 0))
        
        self.proceed_btn = Button(button_frame, text="Proceed", 
                                command=self._on_proceed,
                                bg='#8B2E2E', fg='white', 
                                font=('Helvetica', 12))
        self.proceed_btn.pack(side='left', padx=10)
        
        cancel_btn = Button(button_frame, text="Cancel", 
                          command=self._on_cancel,
                          font=('Helvetica', 12))
        cancel_btn.pack(side='left', padx=10)
    
    def _setup_event_handlers(self):
        """Set up event handlers"""
        self._check_mode_conflict()  # Initial check
    
    def _check_mode_conflict(self):
        """Check for mode conflicts and update UI accordingly"""
        dry_run = self.dry_run_var.get()
        staging = self.staging_var.get()
        
        if dry_run and staging:
            # Show conflict warning
            self.conflict_frame.pack(fill='x', pady=(10, 10))
            self.conflict_label.pack(pady=5)
            
            conflict_desc = Label(self.conflict_frame, 
                                text="Both Dry Run and Staging modes are selected.\n"
                                     "Dry Run mode will take precedence.", 
                                font=('Helvetica', 9), fg='#B22222', bg='#FFEEEE')
            conflict_desc.pack(pady=(0, 5))
        else:
            # Hide conflict warning
            self.conflict_frame.pack_forget()
    
    def _on_proceed(self):
        """Handle proceed button click"""
        dry_run = self.dry_run_var.get()
        staging = self.staging_var.get()
        
        # Handle mode conflicts
        if dry_run and staging:
            response = messagebox.askyesno(
                "Mode Conflict Resolution",
                "Both Dry Run and Staging modes are selected.\n\n"
                "Dry Run Mode will take precedence:\n"
                "• No files will be modified\n"
                "• Only CSV report will be generated\n"
                "• Staging mode will be ignored\n\n"
                "Continue with Dry Run Mode?",
                parent=self.dialog
            )
            if not response:
                return
        
        self.result = {
            'cancelled': False,
            'dry_run': dry_run,
            'staging': staging if not dry_run else False,  # Staging disabled if dry_run
            'advanced_logs': self.advanced_logs_var.get()
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.dialog.destroy()


class InstructionsWindow:
    """Window for displaying usage instructions"""
    
    @staticmethod
    def show(parent):
        """Show the instructions window"""
        try:
            instruction_text = """CETAMURA BATCH INGEST TOOL
==========================

This tool automates the process for creating ingest files for the Cetamura Digital Collections.

REQUIREMENTS
-----------
- TIFF image files
- Corresponding XML metadata files
- MANIFEST.ini file in each folder
- Files must be organized in year/trench structure

USAGE INSTRUCTIONS
----------------
1. Click "Select Folder" to choose the parent directory containing your year folders
   Example structure:
   Parent_Folder/
   ├── 2006/
   │   ├── 46N-3W/
   │   │   ├── image.tiff
   │   │   ├── metadata.xml
   │   │   └── MANIFEST.ini
   │   └── ...
   └── ...

2. The tool will:
   - Extract IID from XML files.
   - Rename image and XML files to match the IID.
   - Copy the MANIFEST.ini file as-is.
   - Package the files into a ZIP archive.
"""

            # Create a new top-level window
            instructions_window = Toplevel(parent)
            instructions_window.title("Instructions")
            instructions_window.geometry("600x500")

            # Add a scrollbar
            scrollbar = Scrollbar(instructions_window)
            scrollbar.pack(side='right', fill='y')

            # Create a Text widget
            text_area = Text(instructions_window, wrap='word', yscrollcommand=scrollbar.set)
            text_area.pack(expand=True, fill='both')
            text_area.insert('1.0', instruction_text)
            text_area.config(state='disabled')  # Make the text read-only

            # Configure scrollbar
            scrollbar.config(command=text_area.yview)

        except Exception as e:
            logging.error(f"Error displaying instructions: {e}")


class LogViewers:
    """Utilities for viewing log files"""
    
    @staticmethod
    def view_technical_log():
        """Open the technical log file"""
        log_file = Path("batch_tool.log")
        try:
            if log_file.exists():
                open_file_with_system_app(log_file)
                logging.info(f"Opened technical log file: {log_file}")
            else:
                messagebox.showwarning("Log File Not Found", 
                                     f"Technical log file does not exist: {log_file}")
                logging.warning("Attempted to open non-existent technical log file")
        except Exception as e:
            messagebox.showerror("Error Opening Log", f"Could not open technical log file: {e}")
            logging.error(f"Error opening technical log file: {e}")
    
    @staticmethod
    def view_summary_log():
        """Open the user-friendly summary log file"""
        summary_log_file = Path("batch_process_summary.log")
        try:
            if summary_log_file.exists():
                open_file_with_system_app(summary_log_file)
                logging.info("User opened user-friendly summary log file")
            else:
                messagebox.showwarning("Summary Log Not Found", 
                                     f"Summary log file does not exist: {summary_log_file}")
                logging.warning("Attempted to open non-existent summary log file")
        except Exception as e:
            messagebox.showerror("Error Opening Summary Log", 
                                f"Could not open summary log file: {e}")
            logging.error(f"Error opening summary log file: {e}")
