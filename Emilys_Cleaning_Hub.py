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
import winshell
import pythoncom
from win32com.client import Dispatch
import tkinter as tk
from tkinter import ttk, messagebox

# Constants
GITHUB_API_URL = "https://api.github.com/repos/OEM0VER/ESC/releases/latest"
CURRENT_VERSION = "v1.2"
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

def move_updated_executable(version):
    # Use the script directory for where we want to move the executable
    current_dir = get_script_directory()
    new_executable_name = f"Emilys_Cleaning_Hub_{version}.exe"  # Versioned executable name
    new_executable_path = os.path.join(current_dir, new_executable_name)

    # The folder where the update was extracted (the downloads folder)
    extracted_folder = DOWNLOAD_FOLDER  # Or wherever the extraction happens
    downloaded_executable_name = f"Emilys_Cleaning_Hub_{version}.exe"  # The correct versioned executable name
    downloaded_executable_path = os.path.join(extracted_folder, downloaded_executable_name)

    # Delete old versions
    delete_old_versions(current_dir, version)

    # Check if the downloaded executable exists and move it
    if os.path.exists(downloaded_executable_path):
        shutil.move(downloaded_executable_path, new_executable_path)
        print(f"Moved {downloaded_executable_path} to {new_executable_path}.")
        return new_executable_path  # Return the new executable path
    else:
        print(f"Downloaded executable not found at {downloaded_executable_path}, cannot move.")
        return None  # Return None if not found

def delete_old_versions(directory, current_version):
    """Delete all old .exe versions except the current version."""
    for file_name in os.listdir(directory):
        # Check if the file starts with "Emilys_Cleaning_Hub" and ends with ".exe"
        if file_name.startswith("Emilys_Cleaning_Hub") and file_name.endswith(".exe"):
            version_in_file = None

            # Handle the case with version number (e.g., "Emilys_Cleaning_Hub_v1.1.exe")
            if "_" in file_name:
                version_in_file = file_name.split("_")[-1].replace(".exe", "")
            else:
                # Handle the case without a version number (e.g., "Emilys_Cleaning_Hub.exe")
                version_in_file = "no_version"

            # Delete files that are either old versioned files or the unversioned file
            if version_in_file != current_version and version_in_file != "no_version":
                old_file_path = os.path.join(directory, file_name)
                try:
                    os.remove(old_file_path)
                    print(f"Deleted old version: {old_file_path}")
                except Exception as e:
                    print(f"Failed to delete {old_file_path}: {e}")
            elif version_in_file == "no_version":
                # Remove the unversioned file "Emilys_Cleaning_Hub.exe" if it exists
                old_file_path = os.path.join(directory, file_name)
                try:
                    os.remove(old_file_path)
                    print(f"Deleted old unversioned executable: {old_file_path}")
                except Exception as e:
                    print(f"Failed to delete {old_file_path}: {e}")

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

    # Rename and move the new executable to the app's directory
    new_executable_path = move_updated_executable(version)

    # Delete the zip file after extraction and installation
    try:
        os.remove(zip_file_path)
        print(f"Deleted update zip file: {zip_file_path}")
    except Exception as e:
        print(f"Failed to delete zip file {zip_file_path}: {e}")

    # Restart the app with the new executable path
    restart_app(new_executable_path)

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

def create_shortcut_to_desktop(target_path, shortcut_name="Emily's Super Cleans.lnk"):
    """Creates a shortcut to the new executable on the desktop."""
    desktop = winshell.desktop()  # Get the desktop path
    shortcut_path = os.path.join(desktop, shortcut_name)  # Define the full path for the shortcut
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path  # Path to the executable
    shortcut.WorkingDirectory = os.path.dirname(target_path)  # Set the working directory
    shortcut.IconLocation = target_path  # You can use the executable icon
    shortcut.save()  # Save the shortcut
    
    print(f"Shortcut created: {shortcut_path}")

def restart_app(new_executable_path):
    # Create the desktop shortcut to the new executable
    create_shortcut_to_desktop(new_executable_path)
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
    global all_buttons  # Ensure you reference the list of all buttons

    # Disable all buttons before opening the dialog
    for button in all_buttons:
        button.config(state=tk.DISABLED)

    # Create a Toplevel window for the dialog
    dialog = tk.Toplevel()
    dialog.title("Details")

    # Lock the window so it's not resizable
    dialog.resizable(False, False)

    # Tkinter variables to hold the entered values
    name_var = tk.StringVar()
    date_var = tk.StringVar()

    # Function to retrieve name and date
    def get_details():
        name = name_var.get()
        date = date_var.get()
        dialog.destroy()  # Close the dialog window
        
        # Re-enable all buttons after the dialog is closed
        for button in all_buttons:
            button.config(state=tk.NORMAL)

        return name, date

    # Create labels and entry widgets for name and date
    name_label = ttk.Label(dialog, text="Name:")
    name_label.grid(row=0, column=0, padx=10, pady=5)

    # Entry widget for entering name
    name_entry = ttk.Entry(dialog, textvariable=name_var)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    # Entry widget for date
    date_label = ttk.Label(dialog, text="Date (DD-MM-YYYY):")
    date_label.grid(row=1, column=0, padx=10, pady=5)

    date_entry = ttk.Entry(dialog, textvariable=date_var)
    date_entry.grid(row=1, column=1, padx=10, pady=5)

    # Create a button to submit details
    submit_button = ttk.Button(dialog, text="Submit", command=get_details)
    submit_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
    submit_button.configure(padding=(5, 1))  # Adjust padding for height and width

    # Focus on the name entry initially
    name_entry.focus_set()

    # Calculate the position to center the dialog above the main window
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    dialog_width = 300  # Adjust width as needed
    dialog_height = 130  # Adjust height as needed
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    # Make the dialog modal (prevents interaction with other windows)
    dialog.grab_set()

    # Wait for the dialog to be closed
    dialog.wait_window()

    # This part is not necessary because the buttons are already re-enabled in `get_details`.
    # Just in case we need to re-enable buttons here too
    for button in all_buttons:
        button.config(state=tk.NORMAL)

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
            messagebox.showinfo("Success", "Customer details added successfully.")
            add_window.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    add_window = tk.Toplevel()
    add_window.title("Add Customer")

    # Labels and entry fields using ttk
    name_label = ttk.Label(add_window, text="Name:")
    name_label.grid(row=0, column=0, padx=10, pady=5)
    name_entry = ttk.Entry(add_window, textvariable=name_var)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    address_label = ttk.Label(add_window, text="Address:")
    address_label.grid(row=1, column=0, padx=10, pady=5)
    address_entry = ttk.Entry(add_window, textvariable=address_var)
    address_entry.grid(row=1, column=1, padx=10, pady=5)

    email_label = ttk.Label(add_window, text="Email:")
    email_label.grid(row=2, column=0, padx=10, pady=5)
    email_entry = ttk.Entry(add_window, textvariable=email_var)
    email_entry.grid(row=2, column=1, padx=10, pady=5)

    payment_frequency_label = ttk.Label(add_window, text="Payment Frequency:")
    payment_frequency_label.grid(row=3, column=0, padx=10, pady=5)
    payment_frequency_entry = ttk.Entry(add_window, textvariable=payment_frequency_var)
    payment_frequency_entry.grid(row=3, column=1, padx=10, pady=5)

    # Add button using ttk
    add_button = ttk.Button(add_window, text="Add", command=add_customer)
    add_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # Set focus to name entry
    name_entry.focus_set()

    # Center the window on the screen
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

def load_image_from_url(url, size):
    img_data = fetch_image_with_retry(url)
    img = Image.open(BytesIO(img_data))
    img = img.resize(size, Image.LANCZOS)  # Resize the image
    return ImageTk.PhotoImage(img)

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

#def crop_circle(img, output_size):
    ## Resize the image to the desired output size
    #img = img.resize(output_size, Image.LANCZOS)

    ## Create a new image with a white background
    #result = Image.new("RGBA", img.size, (255, 255, 255, 255))

    ## Create a mask for the circular crop
    #mask = Image.new("L", img.size, 0)
    #draw = ImageDraw.Draw(mask)
    
    ## Draw a filled ellipse on the mask
    #draw.ellipse((0, 0) + img.size, fill=255)

    ## Paste the image onto the result using the mask
    #result.paste(img, (0, 0), mask)

    ## Convert result to an RGB image to avoid alpha channel issues
    #result = result.convert("RGB")

    #return result

def open_url(event):
    webbrowser.open("https://www.facebook.com/people/Emilys-super-cleans/61555658297341/")

def load_image_and_bind(root):
    try:
        image_url = "https://static.wixstatic.com/media/4db758_9c87d89ee5e94ef5b25fe6569fbd0589~mv2.jpg/v1/fit/w_720,h_720,q_90/4db758_9c87d89ee5e94ef5b25fe6569fbd0589~mv2.webp"
        img_data = fetch_image_with_retry(image_url)
        img = Image.open(BytesIO(img_data))
        
        output_size = (100, 100)  # Desired output size (width, height)
        
        # Resize the image to the desired output size
        img = img.resize(output_size, Image.LANCZOS)

        # Convert the image to PhotoImage for Tkinter
        tk_image = ImageTk.PhotoImage(img)
        
        # Create a label to display the image
        img_label = tk.Label(root, image=tk_image, cursor="hand2")
        img_label.pack(pady=10)  # Pack the label with some padding
        img_label.bind("<Button-1>", open_url)  # Bind the click event to open the URL
        
        return tk_image, img_label
    except Exception as e:
        print("Error loading image:", e)
        return None, None

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
all_buttons = []  # Global list to keep track of buttons to enable/disable

def display_customer_info():
    global customer_details_window, customer_details_window_open, all_buttons
    
    # Check if the customer details window is already open
    if customer_details_window_open:
        tk.messagebox.showinfo("Info", "Customer details window is already open.")
        return

    # Set the flag to indicate that the window is open
    customer_details_window_open = True

    # Disable all buttons before opening the customer details window
    for button in all_buttons:
        button.config(state=tk.DISABLED)

    customer_info = get_customer_info()
    customer_details_window = tk.Toplevel()
    customer_details_window.title("Customer Details")

    def on_window_close():
        # Unset the flag when the window is closed
        global customer_details_window_open
        customer_details_window_open = False
        customer_details_window.destroy()

        # Re-enable all buttons after the dialog is closed
        for button in all_buttons:
            button.config(state=tk.NORMAL)

    customer_details_window.protocol("WM_DELETE_WINDOW", on_window_close)  # Handle window close event

    # Create buttons using ttk
    btn_add_customer = ttk.Button(customer_details_window, text="Add Customer", command=add_customer_dialog)
    btn_add_customer.pack(pady=10, padx=10)  # Adding padding for aesthetics
    btn_add_customer.configure(padding=(5, 1))  # Adjust padding for height and width

    btn_refresh = ttk.Button(customer_details_window, text="Refresh", command=lambda: reload_customer_info(text_widget))
    btn_refresh.pack(pady=10, padx=10)  # Adding padding for aesthetics
    btn_refresh.configure(padding=(5, 1))  # Adjust padding for height and width

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

    # Lock the window so it's not resizable
    previous_invoices_window.resizable(False, False)

    # Calculate the position of the window
    app_x = root.winfo_x()  # Get the x-coordinate of the main application window
    app_y = root.winfo_y()  # Get the y-coordinate of the main application window
    app_width = root.winfo_width()  # Get the width of the main application window

    window_width = 410  # Set the width of the window
    window_height = 435  # Set the height of the window

    # Calculate the position of the window to be slightly to the right of the main application window
    x = app_x + app_width + 50  # Adjust 50 for the desired offset
    y = app_y + (root.winfo_height() - window_height) // 2  # Center vertically

    previous_invoices_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Create a frame to hold the text widget and scrollbar
    frame = ttk.Frame(previous_invoices_window)
    frame.pack(fill=tk.BOTH, expand=True)

    # Create a text widget to display invoices with scrollbars
    text_widget = tk.Text(previous_invoices_window, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True)

    scrollbar_y = tk.Scrollbar(previous_invoices_window, orient=tk.VERTICAL, command=text_widget.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget.config(yscrollcommand=scrollbar_y.set)

    # Reload and display previous invoices
    reload_previous_invoices(text_widget)

    # Add a "Refresh" button using ttk
    refresh_button = ttk.Button(previous_invoices_window, text="Refresh", command=lambda: reload_previous_invoices(text_widget))
    refresh_button.pack(pady=10)  # Add padding for better spacing

def display_help():
    help_text = """
    Emily's Super Cleans App Help

    This application allows you to create invoices and manage customer details.

    Usage:
    1. Click on "Manage Customer Details" to view and add customer information.
    2. Click on "Create Invoice No." to generate a new invoice number.
    3. Click on "Open Invoice Template Folder" to open the folder containing invoice templates.
    4. Click on "GMail" to open the business email in your browser.
    5. Click on "GDocs" to open Google Docs in your browser, for creating invoices.

    File:
    1. View Previous Invoices: Click to view the history of all previous invoices.
    2. Remove Invoice: Click to delete an existing invoice from the system.
    3. Remove Customer Details: Click to remove customer details from the database.
    4. Import/Replace data.ini: Click to import or replace the data.ini file with another file.
    5. Import/Replace Data2.ini: Click to import or replace the Data2.ini file with another file.
    6. Exit: Click to safely close and exit the application.

    Key Bindings:
    - Ctrl+F: Search for a customer (available in the customer details window).

    """
    help_window = tk.Toplevel()
    help_window.title("Help")

    # Set the background color of the help window to white
    help_window.configure(bg="white")
    
    # Lock the window so it's not resizable
    help_window.resizable(False, False)

    # Create a label with a white background and black text
    help_label = tk.Label(help_window, text=help_text, justify=tk.LEFT, bg="white", fg="black", wraplength=500)  # Added wraplength for better text display
    help_label.pack(padx=10, pady=10)

    # Calculate the position of the help window
    main_window_x = root.winfo_x()
    main_window_y = root.winfo_y()
    main_window_width = root.winfo_width()
    main_window_height = root.winfo_height()

    help_window_width = 520
    help_window_height = 350

    help_window_x = main_window_x - help_window_width - 20  # Adjust 20 for some spacing
    help_window_y = main_window_y + (main_window_height - help_window_height) // 2

    help_window.geometry(f"{help_window_width}x{help_window_height}+{help_window_x}+{help_window_y}")

    help_window.focus_set()
    help_window.grab_set()  # Make the help window modal
    help_window.lift()  # Bring the help window to the top
    help_window.attributes("-topmost", True)  # Ensure help window stays on top of the main window

######

# Define the function to remove an invoice
def remove_invoice():
    # Create a Toplevel window for the remove invoice dialog
    remove_dialog = tk.Toplevel()
    remove_dialog.title("Remove Invoice")

    # Lock the window so it's not resizable
    remove_dialog.resizable(False, False)

    # Create a frame to hold the Listbox and the scrollbar
    frame = ttk.Frame(remove_dialog)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Create a listbox to display the invoices using ttk
    invoice_listbox = tk.Listbox(frame, width=50, height=10)  # You can adjust the height as needed
    invoice_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a vertical scrollbar for the listbox using ttk
    scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=invoice_listbox.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

    invoice_listbox.config(yscrollcommand=scrollbar_y.set)

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
    
                # Remove the invoice section from the config
                config.remove_section(f'Invoice{invoice_number}')

                # Check if any invoices remain and update LastInvoice accordingly
                invoice_numbers = []
                for section in config.sections():
                    if 'invoicenumber' in config[section]:
                        invoice_numbers.append(int(config[section]['invoicenumber']))

                if invoice_numbers:
                    # Set LastInvoice to the maximum invoicenumber remaining
                    config['LastInvoice']['number'] = str(max(invoice_numbers))
                else:
                    # If no invoices left, reset LastInvoice to 0
                    config['LastInvoice']['number'] = '0'

                # Write the updated config back to the file
                with open('data.ini', 'w') as configfile:
                    config.write(configfile)

                # Remove the selected invoice from the listbox
                invoice_listbox.delete(selected_index)

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    # Button to remove selected invoice using ttk
    remove_button = ttk.Button(remove_dialog, text="Remove Selected Invoice", command=remove_selected_invoice)
    remove_button.pack(pady=5)

    # Button to close the remove invoice dialog using ttk
    close_button = ttk.Button(remove_dialog, text="Close", command=remove_dialog.destroy)
    close_button.pack(pady=5)

    # Calculate the position to center the dialog underneath the main window
    app_x = root.winfo_x()  # Get the x-coordinate of the main application window
    app_y = root.winfo_y()  # Get the y-coordinate of the main application window
    app_width = root.winfo_width()  # Get the width of the main application window
    app_height = root.winfo_height()  # Get the height of the main application window

    dialog_width = 340  # Adjust width as needed
    dialog_height = 260  # Adjust height as needed
    x = app_x + (app_width - dialog_width) // 2
    y = app_y + app_height + 60  # Place the dialog 50 pixels below the main window

    remove_dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    # Make the dialog modal
    remove_dialog.grab_set()

    # Wait for the dialog to be closed
    remove_dialog.wait_window()

#########

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

        # Lock the window so it's not resizable
        remove_window.resizable(False, False)
        
        # Calculate the position of the new window
        root_x = root.winfo_rootx()
        root_y = root.winfo_rooty()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        remove_window_width = 195  # Adjust according to your needs
        remove_window_height = 225  # Adjust according to your needs
        x = root_x + root_width // 2 - remove_window_width // 2
        y = root_y + root_height + 50  # Place the new window 50 pixels below the main window

        # Set the position of the new window
        remove_window.geometry(f"{remove_window_width}x{remove_window_height}+{x}+{y}")

        # Keep the new window on top of other windows
        remove_window.attributes('-topmost', True)

        # Create a frame to hold the Listbox and the scrollbar
        frame = tk.Frame(remove_window)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create a Listbox to display the customer names
        listbox = tk.Listbox(frame)
        for name in customer_names:
            listbox.insert(tk.END, name)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a vertical scrollbar for the Listbox
        scrollbar_y = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        listbox.config(yscrollcommand=scrollbar_y.set)

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
        remove_button = ttk.Button(remove_window, text="Remove Selected Customer", command=remove_selected_customer)
        remove_button.pack(pady=5)  # Pack the button below the listbox
        remove_button.configure(padding=(1, 1))
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

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.tooltip_delay = 500  # Delay in milliseconds
        self.tooltip_id = None  # To hold the ID for the tooltip after call
        
        # Bind mouse events to show and hide the tooltip
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event=None):
        self.tooltip_id = self.widget.after(self.tooltip_delay, self.show_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window is not None:
            return  # Tooltip is already shown
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")  # Position tooltip
        label = tk.Label(self.tooltip_window, text=self.text, background="white", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_id is not None:
            self.widget.after_cancel(self.tooltip_id)  # Cancel the scheduled tooltip
            self.tooltip_id = None
        if self.tooltip_window is not None:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# Function to set the directory for data files
def set_data_directory():
    # Open a directory dialog
    selected_directory = filedialog.askdirectory(title="Select Directory for data.ini and Data2.ini files")
    
    if selected_directory:  # If a directory is selected
        # Save the selected path to data_files_folder_path.txt
        with open("data_files_folder_path.txt", "w") as f:
            f.write(selected_directory)
        messagebox.showinfo("Success", f"Directory set to:\n{selected_directory}")

# Function to get the directory from the text file
def get_data_directory():
    try:
        with open("data_files_folder_path.txt", "r") as f:
            return f.read().strip()  # Read and return the path
    except FileNotFoundError:
        return None  # Return None if the file doesn't exist

# Existing function to replace data.ini
def replace_data_ini():
    # Get the directory for data files
    data_directory = get_data_directory()
    
    if data_directory is None:
        messagebox.showwarning("Warning", "No directory set for data files. Please set the directory first.")
        return

    # Define the path for the existing data.ini
    existing_file = os.path.join(data_directory, 'data.ini')

    # Open a file dialog for the user to select their own data.ini file
    new_file_path = filedialog.askopenfilename(
        title="Select your data.ini file",
        filetypes=(("INI files", "*.ini"), ("All files", "*.*"))
    )
    
    if new_file_path:  # If the user selects a file
        # Check if the selected file has the same name as data.ini
        if os.path.basename(new_file_path) == "data.ini":
            try:
                # Replace the existing data.ini with the new file
                shutil.copyfile(new_file_path, existing_file)
                messagebox.showinfo("Success", "data.ini has been replaced successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to replace data.ini: {str(e)}")
        else:
            messagebox.showwarning("Warning", "You can only replace 'data.ini' with a file named 'data.ini'.")
    else:
        messagebox.showwarning("Warning", "No file selected.")

# Existing function to replace Data2.ini
def replace_data2_ini():
    # Get the directory for data files
    data_directory = get_data_directory()

    if data_directory is None:
        messagebox.showwarning("Warning", "No directory set for data files. Please set the directory first.")
        return

    # Define the path for the existing Data2.ini
    existing_file = os.path.join(data_directory, 'Data2.ini')

    # Open a file dialog for the user to select their own Data2.ini file
    new_file_path = filedialog.askopenfilename(
        title="Select your Data2.ini file",
        filetypes=(("INI files", "*.ini"), ("All files", "*.*"))
    )
    
    if new_file_path:  # If the user selects a file
        # Check if the selected file has the same name as Data2.ini
        if os.path.basename(new_file_path) == "Data2.ini":
            try:
                # Replace the existing Data2.ini with the new file
                shutil.copyfile(new_file_path, existing_file)
                messagebox.showinfo("Success", "Data2.ini has been replaced successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to replace Data2.ini: {str(e)}")
        else:
            messagebox.showwarning("Warning", "You can only replace 'Data2.ini' with a file named 'Data2.ini'.")
    else:
        messagebox.showwarning("Warning", "No file selected.")

def on_closing():
    # Delete app_icon.ico file if it exists
    if os.path.exists("app_icon.ico"):
        os.remove("app_icon.ico")

    # Get the script directory (executable folder) dynamically
    executable_folder = get_script_directory()

    # Get the current version from the app
    current_version = CURRENT_VERSION

    # Delete old versions of the executable (including versions with and without numbers)
    delete_old_versions(executable_folder, current_version)

    # Close the app
    root.destroy()

# Now, create the root window and other GUI elements
root = tk.Tk()
root.title("Emily's Super Cleans App")
root.resizable(False, False)

# Set the background color of the main window to white
root.configure(bg='white')

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
file_menu.add_command(label="Import/Replace data.ini", command=replace_data_ini)
file_menu.add_command(label="Import/Replace Data2.ini", command=replace_data2_ini)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_closing)

# Add the "Help" menu to the menu bar
help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Add options to the "Help" menu
help_menu.add_command(label="Help Contents", command=display_help)
help_menu.add_separator()
help_menu.add_command(label="About", command=lambda: tk.messagebox.showinfo("About", "Emily's Super Cleans App v1.2"))

load_config()

window_width = 320
window_height = 390

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

# Load the Gdocs image from the URL
image_url = "https://static.wixstatic.com/media/4db758_07abf706a4eb4fa492e4567a20fba20d~mv2.png/v1/fit/w_720,h_720,q_90/4db758_07abf706a4eb4fa492e4567a20fba20d~mv2.webp"  # Replace with your image URL
desired_size = (50, 50)  # Set your desired size here
google_docs_image = load_image_from_url(image_url, desired_size)

# Load the Gdocs image from the URL
image_url = "https://static.wixstatic.com/media/4db758_12e100f80b6343aba735c4bb60647a7e~mv2.png/v1/fit/w_720,h_720,q_90/4db758_12e100f80b6343aba735c4bb60647a7e~mv2.webp"  # Replace with your image URL
desired_size = (50, 50)  # Set your desired size here
google_mail_image = load_image_from_url(image_url, desired_size)

# Create a style for the ttk buttons
style = ttk.Style()
style.configure("TButton",
                padding=(10, 1),  # Adjust horizontal and vertical padding
                relief="flat",  # Flat relief for modern look
                #background="#FFFFF",  # Button color
                foreground="black",  # Text color
                font=("Helvetica", 11))  # Adjust font size

# Create ttk buttons using the defined style
# Frame for buttons that need to be side by side
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

# Existing buttons
btn_manage_customer_details = ttk.Button(root, text="Manage Customer Details", command=display_customer_info, style="TButton")
btn_manage_customer_details.pack(pady=10)
btn_manage_customer_details.configure(cursor="hand2")  # Set the cursor to hand2

btn_create_invoice = ttk.Button(root, text="Create Invoice No.", command=lambda: create_invoice(img_label), style="TButton")
btn_create_invoice.pack(pady=10)
btn_create_invoice.configure(cursor="hand2")

btn_open_template_folder = ttk.Button(root, text="Open Invoice Template Folder", command=open_invoice_template_folder, style="TButton")
btn_open_template_folder.pack(pady=10)
btn_open_template_folder.configure(cursor="hand2")

# Create a custom style for the button frame
style = ttk.Style()
style.configure("TFrame", background="white")  # Set the background of the frame style

# Frame for buttons that need to be side by side at the bottom
button_frame = ttk.Frame(root, style="TFrame")  # Apply the style here
button_frame.pack(pady=10)

# Function to change the cursor to hand2 when hovering
def on_enter(event):
    event.widget.config(cursor="hand2")  # Change cursor to hand2

def on_leave(event):
    event.widget.config(cursor="")  # Reset to default cursor

# Create the business email button
btn_open_business_email = ttk.Button(button_frame, image=google_mail_image, command=open_business_email, style="TButton")
btn_open_business_email.pack(side=tk.LEFT, padx=5)  # Add padding on the sides

# Access the underlying tk widget to set cursor behavior
btn_open_business_email.bind("<Enter>", lambda e: btn_open_business_email.state(['!disabled']) or btn_open_business_email.config(cursor="hand2"))
btn_open_business_email.bind("<Leave>", lambda e: btn_open_business_email.config(cursor=""))

# Create tooltip for the email button
#email_tooltip = ToolTip(btn_open_business_email, "Open Business Email")

# Create the Google Docs button
btn_open_google_docs = ttk.Button(button_frame, image=google_docs_image, command=open_google_docs, style="TButton")
btn_open_google_docs.pack(side=tk.LEFT, padx=5)  # Add padding on the sides

# Access the underlying tk widget to set cursor behavior
btn_open_google_docs.bind("<Enter>", lambda e: btn_open_google_docs.state(['!disabled']) or btn_open_google_docs.config(cursor="hand2"))
btn_open_google_docs.bind("<Leave>", lambda e: btn_open_google_docs.config(cursor=""))

# Create tooltip for the Google Docs button
#docs_tooltip = ToolTip(btn_open_google_docs, "Open Google Docs")

# List of all buttons for easier management
all_buttons = [
    btn_manage_customer_details,
    btn_create_invoice,
    btn_open_template_folder,
    btn_open_business_email,
    btn_open_google_docs
]

# Add a watermark label at the bottom of the root window
watermark_label = tk.Label(root, text="Designed & Created by: M0VER", bg="#ffffff", fg="gray")
watermark_label.pack(side=tk.BOTTOM, pady=5)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
