from tkinter import ttk, filedialog, messagebox
import tkinter as tk
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
import os

import stripe
stripe.api_key = os.environ['STRIPE_API_KEY']


class App(tk.Tk):
    """
    A simple Tkinter application with input fields for Name (string),
    Year (integer), and a PDF file selector.
    """

    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("Add Stripe Payment Link")
        self.geometry("500x200")
        self.resizable(False, False)

        # --- Style Configuration ---
        style = ttk.Style(self)
        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("TEntry", padding=5, font=('Helvetica', 10))
        style.configure("TButton", padding=5, font=('Helvetica', 10, 'bold'))

        # --- Tkinter Variables ---
        # These variables are used to get/set widget values
        self.name_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.filepath_var = tk.StringVar()
        self.filepath_display_var = tk.StringVar(value="No file selected.")

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Widget Creation and Layout ---
        self.create_widgets(main_frame)

    def create_widgets(self, container):
        """Creates and arranges all the widgets in the window."""
        container.columnconfigure(
            1, weight=1)  # Allow the entry widgets to expand

        # --- Name Input ---
        ttk.Label(container, text="Name:").grid(row=0, column=0, sticky=tk.W)
        name_entry = ttk.Entry(container, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

        # --- Year Input ---
        ttk.Label(container, text="Year:").grid(row=1, column=0, sticky=tk.W)
        year_entry = ttk.Entry(container, textvariable=self.year_var)
        year_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)

        # --- File Selector ---
        ttk.Label(container, text="PDF File:").grid(
            row=2, column=0, sticky=tk.W, pady=(10, 0))

        # Label to display the selected file path
        filepath_label = ttk.Label(
            container, textvariable=self.filepath_display_var, foreground="gray", wraplength=300)
        filepath_label.grid(row=2, column=1, sticky="ew", pady=(10, 0))

        # Button to open the file dialog
        browse_button = ttk.Button(
            container, text="Browse...", command=self.select_pdf_file)
        browse_button.grid(row=2, column=2, sticky=tk.E, pady=(10, 0))

        # --- Submit Button ---
        submit_button = ttk.Button(
            container, text="Generate", command=self.submit_data)
        submit_button.grid(row=3, column=1, pady=(20, 0))

    def select_pdf_file(self):
        """Opens a file dialog to select a PDF file and updates the file path variable."""
        filetypes = (
            ('PDF files', '*.pdf'),
            ('All files', '*.*')
        )
        filepath = filedialog.askopenfilename(
            title='Select a PDF file',
            initialdir='/',  # Start directory
            filetypes=filetypes)

        if filepath:
            self.filepath_var.set(filepath)
            self.filepath_display_var.set(os.path.basename(filepath))

        self.focus_force()

    def submit_data(self):
        """
        Retrieves data from the input fields, validates it, and prints it.
        Shows a message box with the collected data.
        """
        name = self.name_var.get()
        year_str = self.year_var.get()
        filepath = self.filepath_var.get()

        # --- Validation ---
        if not name:
            messagebox.showerror("Error", "Name field cannot be empty.")
            return

        try:
            # Attempt to convert year to an integer
            year = int(year_str)
        except ValueError:
            messagebox.showerror("Error", "Year must be a valid integer.")
            return

        if filepath == "No file selected.":
            messagebox.showerror("Error", "Please select a PDF file.")
            return

        # --- Display Data ---
        # Print to console
        print("--- Submitted Data ---")
        print(f"Name: {name} (Type: {type(name).__name__})")
        print(f"Year: {year} (Type: {type(year).__name__})")
        print(f"File Path: {filepath} (Type: {type(filepath).__name__})")
        print("----------------------")
        print('\n')

        # Generate PDF.
        product = stripe.Product.create(name=f'{name} - {year}')

        price = stripe.Price.create(
            currency='usd',
            unit_amount=2000_00,
            product=product.id
        )

        payment_link = stripe.PaymentLink.create(
            line_items=[{'price': price.id, 'quantity': 1}],
        )

        class PDF(FPDF):

            def button(self, x, y, w, h, text, link, text_color=(0, 0, 0), fill_color=(255, 255, 255)):
                x -= w / 2
                y -= h / 2
                self.set_fill_color(*fill_color)
                self.set_draw_color(*fill_color)
                self.rect(x, y, w, h, style='DF', round_corners=True)

                self.set_xy(x, y)
                self.set_text_color(*text_color)
                self.cell(w, h, text=text, align='C', link=link)

            def footer(self):
                self.button(pdf.w / 2, pdf.h - 25, 50, 10, 'Make Payment Here', payment_link.url,
                            fill_color=(0, 255, 0))

        # Create an instance of the custom PDF class
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Times', '', 12)

        template_name = 'template.pdf'
        pdf.output(template_name)

        original_pdf = PdfReader(filepath)
        template_pdf = PdfReader(template_name)

        writer = PdfWriter()

        # 3. Overlay the footer on each page
        for original_page in original_pdf.pages:
            footer_page = template_pdf.pages[0]

            # Overlay the footer page onto the original page
            original_page.merge_page(footer_page)
            writer.add_page(original_page)

        # 4. Save the modified PDF
        invoice_name = os.path.basename(filepath)
        name, ext = os.path.splitext(invoice_name)
        output_name = f'{name}_stripe{ext}'
        with open(output_name, "wb") as output_pdf:
            writer.write(output_pdf)

        # Show generated PDF.
        os.startfile(output_name)

        # Clean up temporary files.
        if os.path.exists(template_name):
            os.remove(template_name)


if __name__ == "__main__":
    app = App()
    app.mainloop()
