import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from Crypto.Cipher import AES
from werkzeug.utils import secure_filename
import random, string

app = Flask(__name__)

# Define directories for storing uploaded, encrypted, and decrypted files
UPLOAD_FOLDER = "uploads"
ENCRYPTED_FOLDER = "encrypted"
DECRYPTED_FOLDER = "decrypted"
SECRET_KEY = b"16byte_secretkey"  

# Configure Flask app to use these directories
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)

# Allowed audio file formats
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'aac', 'ogg', 'm4a', 'opus'}

# Function to pad data to be a multiple of AES block size (16 bytes)
def pad(data):
    return data + b" " * (AES.block_size - len(data) % AES.block_size)
    
# Function to check if the uploaded file is in the allowed formats)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to encrypt a file using AES encryption)
def encrypt_file(filepath, key):
    cipher = AES.new(key, AES.MODE_ECB) # Using ECB mode
    with open(filepath, "rb") as f:
        data = f.read()
    encrypted_data = cipher.encrypt(pad(data)) # Encrypt and pad the data
    
    # Save the encrypted file
    enc_filename = os.path.join(ENCRYPTED_FOLDER, os.path.basename(filepath) + ".enc")
    with open(enc_filename, "wb") as f:
        f.write(encrypted_data)
    return enc_filename

# Function to decrypt an AES encrypted file
def decrypt_file(filepath, key):
    if not filepath.endswith(".enc"):
        return None # Ensure the file has the correct .enc extension

    cipher = AES.new(key, AES.MODE_ECB)
    with open(filepath, "rb") as f:
        encrypted_data = f.read()

    decrypted_data = cipher.decrypt(encrypted_data).rstrip() # Decrypt and remove padding
    
    # Save the decrypted file (removing the .enc extension)
    dec_filename = os.path.join(DECRYPTED_FOLDER, os.path.basename(filepath).replace(".enc", ""))

    with open(dec_filename, "wb") as f:
        f.write(decrypted_data)

    return dec_filename
    
# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/next', methods=['GET', 'POST'])
def next():
    key = request.form.get('key')

    # Generate a random key if user requests or no key is provided
    if request.form.get('generate_random') == 'true' or not key:
       
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    return render_template('next.html', key=key)

# Route to download an encrypted file
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(ENCRYPTED_FOLDER, filename)

# Route to play a decrypted audio file
@app.route('/play/<filename>')
def play_file(filename):
    return send_from_directory(DECRYPTED_FOLDER, filename)

# Route to handle file uploads, encryption, and decryption
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not file:
        return "Error: No file uploaded."
    
    filename = secure_filename(file.filename) # Secure filename to prevent path traversal attacks
    file_extension = filename.rsplit('.', 1)[-1].lower()  # Extract file extension
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    action = request.form.get("action") # Determine user action: encrypt or decrypt

    if action == "encrypt":
        if file_extension not in ALLOWED_EXTENSIONS:
            return render_template("error.html", message="Unsupported file format for encryption.")

        file.save(filepath) # Save original file

        encrypted_path = encrypt_file(filepath, SECRET_KEY) # Encrypt the file
        return render_template("download.html", file_url=url_for('download_file', filename=os.path.basename(encrypted_path)))

    elif action == "decrypt":
        if not filename.endswith(".enc"):
            return render_template("error.html", message="Please upload a valid encrypted (.enc) file for decryption.")
        
        file.save(filepath) # Save uploaded encrypted file
        decrypted_path = decrypt_file(filepath, SECRET_KEY) # Decrypt the file
        return render_template("play.html", file_url=url_for('play_file', filename=os.path.basename(decrypted_path)))

    return "Invalid action"

# Run the Flask app on port 10000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
