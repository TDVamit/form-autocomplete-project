import streamlit as st
import asyncio
import json
import time
import html
import os
from main import data, language_processor, json_agent, validation_agent, reply_agent, next_field, form, get_live_logs

st.set_page_config(page_title="Insurance Form Assistant", layout="wide")

# Add custom CSS for dark theme chat bubbles
st.markdown("""
<style>
/* Dark theme styling */
.stApp {
    background-color: #1e1e1e !important;
    color: #ffffff !important;
}

.main .block-container {
    background-color: #1e1e1e !important;
}

.stColumn {
    background-color: #1e1e1e !important;
}

.stColumn > div {
    background-color: #1e1e1e !important;
}

.element-container {
    background-color: transparent !important;
}

.stMarkdown {
    background-color: transparent !important;
}

.chat-container {
    height: 520px;
    overflow-y: auto;
    padding: 15px;
    border: 1px solid #444;
    border-radius: 15px;
    background-color: #2d2d2d;
    margin-bottom: 20px;
    scrollbar-width: thin;
    scrollbar-color: #666 #2d2d2d;
}

.chat-container::-webkit-scrollbar {
    width: 6px;
}

.chat-container::-webkit-scrollbar-track {
    background: #2d2d2d;
}

.chat-container::-webkit-scrollbar-thumb {
    background: #666;
    border-radius: 3px;
}

.user-message {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 15px;
    animation: slideInRight 0.3s ease-out;
}

.assistant-message {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 15px;
    animation: slideInLeft 0.3s ease-out;
}

.user-bubble {
    background: linear-gradient(135deg, #0084ff 0%, #0066cc 100%);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 5px 18px;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: 0 4px 12px rgba(0, 132, 255, 0.3), 0 2px 4px rgba(0, 0, 0, 0.2);
    font-size: 14px;
    line-height: 1.4;
    position: relative;
}

.assistant-bubble {
    background: linear-gradient(135deg, #444 0%, #555 100%);
    color: #ffffff;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 5px;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: 0 4px 12px rgba(68, 68, 68, 0.4), 0 2px 4px rgba(0, 0, 0, 0.2);
    font-size: 14px;
    line-height: 1.4;
    position: relative;
}

.process-indicator {
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
    color: #ffffff;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 5px;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4), 0 2px 4px rgba(0, 0, 0, 0.2);
    font-size: 12px;
    line-height: 1.4;
    position: relative;
    font-family: monospace;
}

.typing-indicator {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 15px;
}

.typing-bubble {
    background: #444;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 5px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.typing-dots {
    display: inline-block;
}

.typing-dots span {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #999;
    margin: 0 2px;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) {
    animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
    animation-delay: -0.16s;
}

@keyframes typing {
    0%, 80%, 100% {
        transform: scale(0);
    }
    40% {
        transform: scale(1);
    }
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.suggestion-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
    margin-left: 10px;
    margin-bottom: 15px;
}

.suggestion-button {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 20px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3);
    outline: none;
}

.suggestion-button:hover {
    background: linear-gradient(135deg, #218838 0%, #1e7e34 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
}

.suggestion-button:active {
    transform: translateY(0);
}

.enum-button {
    background: linear-gradient(135deg, #6f42c1 0%, #6610f2 100%);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 20px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 6px rgba(111, 66, 193, 0.3);
    outline: none;
}

.enum-button:hover {
    background: linear-gradient(135deg, #5a2d91 0%, #5a23c8 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(111, 66, 193, 0.4);
}

.enum-button:active {
    transform: translateY(0);
}

/* Remove all white backgrounds from form area */
.form-container {
    height: 600px;
    overflow-y: auto;
    padding: 15px;
    border: 1px solid #444;
    border-radius: 15px;
    background-color: #1e1e1e !important;
    scrollbar-width: thin;
    scrollbar-color: #666 #1e1e1e;
}

.form-container::-webkit-scrollbar {
    width: 6px;
}

.form-container::-webkit-scrollbar-track {
    background: #1e1e1e;
}

.form-container::-webkit-scrollbar-thumb {
    background: #666;
    border-radius: 3px;
}

.form-container * {
    background-color: transparent !important;
}

.form-container .stExpander {
    background-color: #2d2d2d !important;
}

.form-container .stExpander > div {
    background-color: #2d2d2d !important;
}

/* Dark theme for form elements */
.stTextInput > div > div > input {
    background-color: #333 !important;
    color: #ffffff !important;
    border: 1px solid #555 !important;
}

.stTextInput > div > div > input[value]:not([value=""]) {
    background-color: #0066cc !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

.stSelectbox > div > div > div {
    background-color: #333 !important;
    color: #ffffff !important;
    border: 1px solid #555 !important;
}

.stCheckbox > label {
    color: #ffffff !important;
}

.stNumberInput > div > div > input {
    background-color: #333 !important;
    color: #ffffff !important;
    border: 1px solid #555 !important;
}

.stNumberInput > div > div > input[value]:not([value="0"]) {
    background-color: #0066cc !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

.stExpander {
    background-color: #2d2d2d !important;
    border: 1px solid #444 !important;
}

.stExpander > div {
    background-color: #2d2d2d !important;
}

/* Headers styling */
h1, h2, h3 {
    color: #ffffff !important;
}

/* Override all white backgrounds */
div[data-testid="stVerticalBlock"] {
    background-color: transparent !important;
}

div[data-testid="column"] {
    background-color: transparent !important;
}

/* Highlight last updated field */
.last-updated-field {
    animation: highlightField 2s ease-in-out;
    border: 2px solid #0084ff !important;
    border-radius: 8px !important;
    background-color: rgba(0, 132, 255, 0.1) !important;
}

@keyframes highlightField {
    0% {
        background-color: rgba(0, 132, 255, 0.3);
        border-color: #0084ff;
    }
    50% {
        background-color: rgba(0, 132, 255, 0.2);
        border-color: #0066cc;
    }
    100% {
        background-color: rgba(0, 132, 255, 0.1);
        border-color: #0084ff;
    }
}

/* Highlight next field that needs to be filled */
.last-updated-field {
    animation: pulseNextField 3s ease-in-out infinite;
    border: 3px solid #28a745 !important;
    border-radius: 10px !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.3) !important;
    padding: 8px !important;
    margin: 4px 0 !important;
}

@keyframes pulseNextField {
    0% {
        border-color: #28a745;
        box-shadow: 0 0 15px rgba(40, 167, 69, 0.3);
        background-color: rgba(40, 167, 69, 0.1);
    }
    50% {
        border-color: #20c997;
        box-shadow: 0 0 25px rgba(40, 167, 69, 0.6);
        background-color: rgba(40, 167, 69, 0.2);
    }
    100% {
        border-color: #28a745;
        box-shadow: 0 0 15px rgba(40, 167, 69, 0.3);
        background-color: rgba(40, 167, 69, 0.1);
    }
}

/* Target actual Streamlit input components for next field */
div[data-testid="stTextInput"]:has(input[data-next-field="true"]) {
    animation: pulseNextField 3s ease-in-out infinite !important;
    border: 3px solid #28a745 !important;
    border-radius: 10px !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.3) !important;
    padding: 8px !important;
    margin: 4px 0 !important;
}

div[data-testid="stCheckbox"]:has(input[data-next-field="true"]) {
    animation: pulseNextField 3s ease-in-out infinite !important;
    border: 3px solid #28a745 !important;
    border-radius: 10px !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.3) !important;
    padding: 8px !important;
    margin: 4px 0 !important;
}

div[data-testid="stNumberInput"]:has(input[data-next-field="true"]) {
    animation: pulseNextField 3s ease-in-out infinite !important;
    border: 3px solid #28a745 !important;
    border-radius: 10px !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.3) !important;
    padding: 8px !important;
    margin: 4px 0 !important;
}

/* Alternative approach - target by key attribute */
div[data-testid="stTextInput"]:has(input[id*="next-field"]) {
    animation: pulseNextField 3s ease-in-out infinite !important;
    border: 3px solid #28a745 !important;
    border-radius: 10px !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.3) !important;
    padding: 8px !important;
    margin: 4px 0 !important;
}

div[data-testid="stCheckbox"]:has(input[id*="next-field"]) {
    animation: pulseNextField 3s ease-in-out infinite !important;
    border: 3px solid #28a745 !important;
    border-radius: 10px !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.3) !important;
    padding: 8px !important;
    margin: 4px 0 !important;
}

div[data-testid="stNumberInput"]:has(input[id*="next-field"]) {
    animation: pulseNextField 3s ease-in-out infinite !important;
    border: 3px solid #28a745 !important;
    border-radius: 10px !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 0 0 15px rgba(40, 167, 69, 0.3) !important;
    padding: 8px !important;
    margin: 4px 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Session state for chat history and form
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "form_snapshot" not in st.session_state:
    st.session_state.form_snapshot = json.loads(json.dumps(data.data))
if "greeted" not in st.session_state:
    st.session_state.greeted = False
if "is_typing" not in st.session_state:
    st.session_state.is_typing = False
if "suggestion_clicked" not in st.session_state:
    st.session_state.suggestion_clicked = None
if "processing_step" not in st.session_state:
    st.session_state.processing_step = 0
if "processing_message" not in st.session_state:
    st.session_state.processing_message = ""
if "current_user_message" not in st.session_state:
    st.session_state.current_user_message = ""
if "last_updated_field" not in st.session_state:
    st.session_state.last_updated_field = None
if "focus_next_field" not in st.session_state:
    st.session_state.focus_next_field = True

# Greet the user on first load
if not st.session_state.greeted:
    greeting = "Hi! To get started with your insurance information, could you please provide Your Full Name."
    st.session_state.chat_history.append({
        "role": "assistant", 
        "content": greeting,
        "enums": None,
        "suggestion_values": None
    })
    st.session_state.greeted = True

def detect_last_updated_field(previous_snapshot, current_snapshot, path=""):
    """Detect which field was last updated by comparing form snapshots"""
    if not isinstance(previous_snapshot, dict) or not isinstance(current_snapshot, dict):
        return None
    
    for key, current_value in current_snapshot.items():
        current_path = f"{path}.{key}" if path else key
        
        if key not in previous_snapshot:
            continue
            
        previous_value = previous_snapshot[key]
        
        # Check if this is a field with a value that changed
        if isinstance(current_value, dict) and isinstance(previous_value, dict):
            if "value" in current_value and "value" in previous_value:
                if current_value.get("value") != previous_value.get("value"):
                    # This field's value changed
                    if current_value.get("value") is not None and previous_value.get("value") is None:
                        return current_path
            
            # Recursively check nested fields
            nested_result = detect_last_updated_field(previous_value, current_value, current_path)
            if nested_result:
                return nested_result
                
        elif isinstance(current_value, list) and isinstance(previous_value, list):
            # Check list changes
            if len(current_value) != len(previous_value):
                return current_path
            for i, (prev_item, curr_item) in enumerate(zip(previous_value, current_value)):
                nested_result = detect_last_updated_field(prev_item, curr_item, f"{current_path}[{i}]")
                if nested_result:
                    return nested_result
    
    return None

def render_form_field(field_name, field_data, level=0):
    """Recursively render form fields as Streamlit components"""
    if not isinstance(field_data, dict):
        return
    
    field_type = field_data.get("type")
    description = field_data.get("description", field_name)
    value = field_data.get("value")
    is_required = field_data.get("is_required", False)
    
    # Check if this is the next field that needs to be filled - use form_snapshot
    next_field_obj = next_field(st.session_state.form_snapshot)
    is_next_field = False
    if next_field_obj and st.session_state.focus_next_field:
        next_field_desc = next_field_obj.get("description", "")
        if description == next_field_desc:
            is_next_field = True
    
    # Add indentation based on nesting level
    indent = "  " * level
    
    # Create unique field ID for highlighting - use special key for next field
    if is_next_field:
        field_id = f"next-field-{field_name}_{level}_{id(field_data)}"
    else:
        field_id = f"field_{field_name}_{level}_{id(field_data)}"
    
    # Add visual indicator for next field using Streamlit native components
    if is_next_field:
        st.info(f"👉 **NEXT:** Please provide your {description.lower()}")
    
    if field_type == "string" or field_type == "enum":
        label = f"{indent}{description}" + (" *" if is_required else "")
        if is_next_field:
            st.markdown("🎯 **FILL THIS FIELD NEXT:**")
        st.text_input(label, value=value or "", disabled=True, key=field_id)
    
    elif field_type == "boolean":
        label = f"{indent}{description}" + (" *" if is_required else "")
        if is_next_field:
            st.markdown("🎯 **FILL THIS FIELD NEXT:**")
        st.checkbox(label, value=bool(value), disabled=True, key=field_id)
    
    elif field_type == "date":
        label = f"{indent}{description}" + (" *" if is_required else "")
        if is_next_field:
            st.markdown("🎯 **FILL THIS FIELD NEXT:**")
        if value:
            st.text_input(label, value=str(value), disabled=True, key=field_id)
        else:
            st.text_input(label, value="", placeholder="DD-MM-YYYY", disabled=True, key=field_id)
    
    elif field_type == "integer":
        label = f"{indent}{description}" + (" *" if is_required else "")
        # Convert to float for st.number_input compatibility
        number_value = float(value) if value is not None else 0.0
        if is_next_field:
            st.markdown("🎯 **FILL THIS FIELD NEXT:**")
        st.number_input(label, value=number_value, disabled=True, key=field_id, step=1.0, format="%.0f")
    
    elif field_type == "object":
        if value and isinstance(value, dict):
            # Use expander only at top level (level 0), subheader for deeper levels
            if level == 0:
                with st.expander(f"{description}", expanded=True):
                    for sub_field_name, sub_field_data in value.items():
                        render_form_field(sub_field_name, sub_field_data, level + 1)
            else:
                st.subheader(f"{indent}{description}")
                with st.container():
                    for sub_field_name, sub_field_data in value.items():
                        render_form_field(sub_field_name, sub_field_data, level + 1)
    
    elif field_type == "list":
        if value and isinstance(value, list):
            # Use expander only at top level (level 0), subheader for deeper levels
            if level == 0:
                with st.expander(f"{description} ({len(value)} items)", expanded=False):
                    for i, item in enumerate(value):
                        st.markdown(f"**{description} #{i+1}**")
                        if isinstance(item, dict) and item.get("type") == "object":
                            item_value = item.get("value", {})
                            for sub_field_name, sub_field_data in item_value.items():
                                render_form_field(sub_field_name, sub_field_data, level + 1)
                        if i < len(value) - 1:
                            st.divider()
            else:
                st.subheader(f"{indent}{description} ({len(value)} items)")
                with st.container():
                    for i, item in enumerate(value):
                        st.markdown(f"**{description} #{i+1}**")
                        if isinstance(item, dict) and item.get("type") == "object":
                            item_value = item.get("value", {})
                            for sub_field_name, sub_field_data in item_value.items():
                                render_form_field(sub_field_name, sub_field_data, level + 1)
                        if i < len(value) - 1:
                            st.divider()

def process_step_by_step():
    """Process the chat pipeline step by step with UI updates"""
    
    if st.session_state.processing_step == 1:
        st.session_state.processing_message = "🧠 Processing language..."
        st.session_state.processing_step = 2  # Advance to next step
        st.rerun()
    
    elif st.session_state.processing_step == 2:
        # Language processing
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            processed_message = loop.run_until_complete(language_processor(data, st.session_state.current_user_message))
            loop.close()
            
            st.session_state.processed_data = processed_message
            st.session_state.processing_message = "⚙️ Updating form..."
            st.session_state.processing_step = 3
            st.rerun()
        except Exception as e:
            st.error(f"Language processing failed: {str(e)}")
            st.session_state.is_typing = False
            st.session_state.processing_step = 0
            st.rerun()
    
    elif st.session_state.processing_step == 3:
        # JSON agent processing
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            json_response = loop.run_until_complete(json_agent(data, st.session_state.processed_data))
            loop.close()

            st.session_state.form_snapshot = json.loads(json.dumps(data.data))

            st.session_state.json_response = json_response
            st.session_state.processing_message = "🔍 Validating data..."
            st.session_state.processing_step = 4
            st.rerun()
        except Exception as e:
            st.error(f"Form update failed: {str(e)}")
            st.session_state.is_typing = False
            st.session_state.processing_step = 0
            st.rerun()
    
    elif st.session_state.processing_step == 4:
        # Validation (with retry logic)
        try:
            if "validation_tries" not in st.session_state:
                st.session_state.validation_tries = 3

            processed_data = st.session_state.processed_data
            if isinstance(processed_data, dict) and processed_data.get('command_type', '') != 'find':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                validation_response = loop.run_until_complete(validation_agent(data))
                loop.close()

                if validation_response.get('commands', []):
                    st.session_state.validation_tries -= 1
                    if st.session_state.validation_tries > 0:
                        st.session_state.processing_message = f"🔧 Fixing validation issues... (retries left: {st.session_state.validation_tries})"
                        # Update the message to follow the commands and retry
                        st.session_state.processed_data = {
                            "command_type": "update",
                            "fields": {"_validation_commands": validation_response["commands"]}
                        }
                        st.session_state.processing_step = 3  # Go back to JSON agent step
                        st.rerun()
                    else:
                        st.session_state.processing_message = "❌ Validation failed after 3 attempts."
                        st.session_state.validation_tries = 3  # Reset for next time
                        st.session_state.processing_step = 5  # Proceed to reply anyway
                        st.rerun()
                else:
                    st.session_state.processing_message = "✅ Validation passed"
                    st.session_state.validation_tries = 3  # Reset for next time

            st.session_state.processing_step = 5
            st.rerun()
        except Exception as e:
            st.error(f"Validation failed: {str(e)}")
            st.session_state.is_typing = False
            st.session_state.processing_step = 0
            st.rerun()
    
    elif st.session_state.processing_step == 5:
        # Reply generation
        try:
            st.session_state.processing_message = "💬 Generating response..."
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            reply_response = loop.run_until_complete(reply_agent(data, st.session_state.json_response))
            loop.close()
            
            # Add response to chat history
            assistant_message = reply_response.get("message", str(reply_response))
            enums = reply_response.get("enums", [])
            suggestion_values = reply_response.get("suggestion_values", [])
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": assistant_message,
                "enums": enums,
                "suggestion_values": suggestion_values
            })
            
            # Update form snapshot and trigger next field focus
            st.session_state.form_snapshot = json.loads(json.dumps(data.data))
            st.session_state.focus_next_field = True
            
            # Reset processing state
            st.session_state.is_typing = False
            st.session_state.processing_step = 0
            st.session_state.processing_message = ""
            st.session_state.current_user_message = ""
            
            st.rerun()
        except Exception as e:
            st.error(f"Reply generation failed: {str(e)}")
            st.session_state.is_typing = False
            st.session_state.processing_step = 0
            st.rerun()

# Split the page into two columns
col1, col2 = st.columns([2, 2])

with col1:
    st.subheader("💬 Chat")
    
    # Create a scrollable container for chat with same height as form
    with st.container(height=690):
        # Display chat messages using Streamlit's native chat interface with custom styling
        for i, entry in enumerate(st.session_state.chat_history):
            if entry["role"] == "user":
                with st.chat_message("user"):
                    st.write(entry["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(entry["content"])
                    
                    # Add suggestion buttons if they exist
                    enums = entry.get("enums")
                    suggestions = entry.get("suggestion_values")
                    
                    if enums or suggestions:
                        # Create a compact container for all options
                        with st.container():
                            st.write("**Quick Options:**")
                            
                            # Collect all options
                            all_options = []
                            if enums:
                                for enum_val in enums:
                                    if enum_val:
                                        all_options.append(("enum", enum_val))
                            if suggestions:
                                for suggestion in suggestions:
                                    if suggestion:
                                        all_options.append(("suggestion", suggestion))
                            
                            # Only create columns if we have options to display
                            if all_options:
                                # Display all buttons in a more compact layout using fewer columns
                                num_options = len(all_options)
                                if num_options <= 2:
                                    cols = st.columns(num_options)
                                elif num_options <= 4:
                                    cols = st.columns(2)
                                else:
                                    cols = st.columns(3)
                                
                                for idx, (option_type, option_value) in enumerate(all_options):
                                    col_idx = idx % len(cols)
                                    with cols[col_idx]:
                                        if option_type == "enum":
                                            button_label = f"🔘 {option_value}"
                                        else:
                                            button_label = f"💡 {option_value}"
                                        
                                        if st.button(button_label, key=f"{option_type}_{i}_{idx}_{option_value}", use_container_width=True):
                                            st.session_state.suggestion_clicked = option_value
                                            st.rerun()
        
        # Show detailed processing indicator
        if st.session_state.is_typing:
            with st.chat_message("assistant"):
                # Current status
                st.write(f"**{st.session_state.processing_message}**")
    
    # Chat input
    if next_field(form) is not None:
        user_input = st.chat_input("Type your message and press Enter...")
    else:
        st.success("🎉 Thank you! All required fields are completed.")
        user_input = None

with col2:
    st.subheader("📋 Form Data")
    
    # Create a scrollable container for form data that takes full height
    with st.container(height=750):  # Large height to use most of screen space
        # Add scroll trigger point for next field
        if st.session_state.focus_next_field and next_field(form):
            scroll_placeholder = st.empty()
        
        # Render the form data as actual form fields
        for section_name, section_data in st.session_state.form_snapshot.items():
            render_form_field(section_name, section_data)
        
        # Auto-scroll to next field when focus_next_field is True
        if st.session_state.focus_next_field and next_field(st.session_state.form_snapshot):
            next_field_obj = next_field(st.session_state.form_snapshot)
            next_field_desc = next_field_obj.get("description", "")
            
            import streamlit.components.v1 as components
            
            # Create a unique ID for this scroll event to ensure JavaScript runs
            import time
            scroll_id = int(time.time() * 1000) % 10000
            
            components.html(f"""
            <script>
            // Unique execution ID: {scroll_id}
            try {{
                if (window.parent && window.parent.document) {{
                    // Wait for Streamlit's rendering to complete
                    setTimeout(function() {{
                        const parentDoc = window.parent.document;
                        let targetElement = null;
                        
                        // Look for labels containing the next field description
                        const labels = parentDoc.querySelectorAll('label');
                        for (let label of labels) {{
                            if (label.textContent && label.textContent.includes('{next_field_desc}')) {{
                                targetElement = label.closest('[data-testid^="st"]') || label.parentElement;
                                break;
                            }}
                        }}
                        
                        // Fallback: Look for info boxes with "NEXT:" text
                        if (!targetElement) {{
                            const infoBoxes = parentDoc.querySelectorAll('[data-testid="stAlert"]');
                            for (let box of infoBoxes) {{
                                if (box.textContent && box.textContent.includes('NEXT:')) {{
                                    targetElement = box;
                                    break;
                                }}
                            }}
                        }}
                        
                        // Only scroll if we found the target and it's not already visible
                        if (targetElement) {{
                            const rect = targetElement.getBoundingClientRect();
                            const isVisible = rect.top >= 0 && rect.bottom <= window.parent.innerHeight;
                            
                            if (!isVisible) {{
                                targetElement.scrollIntoView({{
                                    behavior: 'smooth',
                                    block: 'center'
                                }});
                            }}
                            
                            // Visual feedback with green highlighting
                            targetElement.style.border = '3px solid #28a745';
                            targetElement.style.backgroundColor = 'rgba(40, 167, 69, 0.1)';
                            targetElement.style.boxShadow = '0 0 15px rgba(40, 167, 69, 0.3)';
                            
                            setTimeout(() => {{
                                targetElement.style.border = '';
                                targetElement.style.backgroundColor = '';
                                targetElement.style.boxShadow = '';
                            }}, 2000);
                        }}
                    }}, 1500);
                }}
            }} catch (e) {{
                // Silent fail for robustness
            }}
            </script>
            """, height=0)
            
            # Reset the flag after JavaScript is injected
            st.session_state.focus_next_field = False

# Handle suggestion clicks
if st.session_state.suggestion_clicked:
    user_input = st.session_state.suggestion_clicked
    st.session_state.suggestion_clicked = None

# Handle chat interaction
if user_input:
    st.session_state.chat_history.append({
        "role": "user", 
        "content": user_input,
        "enums": None,
        "suggestion_values": None
    })
    
    st.session_state.is_typing = True
    st.session_state.processing_step = 1
    st.session_state.current_user_message = user_input
    st.rerun()

# Handle assistant response with detailed processing
if st.session_state.is_typing:
    process_step_by_step() 

# --- LOG VIEWER SECTION ---
from main import get_live_logs
last_logs = get_live_logs(50)
log_text = "\n".join(last_logs)
st.markdown("---")
st.subheader("📝 System Logs (last 50 lines)")
st.code(log_text, language="text") 