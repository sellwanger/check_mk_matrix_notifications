#!/usr/bin/env python3
import json
import os
import random
import string
import sys
import requests

# === [Konfiguration & Debug] ===

DEBUG = True  # Auf False setzen für produktiv

def log(msg):
    if DEBUG:
        print("[DEBUG]", msg)

# === [Hilfsfunktion für Umgebungsvariablen mit Fallback] ===

def get_env(key, fallback=None, required=False):
    val = os.environ.get(key, fallback)
    if required and not val:
        print(f"❌ Fehlende Umgebungsvariable: {key}")
        sys.exit(1)
    log(f"{key} = {repr(val)}")
    return val

# === [Parameter aus Umgebung lesen] ===

MATRIXHOST = get_env("NOTIFY_PARAMETER_1", required=True)
MATRIXTOKEN = get_env("NOTIFY_PARAMETER_2", required=True)
MATRIXROOM = get_env("NOTIFY_PARAMETER_3", fallback="!DEIN_DEFAULT_RAUM:matrix.org", required=True)

# === [CheckMK Benachrichtigungsdaten] ===

data = {
    "TS": get_env("NOTIFY_SHORTDATETIME", fallback="unknown"),

    "HOST": get_env("NOTIFY_HOSTNAME", fallback="unknown"),
    "HOSTADDR": get_env("NOTIFY_HOSTADDRESS", fallback="unknown"),
    "HOSTSTATE": get_env("NOTIFY_HOSTSTATE", fallback=""),
    "HOSTSTATEPREVIOUS": get_env("NOTIFY_LASTHOSTSTATE", fallback=""),
    "HOSTSTATECOUNT": get_env("NOTIFY_HOSTNOTIFICATIONNUMBER", fallback="0"),
    "HOSTOUTPUT": get_env("NOTIFY_HOSTOUTPUT", fallback=""),

    "SERVICE": get_env("NOTIFY_SERVICEDESC", fallback="$SERVICEDESC$"),
    "SERVICESTATE": get_env("NOTIFY_SERVICESTATE", fallback=""),
    "SERVICESTATEPREVIOUS": get_env("NOTIFY_LASTSERVICESTATE", fallback=""),
    "SERVICESTATECOUNT": get_env("NOTIFY_SERVICENOTIFICATIONNUMBER", fallback="0"),
    "SERVICEOUTPUT": get_env("NOTIFY_SERVICEOUTPUT", fallback="")
}

# === [Nachricht erzeugen] ===

servicemessage = '''Service <b>{SERVICE}</b> at <b>{HOST}</b> ({HOSTADDR}) | TS: {TS} | STATE: <b>{SERVICESTATE}</b>
<br>{SERVICEOUTPUT}<br>'''

hostmessage = '''Host <b>{HOST}</b> ({HOSTADDR}) | TS: {TS} | STATE: <b>{HOSTSTATE}</b>
<br>{HOSTOUTPUT}<br>'''

message = ""

if (data["HOSTSTATE"] != data["HOSTSTATEPREVIOUS"] or data["HOSTSTATECOUNT"] != "0"):
    message = hostmessage.format(**data)

if (data["SERVICESTATE"] != data["SERVICESTATEPREVIOUS"] or data["SERVICESTATECOUNT"] != "0") and (data["SERVICE"] != "$SERVICEDESC$"):
    message = servicemessage.format(**data)

if not message:
    log("Keine Nachricht zu senden (Zustand unverändert)")
    sys.exit(0)

# === [Matrix senden] ===

matrixDataDict = {
    "msgtype": "m.text",
    "body": message,
    "format": "org.matrix.custom.html",
    "formatted_body": message,
}

matrixData = json.dumps(matrixDataDict).encode("utf-8")

txnId = ''.join(random.SystemRandom().choice(
    string.ascii_uppercase + string.digits) for _ in range(16))

matrixHeaders = {
    "Authorization": f"Bearer {MATRIXTOKEN}",
    "Content-Type": "application/json",
    "Content-Length": str(len(matrixData))
}

matrixURL = f"{MATRIXHOST}/_matrix/client/v3/rooms/{MATRIXROOM}/send/m.room.message/{txnId}"
log(f"→ POST to {matrixURL}")

try:
    response = requests.put(url=matrixURL, data=matrixData, headers=matrixHeaders)
    response.raise_for_status()
    print("✅ Matrix-Nachricht erfolgreich gesendet.")
except requests.exceptions.HTTPError as e:
    print(f"❌ Fehler beim Senden: {e}")
    print(f"Response: {response.text}")
    sys.exit(2)
except Exception as e:
    print(f"❌ Unerwarteter Fehler: {e}")
    sys.exit(3)
