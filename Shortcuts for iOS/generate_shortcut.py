"""
generate_shortcut.py
Generates WiFi_QR_Code.shortcut — importable into the iOS Shortcuts app.

Shortcut flow:
  1. Ask for SSID         → stored in variable "SSID"
  2. Ask for Password     → stored in variable "Password"
  3. Build WiFi string    → WIFI:T:WPA;S:<SSID>;P:<Password>;;
  4. URL-encode the string
  5. Build QR API URL     → https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=<encoded>
  6. Get Contents of URL  → downloads QR image
  7. Quick Look           → displays QR code image

Run: python generate_shortcut.py
Output: WiFi_QR_Code.shortcut  (binary plist, ready to AirDrop or share to iPhone)
"""

import plistlib
import uuid

ORC = "\ufffc"  # Object Replacement Character — iOS Shortcuts variable placeholder


def new_uuid():
    return str(uuid.uuid4()).upper()


# ── UUIDs for cross-referencing action outputs ──────────────────────────────
UUID_ASK_SSID     = new_uuid()
UUID_ASK_PASSWORD = new_uuid()
UUID_WIFI_TEXT    = new_uuid()
UUID_URL_ENCODE   = new_uuid()
UUID_QR_URL_TEXT  = new_uuid()
UUID_GET_URL      = new_uuid()


def token_var(name: str) -> dict:
    """Reference a named variable."""
    return {
        "Type": "Variable",
        "VariableName": name,
    }


def token_output(action_uuid: str, output_name: str) -> dict:
    """Reference the output of a previous action by UUID."""
    return {
        "OutputUUID": action_uuid,
        "Type": "ActionOutput",
        "OutputName": output_name,
    }


def wf_text(text: str, attachments: dict) -> dict:
    """
    Build a WFTextTokenString with variable/output tokens embedded.
    text: string with ORC placeholders (one per token)
    attachments: {"{offset, 1}": token_dict, ...}
    """
    return {
        "Value": {
            "attachmentsByRange": attachments,
            "string": text,
        },
        "WFSerializationType": "WFTextTokenString",
    }


# ── Actions ──────────────────────────────────────────────────────────────────

def ask_for_input(prompt: str, action_uuid: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "WFAskActionPrompt": prompt,
            "WFAskActionInputType": "Text",
            "UUID": action_uuid,
            "CustomOutputName": prompt.split("(")[0].strip(),
        },
    }


def set_variable(var_name: str, source_uuid: str, source_output: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": var_name,
            "WFInput": {
                "Value": token_output(source_uuid, source_output),
                "WFSerializationType": "WFTextTokenAttachment",
            },
        },
    }


def text_action(text: str, attachments: dict, action_uuid: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": wf_text(text, attachments),
            "UUID": action_uuid,
            "CustomOutputName": "Text",
        },
    }


def url_encode_action(source_uuid: str, action_uuid: str) -> dict:
    """Percent-encode the previous text action's output."""
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.urlencode",
        "WFWorkflowActionParameters": {
            "WFInput": {
                "Value": token_output(source_uuid, "Text"),
                "WFSerializationType": "WFTextTokenAttachment",
            },
            "UUID": action_uuid,
            "CustomOutputName": "URL Encoded Text",
        },
    }


def url_action(url_text: str, url_attachments: dict, action_uuid: str) -> dict:
    """Build a URL (same as Text action but typed as URL)."""
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "WFURLActionURL": wf_text(url_text, url_attachments),
            "UUID": action_uuid,
            "CustomOutputName": "URL",
        },
    }


def get_contents_of_url(url_source_uuid: str, action_uuid: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "WFURL": {
                "Value": token_output(url_source_uuid, "URL"),
                "WFSerializationType": "WFTextTokenAttachment",
            },
            "WFHTTPMethod": "GET",
            "UUID": action_uuid,
            "CustomOutputName": "Contents of URL",
        },
    }


def quick_look(source_uuid: str, source_output: str) -> dict:
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.previewdocument",
        "WFWorkflowActionParameters": {
            "WFInput": {
                "Value": token_output(source_uuid, source_output),
                "WFSerializationType": "WFTextTokenAttachment",
            },
        },
    }


# ── Assemble shortcut ────────────────────────────────────────────────────────

# WiFi string: WIFI:T:WPA;S:<SSID>;P:<Password>;;
# Positions:   0123456789012345 6789...
#   "WIFI:T:WPA;S:" = 14 chars → ORC at offset 14 (SSID)
#   ";P:"           = 3 chars  → ORC at offset 14+1+3 = 18 (Password)
wifi_template = f"WIFI:T:WPA;S:{ORC};P:{ORC};;"
wifi_attachments = {
    "{14, 1}": token_var("SSID"),
    "{18, 1}": token_var("Password"),
}

# QR URL: https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=<encoded>
qr_base = "https://api.qrserver.com/v1/create-qr-code/?size=400x400&data="
qr_template = f"{qr_base}{ORC}"
qr_attachments = {
    f"{{{len(qr_base)}, 1}}": token_output(UUID_URL_ENCODE, "URL Encoded Text"),
}

actions = [
    # 1. Ask for SSID
    ask_for_input("Wi-Fi Network Name (SSID)", UUID_ASK_SSID),
    # 2. Store SSID
    set_variable("SSID", UUID_ASK_SSID, "Wi-Fi Network Name (SSID)"),
    # 3. Ask for Password
    ask_for_input("Wi-Fi Password", UUID_ASK_PASSWORD),
    # 4. Store Password
    set_variable("Password", UUID_ASK_PASSWORD, "Wi-Fi Password"),
    # 5. Build WiFi string
    text_action(wifi_template, wifi_attachments, UUID_WIFI_TEXT),
    # 6. URL-encode WiFi string
    url_encode_action(UUID_WIFI_TEXT, UUID_URL_ENCODE),
    # 7. Build QR API URL
    url_action(qr_template, qr_attachments, UUID_QR_URL_TEXT),
    # 8. Fetch QR image
    get_contents_of_url(UUID_QR_URL_TEXT, UUID_GET_URL),
    # 9. Display QR image
    quick_look(UUID_GET_URL, "Contents of URL"),
]

shortcut = {
    "WFWorkflowClientVersion": "1140.0.3",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 946986751,   # teal-ish
        "WFWorkflowIconGlyphNumber": 59802,
    },
    "WFWorkflowInputContentItemClasses": [],
    "WFWorkflowActions": actions,
    "WFWorkflowTypes": [],
    "WFWorkflowOutputContentItemClasses": [],
    "WFQuickActionSurfaces": [],
    "WFWorkflowHasShortcutInputVariables": False,
}

out_path = "WiFi_QR_Code.shortcut"
with open(out_path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

print(f"Created: {out_path}")
print("Transfer to your iPhone via AirDrop, Files, or iCloud Drive, then tap to import into Shortcuts.")
