#!/usr/bin/env python3

# Check_mk notifications sender to Matrix.
#
# Copyright(c) 2019, Stanislav N. aka pztrn.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files(the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import json
import os
import random
import string
import sys
import requests

# Hilfsfunktion: sichere Umgebungsvariablenabfrage
def safe_get(env, default=""):
    return os.environ.get(env, default)

# Konfig aus Umgebungsvariablen
MATRIXHOST = safe_get("NOTIFY_PARAMETER_1")  # z.B. "https://matrix.example.com"
MATRIXTOKEN = safe_get("NOTIFY_PARAMETER_2")  # Zugangstoken
MATRIXROOM = safe_get("NOTIFY_PARAMETER_3")  # Raum-ID (z.B. !abcdefg1234:example.com)


# Benachrichtigungsdaten
data = {
    "TS": safe_get("NOTIFY_SHORTDATETIME"),
    "HOST": safe_get("NOTIFY_HOSTNAME"),
    "HOSTADDR": safe_get("NOTIFY_HOSTADDRESS"),
    "HOSTSTATE": safe_get("NOTIFY_HOSTSTATE"),
    "HOSTSTATEPREVIOUS": safe_get("NOTIFY_LASTHOSTSTATE"),
    "HOSTSTATECOUNT": safe_get("NOTIFY_HOSTNOTIFICATIONNUMBER"),
    "HOSTOUTPUT": safe_get("NOTIFY_HOSTOUTPUT"),
    "SERVICE": safe_get("NOTIFY_SERVICEDESC"),
    "SERVICESTATE": safe_get("NOTIFY_SERVICESTATE"),
    "SERVICESTATEPREVIOUS": safe_get("NOTIFY_LASTSERVICESTATE"),
    "SERVICESTATECOUNT": safe_get("NOTIFY_SERVICENOTIFICATIONNUMBER"),
    "SERVICEOUTPUT": safe_get("NOTIFY_SERVICEOUTPUT"),
}

servicemessage = (
    'Service <b>{SERVICE}</b> at <b>{HOST}</b> ({HOSTADDR}) | TS: {TS} | '
    'STATE: <b>{SERVICESTATE}</b><br>{SERVICEOUTPUT}<br>'
)

hostmessage = (
    'Host <b>{HOST}</b> ({HOSTADDR}) | TS: {TS} | STATE: <b>{HOSTSTATE}</b><br>{HOSTOUTPUT}<br>'
)

# Nachricht zusammensetzen
message = ""

# Hostzustand prüfen
if data["HOSTSTATE"] != data["HOSTSTATEPREVIOUS"] or data["HOSTSTATECOUNT"] != "0":
    message = hostmessage.format(**data)

# Servicestatus prüfen
if (
    data["SERVICESTATE"] != data["SERVICESTATEPREVIOUS"]
    or data["SERVICESTATECOUNT"] != "0"
) and data["SERVICE"] not in ["", "$SERVICEDESC$"]:
    message = servicemessage.format(**data)

# Falls keine Nachricht nötig ist, Skript beenden
if not message:
    print("No message to send.")
    sys.exit(0)

# Matrix-Nachricht
matrix_data = {
    "msgtype": "m.text",
    "body": message,
    "format": "org.matrix.custom.html",
    "formatted_body": message,
}
matrix_json = json.dumps(matrix_data).encode("utf-8")

# Zufällige txn ID generieren
txn_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Headers
headers = {
    "Authorization": f"Bearer {MATRIXTOKEN}",
    "Content-Type": "application/json"
}

# Endpunkt (v3 statt r0 empfohlen)
url = f"{MATRIXHOST}/_matrix/client/v3/rooms/{MATRIXROOM}/send/m.room.message/{txn_id}"

# Matrix-Nachricht senden
try:
    response = requests.put(url, data=matrix_json, headers=headers)
    response.raise_for_status()
    print(f"Message sent successfully. Status code: {response.status_code}")
except requests.RequestException as e:
    print(f"Failed to send message: {e}")
    print(f"Response: {getattr(e.response, 'text', 'No response body')}")
    sys.exit(2)
