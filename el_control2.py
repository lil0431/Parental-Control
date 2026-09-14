import subprocess
import signal
import sys
import threading
import tkinter as tk
import os
from tkinter import messagebox, simpledialog, PhotoImage
from mitmproxy import http
from bs4 import BeautifulSoup
from datetime import datetime, time
import csv
import pyminizip
from typing import List
import logging
import json
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def start():
    # Activar el proxy antes de iniciar
    subprocess.call(['bash', 'toggle_proxy.sh'])
    # Create a thread for the GUI
    gui_thread = threading.Thread(target=mitm)
    gui_thread.daemon = True  # Allows the thread to be killed when the main program exits
    gui_thread.start()

    # Inicializar el archivo de reportes
    init_report_file()

def mitm():
    global mitmdump_pid
    logging.debug("Starting mitmdump on port 8082")
    process = subprocess.Popen(['mitmdump', '-s', 'el_control2.py', '-p', '8082'])
    mitmdump_pid = process.pid
    logging.debug(f"mitmdump process started with PID: {mitmdump_pid}")

def stop():
    global mitmdump_pid
    if mitmdump_pid:
        logging.debug(f"Terminating mitmdump process with PID: {mitmdump_pid}")
        os.kill(mitmdump_pid, signal.SIGTERM)
        mitmdump_pid = None
    subprocess.call(['bash', 'toggle_proxy.sh'])
    password_csv(report_file, report_file2, password)
    sys.exit()

def cleanup(signum, frame):
    # Desactivar el proxy
    subprocess.call(['bash', 'toggle_proxy.sh'])
    sys.exit()

# Manejar la señal de interrupción (Ctrl+C)
signal.signal(signal.SIGINT, cleanup)

# Lista de palabras clave
blocked_keywords_lock = threading.Lock()

def read_blocked_keywords():
    try:
        with open("blocked_keywords.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_blocked_keywords(keywords):
    with open("blocked_keywords.json", "w") as f:
        json.dump(keywords, f)

# Initialize the blocked keywords
blocked_keywords: List[str] = read_blocked_keywords()

# Horario permitido
allowed_start_time = time(8, 32)  # 8:30 AM
allowed_end_time = time(22, 45)  # 10:45 PM

# Archivo para guardar los reportes
report_file = "reportes_bloqueo.csv"
report_file2= "reportes_bloqueo"
password= "password123"

valid_users = [('papaguay123', "papa123"), ('mamamola321', "mama123")]

# Crear el archivo de reportes si no existe
def init_report_file():
    with open(report_file, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'url', 'motivo', 'contenido_bloqueado']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvfile.seek(0, 2)  # Comprobar si el archivo está vacío
        if csvfile.tell() == 0:
            writer.writeheader()  # Escribir la cabecera del archivo

# Función para registrar el intento bloqueado en el archivo de reportes
def log_report(url, motivo, contenido_bloqueado=""):
    with open(report_file, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'url', 'motivo', 'contenido_bloqueado']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow(
            {'timestamp': timestamp, 'url': url, 'motivo': motivo, 'contenido_bloqueado': contenido_bloqueado})

# Función para mostrar un pop-up
def show_popup(message):
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal de Tkinter
    messagebox.showwarning("Acceso Denegado", message)
    root.destroy()  # Cierra la ventana después de mostrar el mensaje

# Verificar si está dentro del horario permitido
def is_within_allowed_hours():
    current_time = datetime.now().time()  # Obtiene la hora actual (incluye horas y minutos)
    return allowed_start_time <= current_time <= allowed_end_time

def password_csv(originalFile, name, password):
    file_name = name + ".zip"
    pyminizip.compress(originalFile, None, file_name, password, 5)
    print("El fichero se ha guardado satisfactoriamente")

def add_blocked_keyword():
    global blocked_keywords
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    new_keyword = simpledialog.askstring("Añadir Palabra Bloqueada", "Introduce la nueva palabra clave para bloquear:")
    root.destroy()  # Close the window after getting the input
    if new_keyword:
        with blocked_keywords_lock:
            if new_keyword not in blocked_keywords:
                blocked_keywords.append(new_keyword)
                write_blocked_keywords(blocked_keywords)
                logging.debug(f"Keyword added: {new_keyword}")
            else:
                logging.debug(f"The keyword '{new_keyword}' is already in the list.")

def request(flow: http.HTTPFlow) -> None:
    with blocked_keywords_lock:
        current_blocked_keywords = read_blocked_keywords()

    # Check if the request is a search query (e.g., Google search)
    if "google.com/search" in flow.request.pretty_url or "bing.com/search" in flow.request.pretty_url:
        url = flow.request.pretty_url.lower()
        query = flow.request.query.get('q', '').lower()

        if not is_within_allowed_hours():
            show_popup("Acceso denegado fuera del horario permitido")
            log_report(url, "Acceso denegado fuera del horario permitido", contenido_bloqueado=query)
            flow.response = http.Response.make(302, b"", {
                "Location": "https://i.pinimg.com/originals/73/f8/fd/73f8fd1a923955e454b352abca602d2d.gif"})
            return

        if any(re.search(r'\b' + re.escape(keyword) + r'\b', query) for keyword in current_blocked_keywords):
            # Redirect to a warning page if the search query contains blocked keywords
            log_report(url, "Bloqueado por búsqueda", contenido_bloqueado=query)
            flow.response = http.Response.make(302, b"", {
                "Location": "https://i.pinimg.com/originals/73/f8/fd/73f8fd1a923955e454b352abca602d2d.gif"})
            return

def response(flow: http.HTTPFlow) -> None:
    with blocked_keywords_lock:
        current_blocked_keywords = read_blocked_keywords()

    # Filter search results for blocked keywords
    if ("google.com/search" in flow.request.pretty_url or "bing.com/search" in flow.request.pretty_url) and "text/html" in flow.response.headers.get("Content-Type", ""):
        html = flow.response.text
        soup = BeautifulSoup(html, "html.parser")

        # Remove search result entries containing blocked keywords
        for keyword in current_blocked_keywords:
            regex = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            for element in soup.find_all(text=regex.search):
                parent = element.find_parent('div')
                if parent:
                    parent.decompose()

        flow.response.text = str(soup)

    # Existing content filtering logic
    elif "text/html" in flow.response.headers.get("Content-Type", ""):
        html = flow.response.text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text().lower()

        if any(re.search(r'\b' + re.escape(keyword) + r'\b', text) for keyword in current_blocked_keywords):
            log_report(flow.request.pretty_url, "Bloqueado por contenido", contenido_bloqueado=flow.request.pretty_url)
            flow.response = http.Response.make(302, b"", {
                "Location": "https://i.pinimg.com/originals/73/f8/fd/73f8fd1a923955e454b352abca602d2d.gif"})
            return

def login():
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    new_username = simpledialog.askstring("Usuario:", "Introduzca el usuario:")
    new_password = simpledialog.askstring("Contraseña", "Introduzca la contraseña:")
    root.destroy()  # Close the window after getting the input

    logging.debug(new_username)

    if (new_username, new_password) in valid_users:
        logging.debug("LOGUEADO HERMANO")
    else:
        logging.debug("PA TU CASA CHAVAL")