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
        self.is_processing = False

        # Data storage
        self.selected_pdf_files = []
        self.current_project = None
        self.generated_documents = []
        self.feedbacks_given = []

        # Create tabbed interface
        self.setup_tabbed_interface()

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

        # Add tabs
        self.tab_setup = self.tabview.add("1️⃣ Setup & Examples")
        self.tab_project = self.tabview.add("2️⃣ Project Input")
        self.tab_generate = self.tabview.add("3️⃣ Generate Documents")
        self.tab_feedback = self.tabview.add("4️⃣ Review & Feedback")
        self.tab_knowledge = self.tabview.add("5️⃣ Knowledge Base")

        # Setup each tab
        self.setup_tab_setup()
        self.setup_tab_project()
        self.setup_tab_generate()
        self.setup_tab_feedback()
        self.setup_tab_knowledge()

    def setup_tab_setup(self):
        """Setup: Select example PDFs and initialize knowledge base"""
        tab = self.tab_setup
        tab.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="📚 Setup: Example Documents & Knowledge Base",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            tab,
            text="Select approved BR18 example documents to build the initial knowledge base",
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

        # Progress/status output
        ctk.CTkLabel(
            tab,
            text="📋 Processing Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(10, 5))

        self.setup_output = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.setup_output.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tab.grid_rowconfigure(4, weight=1)

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

    def setup_tab_feedback(self):
        """Review & Feedback: View documents and provide feedback"""
        tab = self.tab_feedback
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="✅ Review Generated Documents",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        self.feedback_status_label = ctk.CTkLabel(
            tab,
            text="No documents generated yet. Generate documents first.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.feedback_status_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Document viewer and feedback panel (side by side)
        review_container = ctk.CTkFrame(tab)
        review_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        review_container.grid_columnconfigure(0, weight=2)
        review_container.grid_columnconfigure(1, weight=1)
        review_container.grid_rowconfigure(0, weight=1)

        # Left: Document viewer
        viewer_frame = ctk.CTkFrame(review_container)
        viewer_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        viewer_frame.grid_rowconfigure(1, weight=1)
        viewer_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            viewer_frame,
            text="Document Viewer:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        self.doc_viewer = ctk.CTkTextbox(
            viewer_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.doc_viewer.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # Right: Feedback panel
        feedback_panel = ctk.CTkFrame(review_container)
        feedback_panel.grid(row=0, column=1, sticky="nsew")
        feedback_panel.grid_rowconfigure(4, weight=1)
        feedback_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            feedback_panel,
            text="Provide Feedback:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # Document selector
        ctk.CTkLabel(
            feedback_panel,
            text="Select Document:",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(5, 5))

        self.doc_selector_var = ctk.StringVar(value="")
        self.doc_selector = ctk.CTkOptionMenu(
            feedback_panel,
            variable=self.doc_selector_var,
            values=["No documents"],
            command=self.display_selected_document,
            state="disabled"
        )
        self.doc_selector.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))

        # Approval buttons
        approval_frame = ctk.CTkFrame(feedback_panel, fg_color="transparent")
        approval_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        approval_frame.grid_columnconfigure((0, 1), weight=1)

        self.approve_btn = ctk.CTkButton(
            approval_frame,
            text="✅ Approve",
            command=lambda: self.submit_feedback(True),
            fg_color="#059669",
            hover_color="#047857",
            state="disabled"
        )
        self.approve_btn.grid(row=0, column=0, sticky="ew", padx=5)

        self.reject_btn = ctk.CTkButton(
            approval_frame,
            text="❌ Reject",
            command=lambda: self.submit_feedback(False),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            state="disabled"
        )
        self.reject_btn.grid(row=0, column=1, sticky="ew", padx=5)

        # Rejection reasons (only shown when rejecting)
        ctk.CTkLabel(
            feedback_panel,
            text="Rejection Reasons:",
            font=ctk.CTkFont(size=12)
        ).grid(row=4, column=0, sticky="nw", padx=15, pady=(0, 5))

        # Template rejection reasons
        template_reasons_frame = ctk.CTkFrame(feedback_panel, fg_color="transparent")
        template_reasons_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 5))

        ctk.CTkLabel(
            template_reasons_frame,
            text="Quick Add:",
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=5)

        reason_buttons = [
            ("Missing BR18 §", "Missing specific BR18 paragraph references (e.g., §508)"),
            ("Unclear distances", "Evacuation distances not clearly specified"),
            ("Fire resistance", "Incorrect or missing fire resistance class specifications"),
            ("Material class", "Missing material classifications (e.g., K1 10/B-s1,d0)"),
            ("Rescue access", "Incomplete rescue service access routes and conditions"),
        ]

        for btn_text, reason_text in reason_buttons:
            ctk.CTkButton(
                template_reasons_frame,
                text=btn_text,
                command=lambda r=reason_text: self.add_rejection_reason(r),
                width=100,
                height=22,
                font=ctk.CTkFont(size=9)
            ).pack(side="left", padx=2)

        self.rejection_text = ctk.CTkTextbox(
            feedback_panel,
            height=120
        )
        self.rejection_text.grid(row=6, column=0, sticky="nsew", padx=15, pady=(5, 15))

        # Learn from feedback button
        self.learn_btn = ctk.CTkButton(
            feedback_panel,
            text="🧠 Learn from All Feedback",
            command=self.learn_from_feedback,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled"
        )
        self.learn_btn.grid(row=7, column=0, sticky="ew", padx=15, pady=(0, 15))

    def setup_tab_knowledge(self):
        """Knowledge Base: Browse stored knowledge"""
        tab = self.tab_knowledge
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        # Header
        ctk.CTkLabel(
            tab,
            text="🧠 Knowledge Base Browser",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            tab,
            text="View stored knowledge chunks, insights, and patterns",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Stats display
        stats_frame = ctk.CTkFrame(tab)
        stats_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.kb_stats = []
        stat_labels = [
            ("Total Chunks", "0"),
            ("Example Documents", "0"),
            ("Learned Insights", "0"),
            ("Municipalities", "0")
        ]

        for i, (title, value) in enumerate(stat_labels):
            card = ctk.CTkFrame(stats_frame)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(pady=(10, 0))

            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=20, weight="bold")
            )
            value_label.pack(pady=(5, 10))

            self.kb_stats.append(value_label)

        # Refresh button
        ctk.CTkButton(
            tab,
            text="🔄 Refresh Knowledge Base Stats",
            command=self.refresh_knowledge_stats,
            width=200
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 10))

        # Knowledge chunks viewer
        ctk.CTkLabel(
            tab,
            text="📚 Knowledge Chunks:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=4, column=0, sticky="w", padx=20, pady=(10, 5))

        self.kb_viewer = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=10),
            wrap="word"
        )
        self.kb_viewer.grid(row=5, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tab.grid_rowconfigure(5, weight=1)

    # ========== Event Handlers ==========

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

                # TODO: Implement actual PDF processing
                # For now, use the existing example documents
                self.demo_system.step1_extract_example_documents()

                print(f"\n✅ Knowledge base initialized successfully!")
                stats = self.demo_system.vector_store.get_stats()
                print(f"   Total chunks: {stats['total_chunks']}")
                print(f"   Example documents: {stats['by_source_type'].get('approved_doc', 0)}")

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                sys.stdout = old_stdout
                self.is_processing = False

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

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

    def add_rejection_reason(self, reason):
        """Add a template rejection reason to the text box"""
        current_text = self.rejection_text.get("1.0", "end").strip()

        # If text box is empty or has placeholder, replace it
        if not current_text or current_text == "Enter reasons for rejection (one per line)...":
            self.rejection_text.delete("1.0", "end")
            self.rejection_text.insert("1.0", reason)
        else:
            # Add to end with newline
            self.rejection_text.insert("end", "\n" + reason)

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

    def save_document_to_file(self, doc):
        """Save a generated document to file"""
        import os
        from datetime import datetime

        # Create output directory if it doesn't exist
        output_dir = Path("data/generated_docs")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename: ProjectName_DocumentType_Timestamp.txt
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_project_name = "".join(c for c in doc.project.project_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_project_name = safe_project_name.replace(' ', '_')

        filename = f"{safe_project_name}_{doc.document_type.value}_{timestamp}.txt"
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
                for doc_type_str in selected:
                    doc_type = DocumentType(doc_type_str)

                    # Get RAG context
                    rag_context = self.demo_system.vector_store.retrieve_context(
                        query=f"{doc_type_str} document for {self.current_project.municipality}",
                        top_k=5
                    )

                    # Generate document
                    print(f"  📝 Generating {doc_type_str}...")
                    doc = self.demo_system.template_engine.generate_document(
                        self.current_project,
                        doc_type,
                        rag_context
                    )
                    self.generated_documents.append(doc)
                    print(f"     ✅ Generated ({len(doc.content)} chars)")

                    # Save document to file
                    self.save_document_to_file(doc)

                print(f"\n✅ All {len(selected)} documents generated successfully!")
                print(f"\n➡️  Go to 'Review & Feedback' tab to view and provide feedback.")

                # Update feedback tab
                self.update_feedback_tab()

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                sys.stdout = old_stdout
                self.is_processing = False

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def update_feedback_tab(self):
        """Update the feedback tab with generated documents"""
        if not self.generated_documents:
            return

        # Update status label
        self.feedback_status_label.configure(
            text=f"{len(self.generated_documents)} documents generated. Select a document to review."
        )

        # Update document selector
        doc_options = [f"{doc.document_type.value} - {doc.project.project_name}" for doc in self.generated_documents]
        self.doc_selector.configure(values=doc_options, state="normal")
        self.doc_selector_var.set(doc_options[0])

        # Display first document
        self.display_selected_document(doc_options[0])

        # Enable buttons
        self.approve_btn.configure(state="normal")
        self.reject_btn.configure(state="normal")

    def display_selected_document(self, selection):
        """Display the selected document in the viewer"""
        if not self.generated_documents or not selection:
            return

        # Find the document
        idx = self.doc_selector.cget("values").index(selection)
        doc = self.generated_documents[idx]

        # Display in viewer
        self.doc_viewer.configure(state="normal")
        self.doc_viewer.delete("1.0", "end")

        header = f"""
{'='*80}
Document Type: {doc.document_type.value}
Project: {doc.project.project_name}
Municipality: {doc.project.municipality}
Fire Classification: {doc.project.fire_classification.value}
Generated: {doc.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

"""
        self.doc_viewer.insert("end", header)
        self.doc_viewer.insert("end", doc.content)
        self.doc_viewer.configure(state="disabled")

    def submit_feedback(self, approved):
        """Submit feedback for the currently selected document"""
        if not self.generated_documents:
            return

        # Get selected document
        selection = self.doc_selector_var.get()
        idx = self.doc_selector.cget("values").index(selection)
        doc = self.generated_documents[idx]

        # Get rejection reasons if applicable
        rejection_reasons = []
        if not approved:
            reasons_text = self.rejection_text.get("1.0", "end").strip()
            if not reasons_text:
                messagebox.showwarning("Missing Reasons", "Please provide rejection reasons!")
                return
            rejection_reasons = [r.strip() for r in reasons_text.split('\n') if r.strip()]

        # Create feedback
        feedback = MunicipalityFeedback(
            document_id=doc.document_id,
            municipality=doc.project.municipality,
            approved=approved,
            rejection_reasons=rejection_reasons if not approved else []
        )

        self.feedbacks_given.append(feedback)

        # Show confirmation
        status = "✅ APPROVED" if approved else "❌ REJECTED"
        messagebox.showinfo("Feedback Submitted", f"{status}\n\nFeedback recorded for {doc.document_type.value}")

        # Clear rejection text
        self.rejection_text.delete("1.0", "end")

        # Enable learn button if we have feedback
        if len(self.feedbacks_given) > 0:
            self.learn_btn.configure(state="normal")

    def learn_from_feedback(self):
        """Learn from all provided feedback"""
        if not self.feedbacks_given:
            messagebox.showwarning("No Feedback", "Please provide feedback on documents first!")
            return

        def learn():
            try:
                self.is_processing = True
                old_stdout = sys.stdout
                sys.stdout = TextRedirector(self.output_queue)

                print(f"\n🧠 Learning from {len(self.feedbacks_given)} feedback entries...\n")

                insights = self.demo_system.step4_learn_from_feedback(self.feedbacks_given)

                print(f"\n✅ Learning complete!")
                print(f"   Extracted {len(insights)} insights")

                stats = self.demo_system.vector_store.get_stats()
                print(f"   Knowledge base now has {stats['total_chunks']} chunks")

                print(f"\n➡️  Check 'Knowledge Base' tab to see learned patterns!")

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                sys.stdout = old_stdout
                self.is_processing = False

        thread = threading.Thread(target=learn, daemon=True)
        thread.start()

    def refresh_knowledge_stats(self):
        """Refresh knowledge base statistics"""
        try:
            stats = self.demo_system.vector_store.get_stats()

            # Update stats cards
            self.kb_stats[0].configure(text=str(stats['total_chunks']))
            self.kb_stats[1].configure(text=str(stats['by_source_type'].get('approved_doc', 0)))
            self.kb_stats[2].configure(text=str(stats['by_source_type'].get('insight', 0)))
            self.kb_stats[3].configure(text=str(len(stats['by_municipality'])))

            # Update viewer with chunk details
            self.kb_viewer.configure(state="normal")
            self.kb_viewer.delete("1.0", "end")

            self.kb_viewer.insert("end", f"Knowledge Base Statistics\n{'='*80}\n\n")
            self.kb_viewer.insert("end", f"Total Chunks: {stats['total_chunks']}\n\n")

            self.kb_viewer.insert("end", "By Source Type:\n")
            for source_type, count in stats['by_source_type'].items():
                self.kb_viewer.insert("end", f"  • {source_type}: {count}\n")

            self.kb_viewer.insert("end", "\nBy Municipality:\n")
            for municipality, count in stats['by_municipality'].items():
                self.kb_viewer.insert("end", f"  • {municipality}: {count}\n")

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

                if "Setup" in current_tab:
                    output_widget = self.setup_output
                elif "Generate" in current_tab:
                    output_widget = self.generate_output
                else:
                    # Default to setup output
                    output_widget = self.setup_output

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
