import os
import requests
import time
import json
import fitz  # PyMuPDF

# Charger les configurations depuis le fichier config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

DEEPL_API_URL = config['deepl']['api_url']
DEEPL_API_KEY = config['deepl']['api_key']
TARGET_LANG = config['translation']['target_lang']
INPUT_FOLDER = config['folders']['input_folder']
OUTPUT_FOLDER = config['folders']['output_folder']

def translate_pdf(file_path, target_lang=TARGET_LANG):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'auth_key': DEEPL_API_KEY,
            'target_lang': target_lang,
        }
        response = requests.post(DEEPL_API_URL, files=files, data=data)
        
        if response.status_code != 200:
            print(f"Erreur lors de la traduction du fichier {file_path}: {response.text}")
            return None
        
        document_id = response.json()["document_id"]
        document_key = response.json()["document_key"]

        return document_id, document_key

def check_translation_status(document_id, document_key):
    status_url = f"{DEEPL_API_URL}/{document_id}"
    data = {
        'auth_key': DEEPL_API_KEY,
        'document_key': document_key,
    }
    
    response = requests.post(status_url, data=data)
    if response.status_code != 200:
        print(f"Erreur lors de la vérification du statut de traduction: {response.text}")
        return None
    
    return response.json()

def download_translated_pdf(document_id, document_key, output_path):
    download_url = f"{DEEPL_API_URL}/{document_id}/result"
    data = {
        'auth_key': DEEPL_API_KEY,
        'document_key': document_key,
    }
    
    response = requests.post(download_url, data=data)
    if response.status_code != 200:
        print(f"Erreur lors du téléchargement du fichier traduit: {response.text}")
        return False
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    return True

def process_pdfs(input_folder=INPUT_FOLDER, output_folder=OUTPUT_FOLDER, target_lang=TARGET_LANG):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith('.pdf'):
            input_path = os.path.join(input_folder, file_name)
            print(f"Traitement du fichier : {input_path}")
            
            document_id, document_key = translate_pdf(input_path, target_lang)
            if not document_id or not document_key:
                continue
            
            status = check_translation_status(document_id, document_key)
            while status['status'] != 'done':
                if status['status'] == 'error':
                    print(f"Erreur lors de la traduction du fichier {file_name}")
                    break
                print(f"Statut de traduction : {status['status']} pour le fichier {file_name}")
                time.sleep(5)  # Attendre 5 secondes avant de vérifier à nouveau le statut
                status = check_translation_status(document_id, document_key)
            
            output_path = os.path.join(output_folder, f"translated_{file_name}")
            if download_translated_pdf(document_id, document_key, output_path):
                print(f"Fichier traduit enregistré : {output_path}")
            else:
                print(f"Échec de l'enregistrement du fichier traduit : {output_path}")

# Utilisation du script
process_pdfs()
