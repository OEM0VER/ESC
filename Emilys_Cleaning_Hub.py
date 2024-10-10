import tkinter as tk
import urllib.request
from tkinter import ttk
from tkinter import messagebox
from configparser import ConfigParser
from PIL import Image, ImageTk, ImageDraw
import requests
from io import BytesIO
import webbrowser
import os
import uuid
import configparser
from tkinter import filedialog
import shutil
import sys
import subprocess
import zipfile

# Constants
GITHUB_API_URL = "https://api.github.com/repos/OEM0VER/ESC/releases/latest"
CURRENT_VERSION = "v1.1"
DOWNLOAD_FOLDER = "updates"  # Folder to store downloaded files

def get_script_directory():
    if getattr(sys, 'frozen', False):
        # The script is bundled into an executable
        return os.path.abspath(os.path.dirname(sys.executable))
    else:
        # The script is run directly
        return os.path.abspath(os.path.dirname(__file__))

def show_info_message(message):
    """Display a message box with the given message."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo("Update Info", message)  # Show the message box
    root.destroy()  # Close the root window

def check_for_updates():
    # Get the latest release from GitHub
    response = requests.get(GITHUB_API_URL)
    
    if response.status_code == 200:
        latest_release = response.json()
        latest_version = latest_release["tag_name"]

        # Compare versions
        if latest_version > CURRENT_VERSION:
            print(f"New version available: {latest_version}. Downloading update...")
            download_url = latest_release["assets"][0]["browser_download_url"]
            show_info_message(f"Downloading update: {latest_version}...")  # Show info message
            download_and_install_update(download_url, latest_version)
        else:
            print("You are using the latest version.")
    else:
        print("Failed to check for updates.")

def download_and_install_update(download_url, version):
    # Create the download folder if it doesn't exist
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    zip_file_path = os.path.join(DOWNLOAD_FOLDER, f"app_update_{version}.zip")

    # Download the update
    response = requests.get(download_url)
    with open(zip_file_path, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded {version} update.")

    # Extract the update
    extract_update(zip_file_path)

    # Delete the ZIP file after extraction
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
        print(f"Deleted the update ZIP file: {zip_file_path}")

    # Rename and move the new executable to the app's directory
    new_executable_path = move_updated_executable(version)

    # Restart the app with the new executable path
    restart_app(new_executable_path)

def move_updated_executable(version):
    script_directory = get_script_directory()  # Use the new function to get the script's directory
    new_executable_name = f"Emilys_Cleaning_Hub_{version}.exe"
    new_executable_path = os.path.join(script_directory, new_executable_name)

    # Move the new executable from the updates folder to the script's directory
    downloaded_executable_path = os.path.join(DOWNLOAD_FOLDER, "Emilys_Cleaning_Hub.exe")  # Adjust this if necessary

    # Check if the downloaded executable exists and move it
    if os.path.exists(downloaded_executable_path):
        shutil.move(downloaded_executable_path, new_executable_path)
        print(f"Moved {downloaded_executable_path} to {new_executable_path}.")
        return new_executable_path  # Return the new executable path
    else:
        print("Downloaded executable not found, cannot move.")
        return None  # Return None if not found

def extract_update(zip_file_path):
    # Unzip the update
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(DOWNLOAD_FOLDER)  # Extract to the download folder
    print("Update installed successfully.")
    return DOWNLOAD_FOLDER  # Return the folder where the update was extracted

def rename_executable(version, extracted_folder):
    """Rename the new executable to include the version number and move it to the executable location."""
    old_executable_name = "Emilys_Cleaning_Hub.exe"
    new_executable_name = f"Emilys_Cleaning_Hub_{version}.exe"
    
    # Construct the full paths
    old_executable_path = os.path.join(extracted_folder, old_executable_name)
    new_executable_path = os.path.join(extracted_folder, new_executable_name)

    # Rename the executable
    os.rename(old_executable_path, new_executable_path)
    print(f"Renamed executable to: {new_executable_name}")

    # Move the new executable to the script/executable location
    target_path = os.path.join(EXECUTABLE_FOLDER, new_executable_name)

    # Check if the new executable exists before moving
    if os.path.exists(new_executable_path):
        shutil.move(new_executable_path, target_path)
        print(f"Moved executable to: {target_path}")
        return target_path  # Return the new path for restarting
    else:
        print("Error: Renamed executable not found after renaming!")
        raise FileNotFoundError("Renamed executable not found after renaming.")

def restart_app(new_executable_path):
    # Restart the app using the new executable path
    subprocess.Popen([new_executable_path])  # Use the new executable path
    sys.exit()  # Exit the current process

def create_initial_ini():
    config = configparser.ConfigParser()

    # Check if the 'data.ini' file exists
    try:
        with open('data.ini', 'r') as configfile:
            config.read('data.ini')
    except FileNotFoundError:
        pass  # File does not exist, it will be created
    
    # Check if the 'LastInvoice' section exists
    if 'LastInvoice' not in config:
        config['LastInvoice'] = {'Number': '0'}

        with open('data.ini', 'w') as configfile:
            config.write(configfile)

# Call the function to create or update 'data.ini' file on startup
create_initial_ini()

def create_and_save_invoice(name, date):
    config = configparser.ConfigParser()
    config.read('data.ini')

    last_invoice_number = config.getint('LastInvoice', 'Number', fallback=0)
    next_invoice_number = last_invoice_number + 1

    # Format the invoice number with leading zeros
    formatted_invoice_number = f"{next_invoice_number:07d}"

    config['LastInvoice']['Number'] = str(next_invoice_number)

    invoice_section_name = f'Invoice{formatted_invoice_number}'
    config[invoice_section_name] = {
        'Name': name,
        'Date': date,
        'InvoiceNumber': str(formatted_invoice_number)
    }

    with open('data.ini', 'w') as configfile:
        config.write(configfile)

def create_invoice(img_label):
    btn_create_invoice.config(state=tk.DISABLED)
    btn_manage_customer_details.config(state=tk.DISABLED)
    btn_open_business_email.config(state=tk.DISABLED)
    img_label.unbind("<Button-1>")
    
    customer_names = fetch_customer_names()  # Fetch customer names
    
    name, date = get_name_and_date(customer_names)  # Pass customer names
    
    btn_create_invoice.config(state=tk.NORMAL)
    btn_manage_customer_details.config(state=tk.NORMAL)
    btn_open_business_email.config(state=tk.NORMAL)
    img_label.bind("<Button-1>", open_url)
    
    if name and date:
        create_and_save_invoice(name, date)

# Check if data.ini exists and create it if not
create_initial_ini()

def load_config():
    config = {}  # Initialize an empty dictionary
    if not os.path.exists("Data2.ini"):
        with open("Data2.ini", "w") as file:
            file.write("")
    else:
        with open("Data2.ini", "r") as file:
            config_data = file.read()
            # Parse config data if needed
            # Example: config = parse_config_data(config_data)
    return config

# Call load_config to initialize config
config = load_config()

def save_config(name, date, invoice_number):
    # Check if all fields are provided
    if name and date and invoice_number:
        config_data = f"[Invoice]\n"
        config_data += f"Name = {name}\n"
        config_data += f"Date = {date}\n"
        config_data += f"InvoiceNumber = {invoice_number}\n"

        with open("Data.ini", "a") as file:  # Open the file in append mode
            file.write(config_data + "\n")  # Add a new line after each configuration entry

def fetch_customer_names():
    customer_names = []
    if os.path.exists("Data2.ini"):
        with open("Data2.ini", "r") as file:
            data = file.readlines()
            for line in data:
                if line.startswith("Name ="):
                    customer_name = line.split("=")[1].strip()
                    customer_names.append(customer_name)
                    print("Customer name:", customer_name)  # Add this line for debugging
    return customer_names

def get_name_and_date(customer_names):
    # Create a Toplevel window for the dialog
    dialog = tk.Toplevel()
    dialog.title("Details")

    # Tkinter variables to hold the entered values
    name_var = tk.StringVar()
    date_var = tk.StringVar()

    # Function to retrieve name and date
    def get_details():
        name = name_var.get()
        date = date_var.get()
        dialog.destroy()  # Close the dialog window
        return name, date

    # Create labels and entry widgets for name and date
    name_label = tk.Label(dialog, text="Name:")
    name_label.grid(row=0, column=0, padx=10, pady=5)

    # Entry widget for entering name
    name_entry = tk.Entry(dialog, textvariable=name_var)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    # Entry widget for date
    date_label = tk.Label(dialog, text="Date (DD-MM-YYYY):")
    date_label.grid(row=1, column=0, padx=10, pady=5)
    date_entry = tk.Entry(dialog, textvariable=date_var)
    date_entry.grid(row=1, column=1, padx=10, pady=5)

    # Create a button to submit details
    submit_button = tk.Button(dialog, text="Submit", command=get_details)
    submit_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    # Focus on the name entry initially
    name_entry.focus_set()

    # Calculate the position to center the dialog above the main window
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    dialog_width = 300  # Adjust width as needed
    dialog_height = 150  # Adjust height as needed
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    # Make the dialog modal (prevents interaction with other windows)
    dialog.grab_set()

    # Wait for the dialog to be closed
    dialog.wait_window()

    # Retrieve the name and date
    name, date = name_var.get(), date_var.get()

    # Return empty strings if name and date are not provided
    if not name.strip() and not date.strip():
        return "", ""

    return name, date

def add_customer_dialog():
    name_var = tk.StringVar()
    address_var = tk.StringVar()
    email_var = tk.StringVar()
    payment_frequency_var = tk.StringVar()

    def add_customer():
        name = name_var.get()
        address = address_var.get()
        email = email_var.get()
        payment_frequency = payment_frequency_var.get()

        # Check if all fields are provided
        if name and address and email and payment_frequency:
            save_customer_details(name, address, email, payment_frequency)
            tk.messagebox.showinfo("Success", "Customer details added successfully.")
            add_window.destroy()
        else:
            tk.messagebox.showerror("Error", "Please fill in all fields.")

    add_window = tk.Toplevel()
    add_window.title("Add Customer")

    name_label = tk.Label(add_window, text="Name:")
    name_label.grid(row=0, column=0, padx=10, pady=5)
    name_entry = tk.Entry(add_window, textvariable=name_var)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    address_label = tk.Label(add_window, text="Address:")
    address_label.grid(row=1, column=0, padx=10, pady=5)
    address_entry = tk.Entry(add_window, textvariable=address_var)
    address_entry.grid(row=1, column=1, padx=10, pady=5)

    email_label = tk.Label(add_window, text="Email:")
    email_label.grid(row=2, column=0, padx=10, pady=5)
    email_entry = tk.Entry(add_window, textvariable=email_var)
    email_entry.grid(row=2, column=1, padx=10, pady=5)

    payment_frequency_label = tk.Label(add_window, text="Payment Frequency:")
    payment_frequency_label.grid(row=3, column=0, padx=10, pady=5)
    payment_frequency_entry = tk.Entry(add_window, textvariable=payment_frequency_var)
    payment_frequency_entry.grid(row=3, column=1, padx=10, pady=5)

    add_button = tk.Button(add_window, text="Add", command=add_customer)
    add_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    name_entry.focus_set()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    dialog_width = 300
    dialog_height = 200
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    add_window.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def on_window_close():
        add_window.destroy()

    add_window.protocol("WM_DELETE_WINDOW", on_window_close)  # Handle window close event

    name_label = tk.Label(add_window, text="Name:")
    name_label.grid(row=0, column=0, padx=10, pady=5)
    name_entry = tk.Entry(add_window, textvariable=name_var)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    address_label = tk.Label(add_window, text="Address:")
    address_label.grid(row=1, column=0, padx=10, pady=5)
    address_entry = tk.Entry(add_window, textvariable=address_var)
    address_entry.grid(row=1, column=1, padx=10, pady=5)

    email_label = tk.Label(add_window, text="Email:")
    email_label.grid(row=2, column=0, padx=10, pady=5)
    email_entry = tk.Entry(add_window, textvariable=email_var)
    email_entry.grid(row=2, column=1, padx=10, pady=5)

    payment_frequency_label = tk.Label(add_window, text="Payment Frequency:")
    payment_frequency_label.grid(row=3, column=0, padx=10, pady=5)
    payment_frequency_entry = tk.Entry(add_window, textvariable=payment_frequency_var)
    payment_frequency_entry.grid(row=3, column=1, padx=10, pady=5)

    add_button = tk.Button(add_window, text="Add", command=add_customer)
    add_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    name_entry.focus_set()

    screen_width = add_window.winfo_screenwidth()
    screen_height = add_window.winfo_screenheight()
    dialog_width = 300
    dialog_height = 200
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    add_window.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    # Ensure the dialog window is destroyed when closed
    add_window.grab_set()
    add_window.focus_set()
    add_window.wait_window(add_window)

def save_customer_details(name, address, email, payment_frequency):
    customer_id = str(uuid.uuid4())

    customer_data = f"[Customer_{customer_id}]\n"
    customer_data += f"Name = {name}\n"
    customer_data += f"Address = {address}\n"
    customer_data += f"Email = {email}\n"
    customer_data += f"PaymentFrequency = {payment_frequency}\n"

    with open("Data2.ini", "a") as file:
        file.write(customer_data)

def open_business_email():
    webbrowser.open("https://mail.google.com/mail/u/?authuser=emilyssupercleans@gmail.com")

def open_google_docs():
    webbrowser.open("https://docs.google.com/document/u/0/")

MAX_RETRIES = 5
BASE_DELAY = 3  # Initial delay in seconds

def fetch_image_with_retry(image_url):
    retries = 0
    delay = BASE_DELAY
    while retries < MAX_RETRIES:
        try:
            response = urllib.request.urlopen(image_url)
            img_data = response.read()
            return img_data
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Too Many Requests
                print("Too many requests. Retrying in {} seconds...".format(delay))
                time.sleep(delay)
                delay *= 2  # Exponential backoff
                retries += 1
            else:
                raise  # Re-raise other HTTP errors

    raise Exception("Max retries exceeded. Unable to fetch image.")

def crop_circle(img, output_size):
    img = img.resize(output_size, Image.LANCZOS)
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + img.size, fill=255)
    result = Image.new("RGBA", img.size)
    result.paste(img, (0, 0), mask)
    return result

def open_url(event):
    webbrowser.open("https://www.facebook.com/people/Emilys-super-cleans/61555658297341/")

def load_image_and_bind(root):
    try:
        image_url = "https://static.wixstatic.com/media/4db758_9c87d89ee5e94ef5b25fe6569fbd0589~mv2.jpg/v1/fit/w_720,h_720,q_90/4db758_9c87d89ee5e94ef5b25fe6569fbd0589~mv2.webp"
        img_data = fetch_image_with_retry(image_url)
        img = Image.open(BytesIO(img_data))
        output_size = (100, 100)
        cropped_img = crop_circle(img, output_size)
        tk_image = ImageTk.PhotoImage(cropped_img)
        img_label = tk.Label(root, image=tk_image, cursor="hand2")
        img_label.pack(pady=10)
        img_label.bind("<Button-1>", open_url)
        return tk_image, img_label
    except Exception as e:
        print("Error loading image:", e)
        return None, None

def load_config():
    if not os.path.exists("Data2.ini"):
        with open("Data2.ini", "w") as file:
            file.write("")

def get_last_invoice_number_from_data_ini():
    last_invoice_number = 1000000  # Default starting invoice number
    if os.path.exists("Data.ini"):
        with open("Data.ini", "r") as file:
            lines = file.readlines()
            for line in reversed(lines):  # Iterate over lines in reverse order
                if line.startswith("InvoiceNumber"):
                    last_invoice_number = int(line.split("=")[-1].strip())
                    break
    return last_invoice_number

def generate_invoice_number(name, date):
    global config  # Ensure config is accessible as a global variable

    if name.strip() and date.strip():  # Check if both name and date are not empty strings
        # Load the last used invoice number from data.ini
        last_invoice_number = get_last_invoice_number_from_data_ini()

        # Generate the next invoice number
        next_invoice_number = last_invoice_number + 1

        # Check if the next invoice number exceeds the upper limit
        if next_invoice_number > 2000000000:
            print("Invoice number limit reached. Cannot generate more invoices.")
            return

        # Save the new invoice number to the config
        config["Invoices"] = {"LastInvoice": str(next_invoice_number)}

        # Save the updated config to the file
        save_config(name, date, next_invoice_number)

        print(f"Invoice number generated: {next_invoice_number}")

# Function to generate sequential invoice number
def generate_sequential_invoice_number():
    global config
    # Check if 'Invoices' section exists
    if "Invoices" not in config or "LastInvoice" not in config["Invoices"] or not config["Invoices"]["LastInvoice"]:
        # Starting invoice number
        start_invoice_number = "1000000000"
        config["Invoices"] = {"LastInvoice": start_invoice_number}
        return start_invoice_number

    last_invoice = int(config["Invoices"]["LastInvoice"])
    next_invoice = last_invoice + 1

    config["Invoices"]["LastInvoice"] = str(next_invoice)
    return str(next_invoice)

def save_config(name, date, invoice_number):
    config_data = f"[Invoice]\n"
    config_data += f"Name = {name}\n"
    config_data += f"Date = {date}\n"
    config_data += f"InvoiceNumber = {invoice_number}\n"

    with open("Data.ini", "a") as file:  # Open the file in append mode
        file.write(config_data + "\n")  # Add a new line after each configuration entry

def search_customer(text_widget, event):
    search_window = tk.Toplevel()
    search_window.title("Search Customer")

    search_var = tk.StringVar()

    def search():
        query = search_var.get().lower()
        if query:
            text_widget.tag_remove("found", "1.0", tk.END)
            search_pos = "1.0"
            while True:
                search_pos = text_widget.search(query, search_pos, stopindex=tk.END, nocase=1)
                if not search_pos:
                    break
                end_pos = f"{search_pos}+{len(query)}c"
                text_widget.tag_add("found", search_pos, end_pos)
                search_pos = end_pos
            text_widget.tag_config("found", background="blue")  # Change foreground color to blue
        else:
            # Notify the user that the search query is empty
            tk.messagebox.showinfo("Empty Search", "Please enter a search query.")

    def reset_highlight():
        text_widget.tag_remove("found", "1.0", tk.END)

    search_label = tk.Label(search_window, text="Search:")
    search_label.grid(row=0, column=0, padx=10, pady=5)
    search_entry = tk.Entry(search_window, textvariable=search_var)
    search_entry.grid(row=0, column=1, padx=10, pady=5)
    search_entry.focus_set()

    search_button = tk.Button(search_window, text="Search", command=search)
    search_button.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5))

    reset_button = tk.Button(search_window, text="Reset Highlight", command=reset_highlight)
    reset_button.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 5))

    close_button = tk.Button(search_window, text="Close", command=search_window.destroy)
    close_button.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10))

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    dialog_width = 220
    dialog_height = 160
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    search_window.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    search_window.grab_set()

def display_search_results(results):
    # Clear the text widget
    text_widget.config(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)

    for info in results:
        text_widget.insert(tk.END, "Customer Details:\n")
        for key, value in info.items():
            if key != "Customer ID":  # Exclude 'Customer ID' from being displayed
                text_widget.insert(tk.END, f"{key}: {value}\n")
        text_widget.insert(tk.END, "\n")
    text_widget.config(state=tk.DISABLED)

def get_customer_info():
    if not os.path.exists("Data2.ini"):
        return []

    customer_info = []
    with open("Data2.ini", "r") as file:
        data = file.readlines()
        customer_details = {}
        for line in data:
            if line.startswith("[Customer_"):
                if customer_details:
                    # Exclude Customer ID from the displayed details
                    del customer_details["Customer ID"]
                    customer_info.append(customer_details)
                    customer_details = {}
                customer_details["Customer ID"] = line.split("_")[1].strip()
            elif "=" in line:  # Check if line contains '='
                key, value = line.split("=")
                customer_details[key.strip()] = value.strip()
        if customer_details:
            # Exclude Customer ID from the displayed details
            del customer_details["Customer ID"]
            customer_info.append(customer_details)
    return customer_info

customer_details_window_open = False  # Global variable to track the status of the customer details window

def display_customer_info():
    global customer_details_window, customer_details_window_open
    
    # Check if the customer details window is already open
    if customer_details_window_open:
        tk.messagebox.showinfo("Info", "Customer details window is already open.")
        return
    
    # Set the flag to indicate that the window is open
    customer_details_window_open = True

    customer_info = get_customer_info()
    customer_details_window = tk.Toplevel()
    customer_details_window.title("Customer Details")

    def on_window_close():
        # Unset the flag when the window is closed
        global customer_details_window_open
        customer_details_window_open = False
        customer_details_window.destroy()

    customer_details_window.protocol("WM_DELETE_WINDOW", on_window_close)  # Handle window close event

    btn_add_customer = tk.Button(customer_details_window, text="Add Customer", command=add_customer_dialog, cursor="hand2")
    btn_add_customer.pack(pady=10)

    btn_refresh = tk.Button(customer_details_window, text="Refresh", command=lambda: reload_customer_info(text_widget), cursor="hand2")
    btn_refresh.pack(pady=10)

    app_x = root.winfo_x()
    app_y = root.winfo_y()
    app_width = root.winfo_width()
    app_height = root.winfo_height()

    window_width = 700
    window_height = 300
    gap = 50

    x = app_x + (app_width - window_width) // 2
    y = app_y - window_height - gap

    customer_details_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Create a frame to hold the text widget and scrollbar
    frame = tk.Frame(customer_details_window)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Create a text widget to display customer details
    text_widget = tk.Text(frame, height=20, width=60)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a scrollbar
    scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the text widget to use the scrollbar
    text_widget.config(yscrollcommand=scrollbar.set)

    reload_customer_info(text_widget)

    # Bind Ctrl+F to trigger the search function only within this window
    customer_details_window.bind("<Control-f>", lambda event: search_customer(text_widget, event))

    customer_details_window.grab_set()  # Make the customer details window modal
    customer_details_window.lift()  # Bring the customer details window to the top
    customer_details_window.attributes("-topmost", True)  # Ensure customer details window stays on top of the main window

def reload_customer_info(text_widget):
    customer_info = get_customer_info()

    # Clear the text widget
    text_widget.config(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)

    for info in customer_info:
        text_widget.insert(tk.END, "Customer Details:\n")
        for key, value in info.items():
            if key != "Customer ID":  # Exclude 'Customer ID' from being displayed
                text_widget.insert(tk.END, f"{key}: {value}\n")
        text_widget.insert(tk.END, "\n")
    text_widget.config(state=tk.DISABLED)

def set_customer_details_window_open(open_status):
    global customer_details_window_open
    customer_details_window_open = open_status

def on_closing():
    generate_invoice_number("", "")
    root.destroy()

# Define the function to reload and display previous invoices
def reload_previous_invoices(text_widget):
    text_widget.config(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)

    invoices = []  # List to store invoice blocks

    with open("data.ini", "r") as file:
        invoice_data = {}
        for line in file:
            line = line.strip()
            print("Processing line:", line)  # Debugging output
            if line.startswith("[Invoice"):
                if invoice_data:
                    invoices.append(invoice_data)  # Add the current invoice data to the list
                invoice_data = {}
            elif line:
                try:
                    key, value = line.split("=", 1)
                    invoice_data[key.strip()] = value.strip()
                except ValueError:
                    print("Skipping line due to incorrect format:", line)  # Debugging output

        if invoice_data:
            invoices.append(invoice_data)  # Add the last invoice to the list

    # Reverse the order of invoices to show the most recent first
    for invoice_data in reversed(invoices):
        text_widget.insert(tk.END, "\n")
        for key, value in invoice_data.items():
            text_widget.insert(tk.END, f"{key}: {value}\n")
        text_widget.insert(tk.END, "\n" + "=" * 50 + "\n\n")

    text_widget.config(state=tk.DISABLED)  # Disable editing of the text widget

# Define the global file_menu variable
file_menu = None

# Define the function to view previous invoices
def view_previous_invoices():
    if not os.path.exists("Data.ini"):
        messagebox.showinfo("Previous Invoices", "No previous invoices found.")
        return

    # Create a new window to display previous invoices
    previous_invoices_window = tk.Toplevel()
    previous_invoices_window.title("Previous Invoices")

    # Set the window to stay on top
    previous_invoices_window.attributes("-topmost", True)

    # Calculate the position of the window
    app_x = root.winfo_x()  # Get the x-coordinate of the main application window
    app_y = root.winfo_y()  # Get the y-coordinate of the main application window
    app_width = root.winfo_width()  # Get the width of the main application window

    window_width = 410  # Set the width of the window
    window_height = 420  # Set the height of the window

    # Calculate the position of the window to be slightly to the right of the main application window
    x = app_x + app_width + 50  # Adjust 50 for the desired offset
    y = app_y + (root.winfo_height() - window_height) // 2  # Center vertically

    previous_invoices_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Create a text widget to display invoices with scrollbars
    text_widget = tk.Text(previous_invoices_window, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True)

    scrollbar_y = tk.Scrollbar(previous_invoices_window, orient=tk.VERTICAL, command=text_widget.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget.config(yscrollcommand=scrollbar_y.set)

    # Reload and display previous invoices
    reload_previous_invoices(text_widget)

    # Add a "Refresh" button
    refresh_button = tk.Button(previous_invoices_window, text="Refresh", command=lambda: reload_previous_invoices(text_widget))
    refresh_button.pack()

# Define the function to exit the application
def exit_application():
    # Save any necessary data or perform cleanup before exiting
    generate_invoice_number("", "")  # Save the current invoice state
    root.destroy()  # Close the application window

def display_help():
    help_text = """
    Emily's Super Cleans App Help

    This application allows you to create invoices and manage customer details.

    Usage:
    1. Click on "Create Invoice No." to generate a new invoice number.
    2. Click on "Manage Customer Details" to view and add customer information.
    3. Click on "Open Business Email" to open the business email in a web browser.
    3. Click on "Open Invoice Template Folder" to open the folder containing invoice templates.

    Key Bindings:
    - Ctrl+F: Search for a customer (available in the customer details window)

    """
    help_window = tk.Toplevel()
    help_window.title("Help")

    help_label = tk.Label(help_window, text=help_text, justify=tk.LEFT)
    help_label.pack(padx=10, pady=10)

    # Calculate the position of the help window
    main_window_x = root.winfo_x()
    main_window_y = root.winfo_y()
    main_window_width = root.winfo_width()
    main_window_height = root.winfo_height()

    help_window_width = 520
    help_window_height = 210

    help_window_x = main_window_x - help_window_width - 20  # Adjust 20 for some spacing
    help_window_y = main_window_y + (main_window_height - help_window_height) // 2

    help_window.geometry(f"{help_window_width}x{help_window_height}+{help_window_x}+{help_window_y}")

    help_window.focus_set()
    help_window.grab_set()  # Make the help window modal
    help_window.lift()  # Bring the help window to the top
    help_window.attributes("-topmost", True)  # Ensure help window stays on top of the main window

    # Function definitions

def remove_invoice():
    # Create a Toplevel window for the remove invoice dialog
    remove_dialog = tk.Toplevel()
    remove_dialog.title("Remove Invoice")

    # Create a listbox to display the invoices
    invoice_listbox = tk.Listbox(remove_dialog, width=50)
    invoice_listbox.pack(padx=10, pady=10)

    # Function to populate the listbox with invoice details from data.ini
    def populate_invoice_list():
        # Clear existing items in the listbox
        invoice_listbox.delete(0, tk.END)
        # Read invoice details from data.ini
        config = configparser.ConfigParser()
        config.read('data.ini')
        # Populate listbox with invoice numbers and customer names
        for section in config.sections():
            if 'invoicenumber' in config[section]:
                invoice_number = config[section]['invoicenumber']
                customer_name = config[section]['name']
                invoice_listbox.insert(tk.END, f"Invoice Number: {invoice_number}, Name: {customer_name}")

    # Call the function to initially populate the listbox
    populate_invoice_list()

    # Create a function to remove the selected invoice
    def remove_selected_invoice():
        # Get the selected index
        selected_indices = invoice_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]  # Take the first index if multiple are selected
            try:
                # Read invoice details from data.ini
                config = configparser.ConfigParser()
                config.read('data.ini')
                # Remove the corresponding invoice from data.ini
                section_to_remove = invoice_listbox.get(selected_index)
                invoice_number = section_to_remove.split("Invoice Number: ")[1].split(",")[0].strip()
                config.remove_section(f'Invoice{invoice_number}')
                with open('data.ini', 'w') as configfile:
                    config.write(configfile)
                # Remove the selected invoice from the listbox
                invoice_listbox.delete(selected_index)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    # Button to remove selected invoice
    remove_button = tk.Button(remove_dialog, text="Remove Selected Invoice", command=remove_selected_invoice)
    remove_button.pack(pady=5)

    # Button to close the remove invoice dialog
    close_button = tk.Button(remove_dialog, text="Close", command=remove_dialog.destroy)
    close_button.pack(pady=5)

    # Calculate the position to center the dialog underneath the main window
    app_x = root.winfo_x()  # Get the x-coordinate of the main application window
    app_y = root.winfo_y()  # Get the y-coordinate of the main application window
    app_width = root.winfo_width()  # Get the width of the main application window
    app_height = root.winfo_height()  # Get the height of the main application window

    dialog_width = 300  # Adjust width as needed
    dialog_height = 260  # Adjust height as needed
    x = app_x + (app_width - dialog_width) // 2
    y = app_y + app_height + 60  # Place the dialog 50 pixels below the main window

    remove_dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    # Make the dialog modal
    remove_dialog.grab_set()

    # Wait for the dialog to be closed
    remove_dialog.wait_window()

def remove_customer_details():
    # Function to fetch customer names
    def fetch_customer_names():
        config = ConfigParser()
        config.read("Data2.ini")
        return [config[section]['Name'] for section in config.sections()]

    customer_names = fetch_customer_names()  # Fetch customer names
    if customer_names:
        # Create a new window for selecting the customer to remove
        remove_window = tk.Toplevel(root)
        remove_window.title("Remove Customer")
        
        # Calculate the position of the new window
        root_x = root.winfo_rootx()
        root_y = root.winfo_rooty()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        remove_window_width = 165  # Adjust according to your needs
        remove_window_height = 195  # Adjust according to your needs
        x = root_x + root_width // 2 - remove_window_width // 2
        y = root_y + root_height + 50  # Place the new window 50 pixels below the main window

        # Set the position of the new window
        remove_window.geometry(f"{remove_window_width}x{remove_window_height}+{x}+{y}")

        # Keep the new window on top of other windows
        remove_window.attributes('-topmost', True)

        # Create a Listbox to display the customer names
        listbox = tk.Listbox(remove_window)
        for name in customer_names:
            listbox.insert(tk.END, name)
        listbox.pack()

        # Function to handle the removal of the selected customer
        def remove_selected_customer():
            selected_index = listbox.curselection()
            if selected_index:
                selected_customer = listbox.get(selected_index)
                config = ConfigParser()
                config.read("Data2.ini")

                # Find the section corresponding to the selected customer name
                for section in config.sections():
                    if config[section]['Name'] == selected_customer:
                        config.remove_section(section)
                        with open("Data2.ini", "w") as configfile:
                            config.write(configfile)
                        tk.messagebox.showinfo("Customer Details Removed", f"Customer {selected_customer} details removed successfully.")
                        remove_window.destroy()
                        return
                tk.messagebox.showinfo("Error", f"Failed to find customer {selected_customer} details.")
            else:
                tk.messagebox.showinfo("No Selection", "Please select a customer to remove.")

        # Button to remove the selected customer
        remove_button = tk.Button(remove_window, text="Remove Selected Customer", command=remove_selected_customer)
        remove_button.pack()  # Pack the button below the listbox
    else:
        tk.messagebox.showinfo("No Customers", "No customer details found.")

def open_invoice_template_folder():
    # Check if the invoice template folder path is saved in a configuration file
    if os.path.exists("invoice_template_folder_path.txt"):
        with open("invoice_template_folder_path.txt", "r") as file:
            invoice_template_folder = file.read().strip()
    else:
        # Prompt the user to input the folder path
        invoice_template_folder = tk.filedialog.askdirectory(title="Select Invoice Template Folder")
        if invoice_template_folder:
            # Save the folder path to a configuration file for future use
            with open("invoice_template_folder_path.txt", "w") as file:
                file.write(invoice_template_folder)

    # Check if the folder path exists
    if os.path.exists(invoice_template_folder):
        # Open the folder in the default file explorer
        os.startfile(invoice_template_folder)
    else:
        tk.messagebox.showerror("Error", "Invoice template folder not found!")

def on_closing():
    # Delete app_icon.ico file if it exists
    if os.path.exists("app_icon.ico"):
        os.remove("app_icon.ico")
    root.destroy()

# Now, create the root window and other GUI elements
root = tk.Tk()
root.title("Emily's Super Cleans App")

# Call this function at the start of your app
check_for_updates()

# Add the "File" menu to the menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)

# Add the "View Previous Invoices" option first
file_menu.add_command(label="View Previous Invoices", command=view_previous_invoices)
file_menu.add_separator()
file_menu.add_command(label="Remove Invoice", command=remove_invoice)
file_menu.add_command(label="Remove Customer Details", command=remove_customer_details)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=exit_application)

# Add the "Help" menu to the menu bar
help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Add options to the "Help" menu
help_menu.add_command(label="Help Contents", command=display_help)
help_menu.add_separator()
help_menu.add_command(label="About", command=lambda: tk.messagebox.showinfo("About", "Emily's Super Cleans App v1.1"))

load_config()

window_width = 320
window_height = 380

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)

root.geometry(f"{window_width}x{window_height}+{x}+{y}")

tk_image, img_label = load_image_and_bind(root)

icon_url = "https://static.wixstatic.com/media/4db758_138505bb308b49aa9df89a7fc3bd0488~mv2.png/v1/fit/w_680,h_776,q_90/4db758_138505bb308b49aa9df89a7fc3bd0488~mv2.webp"
icon_response = requests.get(icon_url)
icon_img = Image.open(BytesIO(icon_response.content))
icon_img.save("app_icon.ico")
root.iconbitmap("app_icon.ico")

btn_manage_customer_details = tk.Button(root, text="Manage Customer Details", command=display_customer_info, cursor="hand2")
btn_manage_customer_details.pack(pady=10)

btn_create_invoice = tk.Button(root, text="Create Invoice No.", command=lambda: create_invoice(img_label), cursor="hand2")
btn_create_invoice.pack(pady=10)

btn_open_business_email = tk.Button(root, text="Open Business Email", command=open_business_email, cursor="hand2")
btn_open_business_email.pack(pady=10)

btn_open_business_email = tk.Button(root, text="Open Google Docs", command=open_google_docs, cursor="hand2")
btn_open_business_email.pack(pady=10)

btn_open_template_folder = tk.Button(root, text="Open Invoice Template Folder", command=open_invoice_template_folder, cursor="hand2")
btn_open_template_folder.pack(pady=10)

# Add a watermark label at the bottom of the root window
watermark_label = tk.Label(root, text="Designed & Created by: M0VER", bg="#f0f0f0", fg="gray")
watermark_label.pack(side=tk.BOTTOM, pady=5)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
