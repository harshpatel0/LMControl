PYTHON_RUNNER_VENV_NAME = ".kodo_venv"

API_BIND_TO_ALL_IPS = True
API_PORT = 8000

API_DESKTOP_STREAMING_FRAME_RATE = 24
API_DESKTOP_STREAMING_PICTURE_QUALITY = 70

ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE = False
ACTOR_MODEL_DEBUG_USER_PROMPT_CONSTRUCTION_TO_FILE = "dbg_actor_model.txt"

MODEL_DEFINITIONS_ENABLE_DEBUG_OLLAMA_REQUESTS = False
MODEL_DEFINITIONS_DEBUG_OLLAMA_REQUESTS_TO_FILE = "dbg_make_ollama_request.txt"

CONTEXT_PROVIDER_UI_DIFF_THRESHOLD_PERCENTAGE = 30

ALLOWED_CONTROL_TYPES = {
    # Core interactive controls
    "Button",
    "Edit",
    "ComboBox",
    "List",
    "ListItem",
    "Menu",
    "MenuItem",
    "MenuBar",
    "CheckBox",
    "RadioButton",
    "Slider",
    "Spinner",
    # Text + document
    "Text",
    "Document",
    # Containers / structure
    "Pane",
    "Group",
    "Window",
    "Custom",
    # Navigation / hierarchy
    "Tree",
    "TreeItem",
    "Tab",
    "TabItem",
    # Advanced / less common but useful
    "Hyperlink",
    "DataItem",
    "DataGrid",
    "Table",
    # Tooling / UX
    "ToolBar",
    "StatusBar",
    "TitleBar",
    # Modern UI patterns
    "SplitButton",
    "Thumb",
    "ProgressBar",
}
