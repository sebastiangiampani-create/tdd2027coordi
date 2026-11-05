"""Prueba aislada de WhatsApp Cloud API; no lee ni envia datos nominales."""
import json
import os
import re
import urllib.error
import urllib.request

def main():
    token = os.environ.get("TDD_WA_ACCESS_TOKEN", "").strip()
    phone_id = os.environ.get("TDD_WA_PHONE_NUMBER_ID", "").strip()
    recipient = re.sub(r"[^0-9]", "", os.environ.get("TDD_WA_TEST_RECIPIENT", ""))
    if not token or not phone_id or not recipient:
        raise RuntimeError("Configura TDD_WA_ACCESS_TOKEN, TDD_WA_PHONE_NUMBER_ID y TDD_WA_TEST_RECIPIENT como GitHub Actions secrets.")
    if not phone_id.isdigit() or not 8 <= len(recipient) <= 15:
        raise RuntimeError("Identificador del emisor o numero destinatario invalido.")
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }
    url = f"https://graph.facebook.com/v25.0/{phone_id}/messages"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Meta can return sensitive diagnostic context; avoid printing full body.
        raise RuntimeError(f"Meta rechazo el envio de prueba (HTTP {error.code}). Verifica token, numero de prueba y destinatario autorizado.") from None
    if not result.get("messages"):
        raise RuntimeError("Meta no confirmo la aceptacion del mensaje de prueba.")
    print("Meta acepto el mensaje de prueba hello_world. Comproba su recepcion en WhatsApp.")

if __name__ == "__main__":
    main()
