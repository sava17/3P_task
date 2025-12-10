"""
BR18 Document Automation - Real Prototype GUI

A fully functional prototype interface for the BR18 automation system.
Users can select files, enter project data, view documents, provide feedback, and browse the knowledge base.
"""

import customtkinter as ctk
import os
import sys
import threading
from tkinter import filedialog, messagebox
import json
from pathlib import Path
from typing import List, Dict, Any
import queue

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from demo import BR18DemoSystem
from src.models import (
    BuildingProject,
    FireClassification,
    MunicipalityFeedback,
    DocumentType,
    GeneratedDocument,
    ApplicationCategory,
    RiskClass
)
from src.project_parser import ProjectInputParser
from src.municipal_response_parser import MunicipalResponseParser

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TextRedirector:
    """Redirect stdout to a text widget"""
    def __init__(self, queue):
        self.queue = queue

    def write(self, string):
        self.queue.put(string)

    def flush(self):
        pass


class BR18PrototypeGUI(ctk.CTk):
    """Real prototype GUI for BR18 Document Automation"""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("BR18 Document Automation - Prototype")
        self.geometry("1800x1000")

        # Make window resizable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Queue for thread-safe text output
        self.output_queue = queue.Queue()

        # Backend system
        self.demo_system = BR18DemoSystem()
        self.project_parser = ProjectInputParser()
        self.municipal_parser = MunicipalResponseParser()
        self.is_processing = False

        # Data storage
        self.selected_pdf_files = []  # For knowledge base PDFs (Del 2)
        self.project_spec_pdf = None  # For project specification PDF (Del 1)
        self.extracted_project_data = None  # Extracted data from project PDF (Del 1)
        self.municipal_response_pdf = None  # For municipal response PDF (Del 2)
        self.current_project = None
        self.generated_documents = []
        self.auto_selected_doc_types = []  # Automatically determined required docs (Del 1)

        # Create tabbed interface
        self.setup_tabbed_interface()

        # Check if BR18 is already loaded
        self.check_br18_status()

        # Start queue checker
        self.check_queue()

    def setup_tabbed_interface(self):
        """Setup main tabbed interface"""
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # Create tab view
        self.tabview = ctk.CTkTabview(main_container, width=1750, height=950)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Add tabs - UPDATED for Del 1 & Del 2 separation
        self.tab_parse = self.tabview.add("1️⃣ Parse Project (Del 1)")
        self.tab_knowledge_setup = self.tabview.add("2️⃣ Knowledge Base (Del 2)")
        self.tab_generate = self.tabview.add("3️⃣ Generate Documents")
        self.tab_knowledge_view = self.tabview.add("4️⃣ View Knowledge")

        # Setup each tab
        self.setup_tab_parse_project()  # NEW: Del 1 - Parse project input
        self.setup_tab_knowledge_setup()  # MOVED: Del 2 - Build knowledge base
        self.setup_tab_generate()
        self.setup_tab_knowledge_view()

    def setup_tab_parse_project(self):
        """NEW Tab 1: Parse Project Input (Del 1) - Automatic extraction from project specification PDF"""
        tab = self.tab_parse
        tab.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="📄 Del 1: Parse Project Input (Automatic)",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            tab,
            text="Upload project specification PDF → Automatically extract building data → Auto-select required documents",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # File selection section
        file_frame = ctk.CTkFrame(tab)
        file_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_frame,
            text="Project Specification PDF:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # Selected file display
        self.project_pdf_label = ctk.CTkLabel(
            file_frame,
            text="No file selected",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.project_pdf_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))

        # File buttons
        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        ctk.CTkButton(
            btn_frame,
            text="📁 Select Project PDF",
            command=self.select_project_pdf,
            width=180
        ).pack(side="left", padx=5)

        # Parse button
        self.parse_btn = ctk.CTkButton(
            file_frame,
            text="🤖 Parse PDF & Extract Project Data",
            command=self.parse_project_pdf,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.parse_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        # Extracted data display
        ctk.CTkLabel(
            tab,
            text="📊 Extracted Project Data:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(10, 5))

        self.extracted_data_viewer = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
            height=200
        )
        self.extracted_data_viewer.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Auto-selected documents display
        ctk.CTkLabel(
            tab,
            text="📋 Auto-Selected Required Documents:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=5, column=0, sticky="w", padx=20, pady=(10, 5))

        self.auto_docs_viewer = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
            height=150
        )
        self.auto_docs_viewer.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Use extracted project button
        self.use_project_btn = ctk.CTkButton(
            tab,
            text="✅ Use This Project for Document Generation",
            command=self.use_extracted_project,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            fg_color="#16a34a",
            hover_color="#15803d"
        )
        self.use_project_btn.grid(row=7, column=0, sticky="ew", padx=20, pady=(10, 20))

        # Processing log
        ctk.CTkLabel(
            tab,
            text="📋 Processing Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=8, column=0, sticky="w", padx=20, pady=(10, 5))

        self.parse_output = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.parse_output.grid(row=9, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tab.grid_rowconfigure(9, weight=1)

    def setup_tab_knowledge_setup(self):
        """Tab 2: Knowledge Base Setup (Del 2) - Build RAG knowledge base from approved documents"""
        tab = self.tab_knowledge_setup
        tab.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="📚 Del 2: Knowledge Base Setup (RAG)",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            tab,
            text="Upload approved BR18 example documents from past projects → Build RAG knowledge base for document generation",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # File selection section
        file_frame = ctk.CTkFrame(tab)
        file_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_frame,
            text="Example PDF Files:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # File list
        self.file_listbox = ctk.CTkTextbox(file_frame, height=200, state="disabled")
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 10))

        # File buttons
        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        ctk.CTkButton(
            btn_frame,
            text="📁 Add PDF Files",
            command=self.add_pdf_files,
            width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Clear All",
            command=self.clear_pdf_files,
            width=120,
            fg_color="#dc2626",
            hover_color="#b91c1c"
        ).pack(side="left", padx=5)

        # Process button
        self.process_btn = ctk.CTkButton(
            file_frame,
            text="⚙️ Extract & Build Knowledge Base",
            command=self.process_example_documents,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.process_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        # BR18 Regulation Upload Section (NEW)
        br18_frame = ctk.CTkFrame(tab)
        br18_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        br18_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            br18_frame,
            text="📖 BR18 Regulation (Building Regulations 2018):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            br18_frame,
            text="Upload BR18.pdf to enable accurate paragraph citations (§508, etc.) in generated documents",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        # BR18 status
        self.br18_status_label = ctk.CTkLabel(
            br18_frame,
            text="Status: Not uploaded",
            font=ctk.CTkFont(size=12),
            text_color="#dc2626"
        )
        self.br18_status_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))

        # BR18 upload button
        ctk.CTkButton(
            br18_frame,
            text="📤 Upload BR18.pdf",
            command=self.upload_br18_regulation,
            width=200,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=3, column=0, sticky="w", padx=15, pady=(0, 15))

        # Municipal Response Upload Section
        municipal_frame = ctk.CTkFrame(tab)
        municipal_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))
        municipal_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            municipal_frame,
            text="📨 Upload Municipal Response (Afslag/Godkendelse):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            municipal_frame,
            text="Upload rejection (Afslag) or approval (Godkendelse) documents to learn from municipal feedback",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))

        # Selected municipal response file display
        self.municipal_response_label = ctk.CTkLabel(
            municipal_frame,
            text="No file selected",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.municipal_response_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))

        # Municipal response buttons
        municipal_btn_frame = ctk.CTkFrame(municipal_frame, fg_color="transparent")
        municipal_btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 10))

        ctk.CTkButton(
            municipal_btn_frame,
            text="📁 Select Municipal Response",
            command=self.select_municipal_response,
            width=200
        ).pack(side="left", padx=5)

        self.parse_municipal_btn = ctk.CTkButton(
            municipal_btn_frame,
            text="🤖 Parse & Learn from Response",
            command=self.parse_municipal_response,
            width=220,
            state="disabled",
            fg_color="#059669",
            hover_color="#047857"
        )
        self.parse_municipal_btn.pack(side="left", padx=5)

        # Progress/status output
        ctk.CTkLabel(
            tab,
            text="📋 Processing Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=4, column=0, sticky="w", padx=20, pady=(10, 5))

        self.setup_output = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.setup_output.grid(row=5, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tab.grid_rowconfigure(5, weight=1)

    def setup_tab_project(self):
        """Project Input: Enter real building project data"""
        tab = self.tab_project
        tab.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="🏢 Project Information",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            tab,
            text="Enter building project details for BR18 document generation",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Form container
        form_container = ctk.CTkFrame(tab)
        form_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        form_container.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Form fields
        row = 0

        # Project Name
        ctk.CTkLabel(form_container, text="Project Name:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=(15, 10)
        )
        self.project_name_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., Kontorhus Aarhus C")
        self.project_name_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=(15, 10))
        row += 1

        # Address
        ctk.CTkLabel(form_container, text="Address:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.address_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., Åboulevarden 15, 8000 Aarhus C")
        self.address_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Municipality
        ctk.CTkLabel(form_container, text="Municipality:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.municipality_var = ctk.StringVar(value="Aarhus")
        municipality_menu = ctk.CTkOptionMenu(
            form_container,
            variable=self.municipality_var,
            values=["Aarhus", "København", "Aalborg", "Odense", "Esbjerg"]
        )
        municipality_menu.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Building Type
        ctk.CTkLabel(form_container, text="Building Type:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.building_type_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., Office Building")
        self.building_type_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Total Area
        ctk.CTkLabel(form_container, text="Total Area (m²):", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.area_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., 2500")
        self.area_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Number of Floors
        ctk.CTkLabel(form_container, text="Number of Floors:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.floors_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., 5")
        self.floors_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Max Occupancy
        ctk.CTkLabel(form_container, text="Max Occupancy:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.occupancy_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., 150")
        self.occupancy_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Application Category
        ctk.CTkLabel(form_container, text="Application Category:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.app_category_var = ctk.StringVar(value="3")
        app_category_menu = ctk.CTkOptionMenu(
            form_container,
            variable=self.app_category_var,
            values=["1 (Single-family)", "2 (Multi-family)", "3 (Commercial/Office)",
                    "4 (Industrial)", "5 (Assembly)", "6 (Special)"]
        )
        app_category_menu.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Risk Class
        ctk.CTkLabel(form_container, text="Risk Class:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.risk_class_var = ctk.StringVar(value="2")
        risk_class_menu = ctk.CTkOptionMenu(
            form_container,
            variable=self.risk_class_var,
            values=["1", "2", "3", "4"]
        )
        risk_class_menu.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Fire Classification
        ctk.CTkLabel(form_container, text="Fire Classification:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.fire_class_var = ctk.StringVar(value="BK2")
        fire_class_menu = ctk.CTkOptionMenu(
            form_container,
            variable=self.fire_class_var,
            values=["BK1", "BK2", "BK3", "BK4"],
            command=self.update_required_documents
        )
        fire_class_menu.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Consultant Name
        ctk.CTkLabel(form_container, text="Consultant Name:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.consultant_name_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., John Doe")
        self.consultant_name_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Consultant Certificate
        ctk.CTkLabel(form_container, text="Consultant Certificate:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.consultant_cert_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., BRC-12345")
        self.consultant_cert_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Client Name
        ctk.CTkLabel(form_container, text="Client Name:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=15, pady=10
        )
        self.client_name_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., ABC Development A/S")
        self.client_name_entry.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Required Documents (read-only)
        ctk.CTkLabel(form_container, text="Required Documents:", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="nw", padx=15, pady=10
        )
        self.required_docs_label = ctk.CTkTextbox(form_container, height=80, state="disabled")
        self.required_docs_label.grid(row=row, column=1, sticky="ew", padx=15, pady=10)
        row += 1

        # Template buttons
        template_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        template_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            template_frame,
            text="Quick Templates:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            template_frame,
            text="🏢 Office Building (BK2)",
            command=self.load_template_office_bk2,
            width=160,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            template_frame,
            text="🏬 Shopping Center (BK3)",
            command=self.load_template_shopping_bk3,
            width=180,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            template_frame,
            text="🏠 Residential (BK1)",
            command=self.load_template_residential_bk1,
            width=160,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        row += 1

        # Save button
        self.save_project_btn = ctk.CTkButton(
            form_container,
            text="💾 Save Project",
            command=self.save_project,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.save_project_btn.grid(row=row, column=0, columnspan=2, sticky="ew", padx=15, pady=(20, 15))

        # Initialize required docs display
        self.update_required_documents("BK2")

    def setup_tab_generate(self):
        """Generate Documents: Select types and generate"""
        tab = self.tab_generate
        tab.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="📝 Generate BR18 Documents",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Project info display
        self.project_info_label = ctk.CTkLabel(
            tab,
            text="No project loaded. Please create a project in the 'Project Input' tab first.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.project_info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Document type selector
        doc_frame = ctk.CTkFrame(tab)
        doc_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            doc_frame,
            text="Select Document Types to Generate:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Checkboxes
        cb_container = ctk.CTkFrame(doc_frame, fg_color="transparent")
        cb_container.pack(fill="x", padx=15, pady=(0, 10))

        self.doc_types = [
            ("START", "Starterklæring"),
            ("ITT", "Redningsberedskabets indsatsforhold"),
            ("DBK", "Dokumentation for brandklasse"),
            ("BSR", "Brandstrategirapport"),
            ("BPLAN", "Brandplaner og situationsplan"),
            ("PFP", "Pladsfordelingsplaner"),
            ("DIM", "Brandteknisk dimensionering (BK3-4)"),
            ("FUNK", "Funktionsbeskrivelse"),
            ("KPLA", "Kontrolplan"),
            ("KRAP", "Kontrolrapporter"),
            ("DKV", "Drift-, kontrol- og vedligeholdelse"),
            ("SLUT", "Sluterklæring"),
        ]

        self.doc_checkboxes = {}
        for i, (doc_id, doc_name) in enumerate(self.doc_types):
            col = i % 3
            row_idx = i // 3

            cb_frame = ctk.CTkFrame(cb_container, fg_color="transparent")
            cb_frame.grid(row=row_idx, column=col, sticky="w", padx=10, pady=5)

            var = ctk.BooleanVar(value=False)
            self.doc_checkboxes[doc_id] = var

            checkbox = ctk.CTkCheckBox(
                cb_frame,
                text=f"{doc_id}: {doc_name}",
                variable=var,
                font=ctk.CTkFont(size=11)
            )
            checkbox.pack(anchor="w")

        # Without knowledge mode checkbox
        demo_frame = ctk.CTkFrame(doc_frame, fg_color="transparent")
        demo_frame.pack(fill="x", padx=15, pady=(5, 5))

        self.demo_mode_var = ctk.BooleanVar(value=True)
        demo_checkbox = ctk.CTkCheckBox(
            demo_frame,
            text="📚 Generate WITHOUT knowledge (baseline documents for comparison)",
            variable=self.demo_mode_var,
            font=ctk.CTkFont(size=11)
        )
        demo_checkbox.pack(anchor="w")

        # Buttons frame
        gen_btn_frame = ctk.CTkFrame(doc_frame, fg_color="transparent")
        gen_btn_frame.pack(fill="x", padx=15, pady=(10, 15))
        gen_btn_frame.grid_columnconfigure(0, weight=3)
        gen_btn_frame.grid_columnconfigure(1, weight=1)

        # Generate button
        self.generate_btn = ctk.CTkButton(
            gen_btn_frame,
            text="🚀 Generate Documents",
            command=self.generate_documents,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.generate_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Open folder button
        ctk.CTkButton(
            gen_btn_frame,
            text="📁 Open Folder",
            command=self.open_generated_docs_folder,
            height=40,
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=1, sticky="ew")

        # Clear all data button
        ctk.CTkButton(
            doc_frame,
            text="🗑️ Clear All Data (Reset for Fresh Demo)",
            command=self.clear_all_data,
            height=35,
            font=ctk.CTkFont(size=11),
            fg_color="#dc2626",
            hover_color="#b91c1c"
        ).pack(fill="x", padx=15, pady=(5, 15))

        # Output
        ctk.CTkLabel(
            tab,
            text="📋 Generation Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(10, 5))

        self.generate_output = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.generate_output.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tab.grid_rowconfigure(4, weight=1)

    def setup_tab_knowledge_view(self):
        """Tab 5: Knowledge Base Viewer - Browse stored knowledge"""
        tab = self.tab_knowledge_view
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(5, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="🧠 Knowledge Base Browser",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            tab,
            text="View stored knowledge chunks, query the database, and explore patterns",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Stats display
        stats_frame = ctk.CTkFrame(tab)
        stats_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.kb_stats = []
        stat_labels = [
            ("Total Chunks", "0"),
            ("Golden Records", "0"),
            ("Negative Constraints", "0"),
            ("Example Documents", "0"),
            ("Municipalities", "0")
        ]

        for i, (title, value) in enumerate(stat_labels):
            card = ctk.CTkFrame(stats_frame)
            card.grid(row=0, column=i, padx=8, pady=10, sticky="nsew")

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(pady=(8, 0))

            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=18, weight="bold")
            )
            value_label.pack(pady=(5, 8))

            self.kb_stats.append(value_label)

        # Query Interface
        query_frame = ctk.CTkFrame(tab)
        query_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        query_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            query_frame,
            text="🔍 Query Knowledge Base:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # Query input and filters
        query_input_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        query_input_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        query_input_frame.grid_columnconfigure(0, weight=1)

        self.query_entry = ctk.CTkEntry(
            query_input_frame,
            placeholder_text="e.g., Hvad kræver København for redningsåbninger?",
            height=35
        )
        self.query_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Filter options
        filter_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        filter_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            filter_frame,
            text="Municipality Filter:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        self.query_municipality_var = ctk.StringVar(value="All")
        self.query_municipality_menu = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.query_municipality_var,
            values=["All", "København", "Aarhus", "Odense", "Aalborg"],
            width=150
        )
        self.query_municipality_menu.pack(side="left", padx=5)

        self.exclude_rejected_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            filter_frame,
            text="Exclude rejected patterns",
            variable=self.exclude_rejected_var,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=10)

        self.prioritize_approved_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            filter_frame,
            text="Prioritize approved patterns",
            variable=self.prioritize_approved_var,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=10)

        # Query button
        ctk.CTkButton(
            query_frame,
            text="🔍 Search Knowledge Base",
            command=self.query_knowledge_base,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Quick view buttons
        quick_view_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        quick_view_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            quick_view_frame,
            text="Quick Views:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            quick_view_frame,
            text="📊 View All Stats",
            command=self.refresh_knowledge_stats,
            width=120,
            height=28,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            quick_view_frame,
            text="✅ Golden Records",
            command=self.show_golden_records,
            width=130,
            height=28,
            font=ctk.CTkFont(size=10),
            fg_color="#059669",
            hover_color="#047857"
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            quick_view_frame,
            text="⚠️ Negative Constraints",
            command=self.show_negative_constraints,
            width=150,
            height=28,
            font=ctk.CTkFont(size=10),
            fg_color="#dc2626",
            hover_color="#b91c1c"
        ).pack(side="left", padx=3)

        # Results viewer
        ctk.CTkLabel(
            tab,
            text="📚 Results:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=4, column=0, sticky="w", padx=20, pady=(10, 5))

        self.kb_viewer = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=10),
            wrap="word"
        )
        self.kb_viewer.grid(row=5, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tab.grid_rowconfigure(5, weight=1)

        # Load stats immediately when tab is set up
        self.after(100, self.refresh_knowledge_stats)

    # ========== Event Handlers ==========

    # Tab 1: Parse Project (Del 1) callbacks

    def select_project_pdf(self):
        """Select a project specification PDF for parsing"""
        file = filedialog.askopenfilename(
            title="Select Project Specification PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if file:
            self.project_spec_pdf = file
            self.project_pdf_label.configure(text=Path(file).name)
            self.parse_btn.configure(state="normal")

    def parse_project_pdf(self):
        """Parse the selected project PDF and extract building data"""
        if not self.project_spec_pdf:
            messagebox.showerror("Error", "No project PDF selected!")
            return

        def run_parsing():
            sys.stdout = TextRedirector(self.output_queue)
            try:
                # Parse PDF
                self.extracted_project_data = self.project_parser.parse_project_pdf(self.project_spec_pdf)

                # Create BuildingProject
                project = self.project_parser.create_building_project(self.extracted_project_data)

                # Determine required documents
                self.auto_selected_doc_types = self.project_parser.determine_required_documents(project.fire_classification)

                # Store the project
                self.current_project = project

                # Display extracted data
                self.after(0, self.display_extracted_data)

            except Exception as e:
                print(f"\n❌ Error parsing PDF: {e}")
                import traceback
                traceback.print_exc()
            finally:
                sys.stdout = sys.__stdout__

        # Run in background thread
        thread = threading.Thread(target=run_parsing, daemon=True)
        thread.start()

    def display_extracted_data(self):
        """Display extracted project data and auto-selected documents"""
        if not self.extracted_project_data:
            return

        # Display extracted project data
        self.extracted_data_viewer.delete("1.0", "end")
        data = self.extracted_project_data

        display_text = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    EXTRACTED PROJECT DATA                             ║
╚══════════════════════════════════════════════════════════════════════╝

Project Name:        {data.get('project_name')}
Address:             {data.get('address')}
Municipality:        {data.get('municipality')}

Building Type:       {data.get('building_type')}
Total Area:          {data.get('total_area_m2')} m²
Floors:              {data.get('floors')}
Max Occupancy:       {data.get('occupancy')} people
Fire Load:           {data.get('fire_load_mj_m2')} MJ/m²

Application Category: {data.get('application_category')}
Risk Class:          {data.get('risk_class')}
Fire Classification: {data.get('fire_classification')}

Consultant:          {data.get('consultant_name')}
Certificate:         {data.get('consultant_certificate')}
Client:              {data.get('client_name')}
"""
        self.extracted_data_viewer.insert("1.0", display_text)

        # Display auto-selected documents
        self.auto_docs_viewer.delete("1.0", "end")
        fire_class = data.get('fire_classification')

        doc_text = f"""
╔══════════════════════════════════════════════════════════════════════╗
║         AUTO-SELECTED REQUIRED DOCUMENTS ({fire_class})                    ║
╚══════════════════════════════════════════════════════════════════════╝

Fire Classification: {fire_class}
Number of Required Documents: {len(self.auto_selected_doc_types)}

Required Document Types:
"""
        for i, doc_type in enumerate(self.auto_selected_doc_types, 1):
            desc = self.project_parser._get_document_description(doc_type)
            doc_text += f"\n  {i}. {doc_type.value}: {desc}"

        self.auto_docs_viewer.insert("1.0", doc_text)

        # Enable "Use Project" button
        self.use_project_btn.configure(state="normal")

    def use_extracted_project(self):
        """Use the extracted project for document generation"""
        if not self.current_project:
            messagebox.showerror("Error", "No project data extracted!")
            return

        messagebox.showinfo(
            "Success",
            f"✅ Project '{self.current_project.project_name}' is ready!\n\n"
            f"Fire Classification: {self.current_project.fire_classification.value}\n"
            f"Required Documents: {len(self.auto_selected_doc_types)}\n\n"
            f"Go to Tab 3 to generate the automatically selected documents."
        )

        # Switch to generation tab
        self.tabview.set("3️⃣ Generate Documents")

        # Update generate tab with project info and auto-selected docs
        self.update_generate_tab_from_parsed_project()

    def update_generate_tab_from_parsed_project(self):
        """Update the generate tab with parsed project data"""
        # Update project info display
        if self.current_project:
            self.project_info_label.configure(
                text=f"Project: {self.current_project.project_name} | "
                     f"{self.current_project.municipality} | "
                     f"{self.current_project.fire_classification.value} | "
                     f"{len(self.auto_selected_doc_types)} documents required"
            )
            self.generate_btn.configure(state="normal")

        # Auto-select the required document checkboxes
        for doc_type_str, var in self.doc_checkboxes.items():
            doc_type = DocumentType(doc_type_str)
            if doc_type in self.auto_selected_doc_types:
                var.set(True)
            else:
                var.set(False)

    # Tab 2: Knowledge Base Setup (Del 2) callbacks

    def add_pdf_files(self):
        """Add PDF files to the example list"""
        files = filedialog.askopenfilenames(
            title="Select BR18 Example PDF Documents",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if files:
            self.selected_pdf_files.extend(files)
            self.update_file_listbox()
            self.process_btn.configure(state="normal")

    def clear_pdf_files(self):
        """Clear all selected PDF files"""
        self.selected_pdf_files = []
        self.update_file_listbox()
        self.process_btn.configure(state="disabled")

    def update_file_listbox(self):
        """Update the file listbox display"""
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", "end")

        if self.selected_pdf_files:
            for i, filepath in enumerate(self.selected_pdf_files, 1):
                filename = Path(filepath).name
                self.file_listbox.insert("end", f"{i}. {filename}\n   Path: {filepath}\n\n")
        else:
            self.file_listbox.insert("end", "No files selected")

        self.file_listbox.configure(state="disabled")

    def process_example_documents(self):
        """Extract and process example PDF documents"""
        if not self.selected_pdf_files:
            messagebox.showwarning("No Files", "Please add PDF files first!")
            return

        def process():
            try:
                self.is_processing = True
                old_stdout = sys.stdout
                sys.stdout = TextRedirector(self.output_queue)

                print(f"\n🔄 Processing {len(self.selected_pdf_files)} PDF documents...\n")

                # Process each selected PDF
                all_chunks = []
                for pdf_path in self.selected_pdf_files:
                    print(f"\n{'='*80}")
                    print(f"Processing: {Path(pdf_path).name}")
                    print(f"{'='*80}")

                    # Extract content, metadata, and insights
                    result = self.demo_system.pdf_extractor.process_br18_example(pdf_path, extract_insights=True)

                    print(f"  ✓ Extracted {len(result['content'])} characters")
                    print(f"  ✓ Created {result['chunk_count']} chunks")
                    print(f"  ✓ Document type: {result['metadata'].get('document_type', 'Unknown')}")

                    if result.get('insights'):
                        print(f"  ✓ Extracted document-type-specific insights")

                    # Create knowledge chunks from content
                    for chunk_text in result['chunks']:
                        from src.models import KnowledgeChunk
                        import uuid

                        # Merge insights into metadata
                        chunk_metadata = result['metadata'].copy()
                        if result.get('insights'):
                            chunk_metadata['insights'] = result['insights']

                        chunk = KnowledgeChunk(
                            chunk_id=str(uuid.uuid4()),
                            source_type="approved_doc",
                            source_reference=Path(pdf_path).name,
                            municipality=result['metadata'].get('municipality'),
                            document_type=result['metadata'].get('document_type'),
                            content=chunk_text,
                            metadata=chunk_metadata
                        )
                        all_chunks.append(chunk)

                # Add all chunks to vector store
                if all_chunks:
                    print(f"\n\n{'='*80}")
                    print(f"Adding {len(all_chunks)} chunks to vector database...")
                    print(f"{'='*80}")
                    self.demo_system.vector_store.add_chunks_batch(all_chunks)

                print(f"\n✅ Knowledge base initialized successfully!")
                stats = self.demo_system.vector_store.get_stats()
                print(f"   Total chunks: {stats['total_chunks']}")
                print(f"   Example documents: {stats['by_source_type'].get('approved_doc', 0)}")
                print(f"   Municipalities: {list(stats['by_municipality'].keys())}")

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                sys.stdout = old_stdout
                self.is_processing = False

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def upload_br18_regulation(self):
        """Upload and process BR18.pdf regulation document"""
        # File dialog to select BR18.pdf
        br18_path = filedialog.askopenfilename(
            title="Select BR18.pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not br18_path:
            return

        # Verify it's a PDF
        if not br18_path.lower().endswith('.pdf'):
            messagebox.showerror("Invalid File", "Please select a PDF file")
            return

        def process_br18():
            try:
                self.is_processing = True
                old_stdout = sys.stdout
                sys.stdout = TextRedirector(self.output_queue)

                print(f"\n{'='*80}")
                print(f"📖 PROCESSING BR18 REGULATION")
                print(f"{'='*80}\n")

                print(f"Selected file: {Path(br18_path).name}")
                print(f"File size: {Path(br18_path).stat().st_size / 1024:.1f} KB\n")

                # Custom extraction prompt for regulation document
                regulation_prompt = """Extract all text content from this BR18 (Building Regulations 2018) document.

IMPORTANT - Preserve structure and paragraph references:
- All paragraph numbers (§508, §509, §93, etc.)
- Section headings and subsection numbers
- Tables with requirements
- Lists of requirements
- Any cross-references between paragraphs

Format the output as structured text with clear section breaks.
Keep paragraph numbers (§) with their corresponding text."""

                print("🔍 Extracting BR18 content with Gemini Vision...")
                content = self.demo_system.pdf_extractor.extract_with_gemini(
                    br18_path,
                    extraction_prompt=regulation_prompt
                )
                print(f"✅ Extracted {len(content)} characters, {len(content.split())} words\n")

                # Chunk with larger size to preserve § paragraph context
                print("✂️  Creating regulation chunks (800 words/chunk)...")
                chunks = self.demo_system.pdf_extractor.chunk_document(
                    content,
                    chunk_size=800,
                    overlap=100
                )
                print(f"✅ Created {len(chunks)} regulation chunks\n")

                # Create knowledge chunks
                print("📊 Adding BR18 regulation to vector store...")
                from src.models import KnowledgeChunk
                import uuid
                from datetime import datetime

                knowledge_chunks = []
                for i, chunk_text in enumerate(chunks):
                    chunk = KnowledgeChunk(
                        chunk_id=str(uuid.uuid4()),
                        source_type="regulation",  # Mark as regulation
                        source_reference="BR18.pdf",
                        municipality=None,  # Applies to all municipalities
                        document_type=None,  # Not a specific doc type
                        content=chunk_text,
                        metadata={
                            "regulation_name": "BR18",
                            "regulation_year": "2018",
                            "section": "Fire Safety",
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "added_date": datetime.now().isoformat()
                        }
                    )
                    knowledge_chunks.append(chunk)

                # Check if BR18 already exists and delete old version
                print("\n🔍 Checking for existing BR18 regulation...")
                deleted_count = self.demo_system.vector_store.delete_by_source(
                    source_reference="BR18.pdf",
                    source_type="regulation"
                )

                if deleted_count > 0:
                    print(f"🗑️  Removed {deleted_count} chunks from old BR18 version")
                    print(f"📝 Replacing with new BR18 version...")

                # Add new BR18 to vector store
                self.demo_system.vector_store.add_chunks_batch(knowledge_chunks)

                print(f"\n✅ BR18 regulation successfully {'updated' if deleted_count > 0 else 'added'}!")
                stats = self.demo_system.vector_store.get_stats()
                print(f"\n📈 Vector Store Statistics:")
                print(f"   Total chunks: {stats['total_chunks']}")
                print(f"   By source type: {stats['by_source_type']}")
                print(f"\n🎯 Document generation will now include accurate BR18 § citations!")

                # Update status label
                self.br18_status_label.configure(
                    text=f"Status: ✅ Loaded ({len(chunks)} chunks)",
                    text_color="#10b981"
                )

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                self.br18_status_label.configure(
                    text="Status: ❌ Error during upload",
                    text_color="#dc2626"
                )
            finally:
                sys.stdout = old_stdout
                self.is_processing = False

        thread = threading.Thread(target=process_br18, daemon=True)
        thread.start()

    def check_br18_status(self):
        """Check if BR18 regulation is already loaded in vector store"""
        try:
            stats = self.demo_system.vector_store.get_stats()
            regulation_count = stats['by_source_type'].get('regulation', 0)

            if regulation_count > 0:
                self.br18_status_label.configure(
                    text=f"Status: ✅ Already loaded ({regulation_count} chunks)",
                    text_color="#10b981"
                )
            else:
                self.br18_status_label.configure(
                    text="Status: Not uploaded",
                    text_color="#dc2626"
                )
        except Exception as e:
            print(f"Warning: Could not check BR18 status: {e}")

    def load_template_office_bk2(self):
        """Load office building BK2 template"""
        self.project_name_entry.delete(0, "end")
        self.project_name_entry.insert(0, "Kontorhus Aarhus City")

        self.address_entry.delete(0, "end")
        self.address_entry.insert(0, "Åboulevarden 23, 8000 Aarhus C")

        self.municipality_var.set("Aarhus")

        self.building_type_entry.delete(0, "end")
        self.building_type_entry.insert(0, "Commercial Office Building")

        self.area_entry.delete(0, "end")
        self.area_entry.insert(0, "2500")

        self.floors_entry.delete(0, "end")
        self.floors_entry.insert(0, "5")

        self.occupancy_entry.delete(0, "end")
        self.occupancy_entry.insert(0, "150")

        self.app_category_var.set("3 (Commercial/Office)")
        self.risk_class_var.set("2")
        self.fire_class_var.set("BK2")

        self.consultant_name_entry.delete(0, "end")
        self.consultant_name_entry.insert(0, "Lars Nielsen")

        self.consultant_cert_entry.delete(0, "end")
        self.consultant_cert_entry.insert(0, "BRC-4523")

        self.client_name_entry.delete(0, "end")
        self.client_name_entry.insert(0, "Aarhus Ejendomme A/S")

        self.update_required_documents("BK2")

    def load_template_shopping_bk3(self):
        """Load shopping center BK3 template"""
        self.project_name_entry.delete(0, "end")
        self.project_name_entry.insert(0, "City Shopping Center")

        self.address_entry.delete(0, "end")
        self.address_entry.insert(0, "Nørregade 15, 1165 København K")

        self.municipality_var.set("København")

        self.building_type_entry.delete(0, "end")
        self.building_type_entry.insert(0, "Shopping Center / Retail")

        self.area_entry.delete(0, "end")
        self.area_entry.insert(0, "8500")

        self.floors_entry.delete(0, "end")
        self.floors_entry.insert(0, "3")

        self.occupancy_entry.delete(0, "end")
        self.occupancy_entry.insert(0, "500")

        self.app_category_var.set("5 (Assembly)")
        self.risk_class_var.set("3")
        self.fire_class_var.set("BK3")

        self.consultant_name_entry.delete(0, "end")
        self.consultant_name_entry.insert(0, "Mette Hansen")

        self.consultant_cert_entry.delete(0, "end")
        self.consultant_cert_entry.insert(0, "BRC-7821")

        self.client_name_entry.delete(0, "end")
        self.client_name_entry.insert(0, "Retail Properties Denmark ApS")

        self.update_required_documents("BK3")

    def load_template_residential_bk1(self):
        """Load residential building BK1 template"""
        self.project_name_entry.delete(0, "end")
        self.project_name_entry.insert(0, "Parcelhus Aalborg")

        self.address_entry.delete(0, "end")
        self.address_entry.insert(0, "Skovvej 12, 9000 Aalborg")

        self.municipality_var.set("Aalborg")

        self.building_type_entry.delete(0, "end")
        self.building_type_entry.insert(0, "Single-family Residence")

        self.area_entry.delete(0, "end")
        self.area_entry.insert(0, "180")

        self.floors_entry.delete(0, "end")
        self.floors_entry.insert(0, "2")

        self.occupancy_entry.delete(0, "end")
        self.occupancy_entry.insert(0, "6")

        self.app_category_var.set("1 (Single-family)")
        self.risk_class_var.set("1")
        self.fire_class_var.set("BK1")

        self.consultant_name_entry.delete(0, "end")
        self.consultant_name_entry.insert(0, "Peter Andersen")

        self.consultant_cert_entry.delete(0, "end")
        self.consultant_cert_entry.insert(0, "BRC-2341")

        self.client_name_entry.delete(0, "end")
        self.client_name_entry.insert(0, "Jensen Familie")

        self.update_required_documents("BK1")

    def update_required_documents(self, fire_class):
        """Update the required documents display based on fire classification"""
        fire_class_map = {
            "BK1": FireClassification.BK1,
            "BK2": FireClassification.BK2,
            "BK3": FireClassification.BK3,
            "BK4": FireClassification.BK4
        }

        # Create a temporary project to get required docs
        temp_project = BuildingProject(
            project_name="Temp",
            address="Temp Address",
            municipality="Aarhus",
            building_type="Office",
            total_area_m2=1000,
            floors=3,
            occupancy=50,
            application_category=ApplicationCategory.CAT_3,
            risk_class=RiskClass.RISK_2,
            fire_classification=fire_class_map[fire_class],
            consultant_name="Temp Consultant",
            consultant_certificate="TEMP-123",
            client_name="Temp Client"
        )

        required = temp_project.get_required_documents()

        self.required_docs_label.configure(state="normal")
        self.required_docs_label.delete("1.0", "end")
        self.required_docs_label.insert("end", f"{len(required)} documents required:\n")
        self.required_docs_label.insert("end", ", ".join(required))
        self.required_docs_label.configure(state="disabled")

    def save_project(self):
        """Save the current project"""
        # Validate inputs
        if not self.project_name_entry.get():
            messagebox.showwarning("Missing Data", "Please enter a project name!")
            return

        try:
            fire_class_map = {
                "BK1": FireClassification.BK1,
                "BK2": FireClassification.BK2,
                "BK3": FireClassification.BK3,
                "BK4": FireClassification.BK4
            }

            # Extract category number from dropdown value (e.g., "3 (Commercial/Office)" -> "3")
            app_cat_str = self.app_category_var.get().split()[0]
            app_category_map = {
                "1": ApplicationCategory.CAT_1,
                "2": ApplicationCategory.CAT_2,
                "3": ApplicationCategory.CAT_3,
                "4": ApplicationCategory.CAT_4,
                "5": ApplicationCategory.CAT_5,
                "6": ApplicationCategory.CAT_6,
            }

            risk_class_map = {
                "1": RiskClass.RISK_1,
                "2": RiskClass.RISK_2,
                "3": RiskClass.RISK_3,
                "4": RiskClass.RISK_4,
            }

            self.current_project = BuildingProject(
                project_name=self.project_name_entry.get(),
                address=self.address_entry.get() or "Not specified",
                municipality=self.municipality_var.get(),
                building_type=self.building_type_entry.get() or "Not specified",
                total_area_m2=float(self.area_entry.get()) if self.area_entry.get() else 0,
                floors=int(self.floors_entry.get()) if self.floors_entry.get() else 1,
                occupancy=int(self.occupancy_entry.get()) if self.occupancy_entry.get() else 0,
                application_category=app_category_map[app_cat_str],
                risk_class=risk_class_map[self.risk_class_var.get()],
                fire_classification=fire_class_map[self.fire_class_var.get()],
                consultant_name=self.consultant_name_entry.get() or "Not specified",
                consultant_certificate=self.consultant_cert_entry.get() or "Not specified",
                client_name=self.client_name_entry.get() or "Not specified"
            )

            # Update project info display in generate tab
            required = self.current_project.get_required_documents()
            self.project_info_label.configure(
                text=f"Project: {self.current_project.project_name} | "
                     f"{self.current_project.municipality} | "
                     f"{self.fire_class_var.get()} | "
                     f"{len(required)} documents required"
            )

            # Enable generate button and set checkboxes
            self.generate_btn.configure(state="normal")
            for doc_id, var in self.doc_checkboxes.items():
                var.set(doc_id in required)

            messagebox.showinfo("Success", f"Project '{self.current_project.project_name}' saved!\n\nGo to 'Generate Documents' tab to continue.")

        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your numeric inputs:\n{str(e)}")

    def clear_all_data(self):
        """Clear all generated data for fresh demo"""
        if self.is_processing:
            messagebox.showwarning("Processing", "Please wait for current operation to complete!")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Clear All Data?",
            "This will delete:\n\n"
            "• Vector database (all indexed documents and learned insights)\n"
            "• Generated BR18 documents\n"
            "• All feedback data\n\n"
            "This prepares the system for a clean demo run.\n\n"
            "Are you sure you want to continue?"
        )

        if not response:
            return

        def clear_data():
            try:
                self.is_processing = True

                # Clear vector database
                self.demo_system.vector_store.clear()

                # Clear generated documents folder
                import shutil
                output_dir = Path("data/generated_docs")
                if output_dir.exists():
                    shutil.rmtree(output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)

                # Reset GUI state
                self.generated_documents = []
                self.current_project = None

                # Reset project info
                self.project_info_label.configure(
                    text="No project loaded. Please create a project in the 'Project Input' tab first."
                )
                self.generate_btn.configure(state="disabled")

                messagebox.showinfo(
                    "Data Cleared",
                    "All data has been cleared!\n\n"
                    "Ready for fresh demo:\n"
                    "1. Tab 1: Extract example PDFs\n"
                    "2. Tab 2: Create project\n"
                    "3. Tab 3: Generate documents"
                )

            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear data:\n{str(e)}")
            finally:
                self.is_processing = False

        # Run in background thread
        import threading
        thread = threading.Thread(target=clear_data, daemon=True)
        thread.start()

    def open_generated_docs_folder(self):
        """Open the folder containing generated documents"""
        import subprocess
        import platform

        output_dir = Path("data/generated_docs")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert to absolute path
        abs_path = output_dir.absolute()

        try:
            if platform.system() == "Windows":
                os.startfile(abs_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", abs_path])
            else:  # Linux
                subprocess.run(["xdg-open", abs_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{str(e)}\n\nPath: {abs_path}")

    def save_document_to_file(self, doc, prefix="", demo_mode=False):
        """Save a generated document to file"""
        import os
        from datetime import datetime

        # Create output directory based on demo mode
        if demo_mode:
            output_dir = Path("data/generated_docs/without_knowledge")
        else:
            output_dir = Path("data/generated_docs/with_knowledge")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with knowledge indicator
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_project_name = "".join(c for c in doc.project.project_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_project_name = safe_project_name.replace(' ', '_')

        # Add knowledge indicator to filename
        knowledge_indicator = "without_knowledge" if demo_mode else "with_knowledge"

        if prefix:
            filename = f"{safe_project_name}_{doc.document_type.value}_{knowledge_indicator}_{prefix}_{timestamp}.txt"
        else:
            filename = f"{safe_project_name}_{doc.document_type.value}_{knowledge_indicator}_{timestamp}.txt"

        filepath = output_dir / filename

        # Write document content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{'='*80}\n")
            f.write(f"BR18 DOCUMENT - {doc.document_type.value}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Project: {doc.project.project_name}\n")
            f.write(f"Address: {doc.project.address}\n")
            f.write(f"Municipality: {doc.project.municipality}\n")
            f.write(f"Fire Classification: {doc.project.fire_classification.value}\n")
            f.write(f"Building Type: {doc.project.building_type}\n")
            f.write(f"Total Area: {doc.project.total_area_m2} m²\n")
            f.write(f"Floors: {doc.project.floors}\n")
            f.write(f"Max Occupancy: {doc.project.occupancy}\n\n")
            f.write(f"Consultant: {doc.project.consultant_name}\n")
            f.write(f"Certificate: {doc.project.consultant_certificate}\n")
            f.write(f"Client: {doc.project.client_name}\n\n")
            f.write(f"Generated: {doc.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Document ID: {doc.document_id}\n")
            f.write(f"\n{'='*80}\n")
            f.write(f"DOCUMENT CONTENT\n")
            f.write(f"{'='*80}\n\n")
            f.write(doc.content)

        print(f"     💾 Saved to: {filepath}")

    def generate_documents(self):
        """Generate selected documents for the current project"""
        if not self.current_project:
            messagebox.showwarning("No Project", "Please save a project first!")
            return

        selected = [doc_id for doc_id, var in self.doc_checkboxes.items() if var.get()]
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one document type!")
            return

        def generate():
            try:
                self.is_processing = True
                old_stdout = sys.stdout
                sys.stdout = TextRedirector(self.output_queue)

                print(f"\n🚀 Generating {len(selected)} documents for: {self.current_project.project_name}\n")

                self.generated_documents = []

                # Check if demo mode is enabled
                use_demo_mode = self.demo_mode_var.get()

                if use_demo_mode:
                    print(f"\n⚠️  Generating WITHOUT learned knowledge")
                    print(f"   Documents will not use RAG context from knowledge base")
                    print(f"   This demonstrates the 'without knowledge' baseline\n")

                for doc_type_str in selected:
                    doc_type = DocumentType(doc_type_str)

                    # Get RAG context (skip in demo mode to show "without knowledge")
                    if use_demo_mode:
                        rag_context = []  # No context = without knowledge baseline
                        print(f"  📝 Generating {doc_type_str} (WITHOUT knowledge)...")
                    else:
                        rag_context = self.demo_system.vector_store.retrieve_context(
                            query=f"{doc_type_str} document for {self.current_project.municipality}",
                            top_k=5
                        )
                        print(f"  📝 Generating {doc_type_str} (WITH knowledge - {len(rag_context)} context chunks)...")

                    # Generate document
                    doc = self.demo_system.template_engine.generate_document(
                        self.current_project,
                        doc_type,
                        rag_context
                    )
                    self.generated_documents.append(doc)
                    print(f"     ✅ Generated ({len(doc.content)} chars)")

                    # Save document to file (pass demo_mode flag)
                    self.save_document_to_file(doc, demo_mode=use_demo_mode)

                print(f"\n✅ All {len(selected)} documents generated successfully!")

                if use_demo_mode:
                    print(f"\n📁 Documents saved to: data/generated_docs/without_knowledge/")
                else:
                    print(f"\n📁 Documents saved to: data/generated_docs/with_knowledge/")

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                sys.stdout = old_stdout
                self.is_processing = False

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def select_municipal_response(self):
        """Select a municipal response file (Afslag/Godkendelse)"""
        file = filedialog.askopenfilename(
            title="Select Municipal Response (Afslag/Godkendelse)",
            filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if file:
            self.municipal_response_pdf = file
            self.municipal_response_label.configure(text=Path(file).name)
            self.parse_municipal_btn.configure(state="normal")

    def parse_municipal_response(self):
        """Parse municipal response and create golden records or negative constraints"""
        if not self.municipal_response_pdf:
            messagebox.showerror("Error", "No municipal response selected!")
            return

        def run_parsing():
            sys.stdout = TextRedirector(self.output_queue)
            try:
                print(f"\n🔄 Parsing municipal response: {Path(self.municipal_response_pdf).name}\n")

                # Detect if rejection or approval based on filename or content
                filename = Path(self.municipal_response_pdf).name.lower()

                if "afslag" in filename or "reject" in filename:
                    # Parse as rejection
                    print("📋 Detected: REJECTION (Afslag)")
                    rejection_data = self.municipal_parser.parse_rejection(self.municipal_response_pdf)

                    print(f"\n✅ Extracted from rejection:")
                    print(f"   Municipality: {rejection_data.get('municipality')}")
                    print(f"   Rejection reasons: {len(rejection_data.get('rejection_reasons', []))}")
                    print(f"   Negative constraints: {len(rejection_data.get('negative_constraints', []))}")

                    # Create knowledge chunks
                    neg_chunks = self.municipal_parser.create_knowledge_chunks_from_rejection(rejection_data)

                    # Add to vector store
                    self.demo_system.vector_store.add_chunks_batch(neg_chunks)

                    print(f"\n✅ Added {len(neg_chunks)} negative constraint chunks to knowledge base")
                    print(f"\n💡 These patterns will be AVOIDED in future document generation")

                    # Show examples
                    print("\nExample negative constraints:")
                    for i, chunk in enumerate(neg_chunks[:3], 1):
                        print(f"\n{i}. {chunk.content[:120]}...")
                        conf = chunk.metadata.get('confidence_score')
                        conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else conf
                        print(f"   Confidence: {conf_str}")
                        print(f"   Status: {chunk.metadata.get('approval_status')}")

                elif "godkend" in filename or "approval" in filename:
                    # Parse as approval
                    print("📋 Detected: APPROVAL (Godkendelse)")
                    approval_data = self.municipal_parser.parse_approval(self.municipal_response_pdf)

                    print(f"\n✅ Extracted from approval:")
                    print(f"   Municipality: {approval_data.get('municipality')}")
                    print(f"   Successful elements: {len(approval_data.get('successful_elements', []))}")
                    print(f"   Golden patterns: {len(approval_data.get('golden_patterns', []))}")

                    # Create knowledge chunks
                    golden_chunks = self.municipal_parser.create_knowledge_chunks_from_approval(approval_data)

                    # Add to vector store
                    self.demo_system.vector_store.add_chunks_batch(golden_chunks)

                    print(f"\n✅ Added {len(golden_chunks)} golden record chunks to knowledge base")
                    print(f"\n💡 These patterns will be PRIORITIZED in future document generation")

                    # Show examples
                    print("\nExample golden records:")
                    for i, chunk in enumerate(golden_chunks[:3], 1):
                        print(f"\n{i}. {chunk.content[:120]}...")
                        conf = chunk.metadata.get('confidence_score')
                        conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else conf
                        print(f"   Confidence: {conf_str}")

                        # Show calculation breakdown if available
                        breakdown = chunk.metadata.get('confidence_breakdown')
                        if breakdown:
                            print(f"   Calculation: {breakdown.get('calculation', 'N/A')}")

                        print(f"   Status: {chunk.metadata.get('approval_status')}")
                else:
                    print("⚠️  Could not auto-detect type. Please include 'Afslag' or 'Godkendelse' in filename.")
                    return

                # Show updated stats
                stats = self.demo_system.vector_store.get_stats()
                print(f"\n📊 Knowledge base now has:")
                print(f"   Total chunks: {stats['total_chunks']}")
                print(f"   Golden records: {stats.get('golden_records', 0)}")
                print(f"   Negative constraints: {stats.get('negative_constraints', 0)}")

            except Exception as e:
                print(f"\n❌ Error parsing municipal response: {e}")
                import traceback
                traceback.print_exc()
            finally:
                sys.stdout = sys.__stdout__

        # Run in background thread
        thread = threading.Thread(target=run_parsing, daemon=True)
        thread.start()

    # Tab 5: Knowledge Base Query callbacks

    def query_knowledge_base(self):
        """Query the knowledge base with user input"""
        query = self.query_entry.get().strip()

        if not query:
            messagebox.showwarning("Empty Query", "Please enter a search query!")
            return

        try:
            # Get filter settings
            municipality = self.query_municipality_var.get()
            municipality_filter = None if municipality == "All" else municipality
            exclude_rejected = self.exclude_rejected_var.get()
            prioritize_approved = self.prioritize_approved_var.get()

            # Search knowledge base with configurable result limit
            # User can adjust this - default 10 for GUI display
            result_limit = 10  # TODO: Make this configurable via GUI slider
            chunks = self.demo_system.vector_store.search_with_confidence(
                query=query,
                municipality=municipality_filter,
                top_k=result_limit,
                exclude_rejected=exclude_rejected,
                prioritize_approved=prioritize_approved
            )

            # Display results
            self.kb_viewer.configure(state="normal")
            self.kb_viewer.delete("1.0", "end")

            self.kb_viewer.insert("end", f"Query: {query}\n")
            if municipality_filter:
                self.kb_viewer.insert("end", f"Municipality Filter: {municipality_filter}\n")
            self.kb_viewer.insert("end", f"{'='*80}\n\n")

            if chunks:
                self.kb_viewer.insert("end", f"Found {len(chunks)} relevant knowledge chunks:\n\n")

                for i, chunk in enumerate(chunks, 1):
                    self.kb_viewer.insert("end", f"{'─'*80}\n")
                    self.kb_viewer.insert("end", f"RESULT {i}\n")
                    self.kb_viewer.insert("end", f"{'─'*80}\n")
                    self.kb_viewer.insert("end", f"Source Type: {chunk.source_type}\n")
                    if chunk.municipality:
                        self.kb_viewer.insert("end", f"Municipality: {chunk.municipality}\n")

                    # Format confidence with 2 decimals
                    conf = chunk.metadata.get('confidence_score', 'N/A')
                    if isinstance(conf, (int, float)):
                        self.kb_viewer.insert("end", f"Confidence: {conf:.2f}\n")
                    else:
                        self.kb_viewer.insert("end", f"Confidence: {conf}\n")

                    # Show calculation breakdown if available
                    breakdown = chunk.metadata.get('confidence_breakdown')
                    if breakdown:
                        self.kb_viewer.insert("end", f"  → Calculation: {breakdown.get('calculation', 'N/A')}\n")

                    approval_status = chunk.metadata.get('approval_status', 'unknown')
                    if approval_status == 'approved':
                        self.kb_viewer.insert("end", f"Status: ✅ APPROVED (Golden Record)\n")
                    elif approval_status == 'rejected':
                        self.kb_viewer.insert("end", f"Status: ⚠️ REJECTED (Negative Constraint)\n")
                    else:
                        self.kb_viewer.insert("end", f"Status: {approval_status}\n")
                    self.kb_viewer.insert("end", f"\nContent:\n{chunk.content}\n\n")
            else:
                self.kb_viewer.insert("end", "❌ No results found.\n\n")
                self.kb_viewer.insert("end", "Suggestions:\n")
                self.kb_viewer.insert("end", "• Try a different query\n")
                self.kb_viewer.insert("end", "• Remove municipality filter\n")
                self.kb_viewer.insert("end", "• Upload more example documents\n")

            self.kb_viewer.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to query knowledge base:\n{str(e)}")

    def show_golden_records(self):
        """Show all golden records (approved patterns)"""
        try:
            golden = self.demo_system.vector_store.get_golden_records(min_confidence=0.8)

            self.kb_viewer.configure(state="normal")
            self.kb_viewer.delete("1.0", "end")

            self.kb_viewer.insert("end", f"✅ GOLDEN RECORDS (Best Practices)\n")
            self.kb_viewer.insert("end", f"{'='*80}\n\n")

            if golden:
                self.kb_viewer.insert("end", f"Found {len(golden)} golden record patterns:\n\n")

                for i, chunk in enumerate(golden[:20], 1):  # Show first 20
                    self.kb_viewer.insert("end", f"{'─'*80}\n")
                    conf = chunk.metadata.get('confidence_score')
                    conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else conf
                    self.kb_viewer.insert("end", f"{i}. [{chunk.municipality or 'General'}] ")
                    self.kb_viewer.insert("end", f"(confidence: {conf_str})\n")

                    # Show calculation breakdown if available
                    breakdown = chunk.metadata.get('confidence_breakdown')
                    if breakdown:
                        self.kb_viewer.insert("end", f"   Calculation: {breakdown.get('calculation', 'N/A')}\n")

                    self.kb_viewer.insert("end", f"{'─'*80}\n")
                    self.kb_viewer.insert("end", f"{chunk.content}\n\n")
            else:
                self.kb_viewer.insert("end", "No golden records yet.\n\n")
                self.kb_viewer.insert("end", "Upload approved documents (Godkendelse) to create them.\n")

            self.kb_viewer.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show golden records:\n{str(e)}")

    def show_negative_constraints(self):
        """Show all negative constraints (rejected patterns)"""
        try:
            negative = self.demo_system.vector_store.get_negative_constraints()

            self.kb_viewer.configure(state="normal")
            self.kb_viewer.delete("1.0", "end")

            self.kb_viewer.insert("end", f"⚠️ NEGATIVE CONSTRAINTS (What to Avoid)\n")
            self.kb_viewer.insert("end", f"{'='*80}\n\n")

            if negative:
                self.kb_viewer.insert("end", f"Found {len(negative)} patterns to avoid:\n\n")

                for i, chunk in enumerate(negative[:20], 1):  # Show first 20
                    self.kb_viewer.insert("end", f"{'─'*80}\n")
                    conf = chunk.metadata.get('confidence_score')
                    conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else conf
                    self.kb_viewer.insert("end", f"{i}. [{chunk.municipality or 'General'}] ")
                    self.kb_viewer.insert("end", f"(confidence: {conf_str})\n")

                    # Show calculation breakdown if available
                    breakdown = chunk.metadata.get('confidence_breakdown')
                    if breakdown:
                        self.kb_viewer.insert("end", f"   Calculation: {breakdown.get('calculation', 'N/A')}\n")

                    self.kb_viewer.insert("end", f"{'─'*80}\n")
                    self.kb_viewer.insert("end", f"{chunk.content}\n\n")
            else:
                self.kb_viewer.insert("end", "No negative constraints yet.\n\n")
                self.kb_viewer.insert("end", "Upload rejection documents (Afslag) to create them.\n")

            self.kb_viewer.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show negative constraints:\n{str(e)}")

    def refresh_knowledge_stats(self):
        """Refresh knowledge base statistics"""
        try:
            stats = self.demo_system.vector_store.get_stats()

            # Update stats cards
            self.kb_stats[0].configure(text=str(stats['total_chunks']))
            self.kb_stats[1].configure(text=str(stats.get('golden_records', 0)))
            self.kb_stats[2].configure(text=str(stats.get('negative_constraints', 0)))
            self.kb_stats[3].configure(text=str(stats['by_source_type'].get('approved_doc', 0)))
            self.kb_stats[4].configure(text=str(len(stats['by_municipality'])))

            # Update viewer with chunk details
            self.kb_viewer.configure(state="normal")
            self.kb_viewer.delete("1.0", "end")

            self.kb_viewer.insert("end", f"Knowledge Base Statistics\n{'='*80}\n\n")
            self.kb_viewer.insert("end", f"Total Chunks: {stats['total_chunks']}\n")
            self.kb_viewer.insert("end", f"Golden Records: {stats.get('golden_records', 0)}\n")
            self.kb_viewer.insert("end", f"Negative Constraints: {stats.get('negative_constraints', 0)}\n\n")

            self.kb_viewer.insert("end", "By Source Type:\n")
            for source_type, count in stats['by_source_type'].items():
                self.kb_viewer.insert("end", f"  • {source_type}: {count}\n")

            self.kb_viewer.insert("end", "\nBy Municipality:\n")
            for municipality, count in stats['by_municipality'].items():
                self.kb_viewer.insert("end", f"  • {municipality}: {count}\n")

            if 'by_approval_status' in stats:
                self.kb_viewer.insert("end", "\nBy Approval Status:\n")
                for status, count in stats['by_approval_status'].items():
                    self.kb_viewer.insert("end", f"  • {status}: {count}\n")

            if 'confidence_distribution' in stats:
                self.kb_viewer.insert("end", "\nConfidence Distribution:\n")
                for level, count in stats['confidence_distribution'].items():
                    self.kb_viewer.insert("end", f"  • {level}: {count}\n")

            self.kb_viewer.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh stats:\n{str(e)}")

    def check_queue(self):
        """Check queue for output from background threads"""
        try:
            while True:
                msg = self.output_queue.get_nowait()

                # Write to appropriate output widget based on current tab
                current_tab = self.tabview.get()

                if "Parse Project" in current_tab or "Del 1" in current_tab:
                    output_widget = self.parse_output
                elif "Knowledge Base" in current_tab or "Del 2" in current_tab:
                    output_widget = self.setup_output
                elif "Generate" in current_tab:
                    output_widget = self.generate_output
                else:
                    # Default to parse output
                    output_widget = self.parse_output

                output_widget.configure(state="normal")
                output_widget.insert("end", msg)
                output_widget.see("end")
                output_widget.configure(state="disabled")

        except queue.Empty:
            pass

        self.after(100, self.check_queue)


if __name__ == "__main__":
    app = BR18PrototypeGUI()
    app.mainloop()
