"""User-facing UI strings.

Defined once here and referenced everywhere -- production widgets and the tests
that assert on them -- so a label can't drift out of sync between the code that
renders it and the code that checks for it.
"""

# Window titles
HISTORY_WINDOW_TITLE = "VetScribe History"
SETTINGS_WINDOW_TITLE = "VetScribe Settings"

# Tray menu items
MENU_OPEN_LAST_SOAP_NOTE = "Open Last SOAP Note"
MENU_VIEW_HISTORY = "View History"
MENU_SETTINGS = "Settings"
MENU_QUIT = "Quit"

# Buttons
BUTTON_COPY_AND_INJECT = "Copy & Inject to AVImark"
BUTTON_COPY_SOAP_NOTE = "Copy SOAP Note"
BUTTON_DELETE_NOTE = "Delete Note"
BUTTON_SAVE_CHANGES = "Save Changes"
BUTTON_SAVE = "Save"

# History detail-pane labels
LABEL_SOAP_NOTE = "SOAP Note"
LABEL_TRANSCRIPT = "Transcript"

# Settings field labels
LABEL_API_ENDPOINT = "API Endpoint URL"
LABEL_API_KEY = "API Key / Token"
LABEL_HOTKEY = "Hotkey Combination"
LABEL_TARGET_WINDOW = "Target Window Matcher"
LABEL_LAUNCH_ON_STARTUP = "Launch VetScribe on Windows Startup"

# Delete-confirmation dialog
DELETE_CONFIRM_TITLE = "Delete note"
DELETE_CONFIRM_MESSAGE = (
    "Delete this SOAP note and its transcript? This cannot be undone."
)
