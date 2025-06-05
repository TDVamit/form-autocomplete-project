import streamlit as st
import asyncio
import json
import time
import html
import os
from main import data, language_processor, json_agent, validation_agent, reply_agent, next_field, form, get_live_logs

st.set_page_config(page_title="Insurance Form Assistant", layout="wide")

# Check if app has started
if "app_started" not in st.session_state:
    st.session_state.app_started = False

# Show start screen if app hasn't started
if not st.session_state.app_started:
    # Add custom CSS for centering
    st.markdown("""
    <style>
    .main > div {
        padding-top: 10rem;
    }

    /* Hide all other elements during start screen */
    .main .block-container > div:not(:first-child) {
        display: none;
    }
    
    /* Enhanced Start Button Styling - Higher specificity */
    div[data-testid="column"] .stButton > button,
    .stButton button,
    button[kind="primary"],
    .stButton > button {
        background: linear-gradient(135deg, #0084ff 0%, #0066cc 50%, #004499 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 20px 40px !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        position: relative !important;
        overflow: hidden !important;
        cursor: pointer !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 
            0 10px 30px rgba(0, 132, 255, 0.4),
            0 5px 15px rgba(0, 0, 0, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.2) !important;
        animation: startButtonPulse 3s ease-in-out infinite !important;
        transform: translateZ(0) !important;
        width: 100% !important;
        min-height: 70px !important;
        border-width: 0 !important;
        outline: none !important;
    }
    
    @keyframes startButtonPulse {
        0%, 100% {
            transform: scale(1) translateY(0);
            box-shadow: 
                0 10px 30px rgba(0, 132, 255, 0.4),
                0 5px 15px rgba(0, 0, 0, 0.3),
                inset 0 2px 0 rgba(255, 255, 255, 0.2);
        }
        50% {
            transform: scale(1.05) translateY(-3px);
            box-shadow: 
                0 15px 40px rgba(0, 132, 255, 0.6),
                0 8px 25px rgba(0, 0, 0, 0.4),
                inset 0 2px 0 rgba(255, 255, 255, 0.3);
        }
    }
    
    /* Shimmer effect */
    div[data-testid="column"] .stButton > button::before,
    .stButton button::before,
    button[kind="primary"]::before,
    .stButton > button::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent) !important;
        transition: left 0.8s ease !important;
        z-index: 1 !important;
    }
    
    div[data-testid="column"] .stButton > button:hover::before,
    .stButton button:hover::before,
    button[kind="primary"]:hover::before,
    .stButton > button:hover::before {
        left: 100% !important;
    }
    
    /* Hover effects */
    div[data-testid="column"] .stButton > button:hover,
    .stButton button:hover,
    button[kind="primary"]:hover,
    .stButton > button:hover {
        background: linear-gradient(135deg, #0066cc 0%, #004499 50%, #002266 100%) !important;
        transform: translateY(-8px) scale(1.1) rotate(2deg) !important;
        box-shadow: 
            0 20px 50px rgba(0, 132, 255, 0.8),
            0 10px 30px rgba(0, 0, 0, 0.5),
            inset 0 2px 0 rgba(255, 255, 255, 0.4) !important;
        animation: startButtonHoverBounce 0.6s ease-in-out !important;
        letter-spacing: 3px !important;
    }
    
    @keyframes startButtonHoverBounce {
        0%, 100% { transform: translateY(-8px) scale(1.1) rotate(2deg); }
        25% { transform: translateY(-12px) scale(1.15) rotate(-1deg); }
        75% { transform: translateY(-6px) scale(1.08) rotate(3deg); }
    }
    
    /* Active/Click effects */
    div[data-testid="column"] .stButton > button:active,
    .stButton button:active,
    button[kind="primary"]:active,
    .stButton > button:active {
        transform: translateY(-4px) scale(1.05) rotate(1deg) !important;
        transition: all 0.1s ease !important;
        animation: startButtonClick 0.2s ease-out !important;
    }
    
    @keyframes startButtonClick {
        0% { transform: translateY(-4px) scale(1.05) rotate(1deg); }
        50% { transform: translateY(-2px) scale(1.02) rotate(0deg); }
        100% { transform: translateY(-4px) scale(1.05) rotate(1deg); }
    }
    
    /* Glow effect */
    div[data-testid="column"] .stButton > button::after,
    .stButton button::after,
    button[kind="primary"]::after,
    .stButton > button::after {
        content: '' !important;
        position: absolute !important;
        top: -2px !important;
        left: -2px !important;
        right: -2px !important;
        bottom: -2px !important;
        background: linear-gradient(135deg, #0084ff, #0066cc, #004499) !important;
        border-radius: 27px !important;
        z-index: -1 !important;
        opacity: 0 !important;
        transition: opacity 0.3s ease !important;
        filter: blur(8px) !important;
    }
    
    div[data-testid="column"] .stButton > button:hover::after,
    .stButton button:hover::after,
    button[kind="primary"]:hover::after,
    .stButton > button:hover::after {
        opacity: 0.7 !important;
        animation: glowPulse 1s ease-in-out infinite !important;
    }
    
    @keyframes glowPulse {
        0%, 100% { opacity: 0.7; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.05); }
    }
    
    /* Focus state */
    div[data-testid="column"] .stButton > button:focus,
    .stButton button:focus,
    button[kind="primary"]:focus,
    .stButton > button:focus {
        outline: none !important;
        box-shadow: 
            0 0 0 4px rgba(0, 132, 255, 0.3),
            0 15px 40px rgba(0, 132, 255, 0.6),
            0 8px 25px rgba(0, 0, 0, 0.4),
            inset 0 2px 0 rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Override any default Streamlit button styles */
    .stButton button[data-testid="baseButton-secondary"],
    .stButton button[data-testid="baseButton-primary"],
    .stButton > div > button {
        background: linear-gradient(135deg, #0084ff 0%, #0066cc 50%, #004499 100%) !important;
        color: white !important;
        border: none !important;
        animation: startButtonPulse 3s ease-in-out infinite !important;
    }
    
    /* Prevent conflicts with title animation */
    h1 {
        animation: titleFadeIn 1.5s ease-out !important;
    }
    
    @keyframes titleFadeIn {
        from { opacity: 0; transform: translateY(-50px) scale(0.8); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add spacing from top
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Centered title
    st.markdown('<h1 style="color: #ffffff; font-size: 10rem; font-weight: bold; text-align: center; margin-bottom: 3rem;">Insurance Form <br> Assistant</h1>', unsafe_allow_html=True)
    
    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Center the start button with better spacing
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🚀 Start", key="start_app", use_container_width=True):
            # Initialize fresh session-specific data
            from main import form, Form
            import json
            
            # Create a deep copy of the form for this session
            session_form_data = json.loads(json.dumps(form))
            
            # Initialize session-specific form instance
            st.session_state.session_data = Form(
                data=session_form_data, 
                history=[],
                language_processor_response=[]
            )
            
            # Initialize other session state variables
            st.session_state.form_snapshot = json.loads(json.dumps(session_form_data))
            st.session_state.chat_history = []
            st.session_state.greeted = False
            st.session_state.is_typing = False
            st.session_state.suggestion_clicked = None
            st.session_state.processing_step = 0
            st.session_state.processing_message = ""
            st.session_state.current_user_message = ""
            st.session_state.focus_next_field = True
            
            st.session_state.app_started = True
            st.rerun()
    
    # Add JavaScript to ensure button styling is applied
    import streamlit.components.v1 as components
    components.html("""
    <script>
        // Wait for the page to load and apply button styling
        setTimeout(function() {
            const buttons = document.querySelectorAll('button');
            buttons.forEach(button => {
                if (button.textContent.includes('🚀 Start') || button.textContent.includes('Start')) {
                    // Apply the styling directly via JavaScript
                    button.style.cssText = `
                        background: linear-gradient(135deg, #0084ff 0%, #0066cc 50%, #004499 100%) !important;
                        color: white !important;
                        border: none !important;
                        border-radius: 25px !important;
                        padding: 20px 40px !important;
                        font-size: 1.5rem !important;
                        font-weight: 700 !important;
                        letter-spacing: 2px !important;
                        text-transform: uppercase !important;
                        position: relative !important;
                        overflow: hidden !important;
                        cursor: pointer !important;
                        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                        box-shadow: 0 10px 30px rgba(0, 132, 255, 0.4), 0 5px 15px rgba(0, 0, 0, 0.3), inset 0 2px 0 rgba(255, 255, 255, 0.2) !important;
                        animation: startButtonPulse 3s ease-in-out infinite !important;
                        transform: translateZ(0) !important;
                        width: 100% !important;
                        min-height: 70px !important;
                        border-width: 0 !important;
                        outline: none !important;
                    `;
                    
                    // Add hover effects
                    button.addEventListener('mouseenter', function() {
                        this.style.background = 'linear-gradient(135deg, #0066cc 0%, #004499 50%, #002266 100%)';
                        this.style.transform = 'translateY(-8px) scale(1.1) rotate(2deg)';
                        this.style.boxShadow = '0 20px 50px rgba(0, 132, 255, 0.8), 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 2px 0 rgba(255, 255, 255, 0.4)';
                        this.style.letterSpacing = '3px';
                    });
                    
                    button.addEventListener('mouseleave', function() {
                        this.style.background = 'linear-gradient(135deg, #0084ff 0%, #0066cc 50%, #004499 100%)';
                        this.style.transform = 'translateZ(0)';
                        this.style.boxShadow = '0 10px 30px rgba(0, 132, 255, 0.4), 0 5px 15px rgba(0, 0, 0, 0.3), inset 0 2px 0 rgba(255, 255, 255, 0.2)';
                        this.style.letterSpacing = '2px';
                    });
                    
                    button.addEventListener('mousedown', function() {
                        this.style.transform = 'translateY(-4px) scale(1.05) rotate(1deg)';
                        this.style.transition = 'all 0.1s ease';
                    });
                    
                    button.addEventListener('mouseup', function() {
                        this.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                    });
                }
            });
        }, 500);
        
        // Also apply on any DOM changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    const buttons = document.querySelectorAll('button');
                    buttons.forEach(button => {
                        if (button.textContent.includes('🚀 Start') && !button.classList.contains('styled')) {
                            button.classList.add('styled');
                            button.style.cssText = `
                                background: linear-gradient(135deg, #0084ff 0%, #0066cc 50%, #004499 100%) !important;
                                color: white !important;
                                border: none !important;
                                border-radius: 25px !important;
                                padding: 20px 40px !important;
                                font-size: 1.5rem !important;
                                font-weight: 700 !important;
                                letter-spacing: 2px !important;
                                text-transform: uppercase !important;
                                animation: startButtonPulse 3s ease-in-out infinite !important;
                                width: 100% !important;
                                min-height: 70px !important;
                            `;
                        }
                    });
                }
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    </script>
    
    <style>
        @keyframes startButtonPulse {
            0%, 100% {
                transform: scale(1) translateY(0);
                box-shadow: 0 10px 30px rgba(0, 132, 255, 0.4), 0 5px 15px rgba(0, 0, 0, 0.3), inset 0 2px 0 rgba(255, 255, 255, 0.2);
            }
            50% {
                transform: scale(1.05) translateY(-3px);
                box-shadow: 0 15px 40px rgba(0, 132, 255, 0.6), 0 8px 25px rgba(0, 0, 0, 0.4), inset 0 2px 0 rgba(255, 255, 255, 0.3);
            }
        }
    </style>
    """, height=0)
    
    st.stop()

# Main app interface (only shows after start button is pressed)

# Add custom CSS for dark theme chat bubbles
st.markdown("""
<style>
/* Pure black theme styling with enhanced chat animations */
.stApp {
    background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%) !important;
    color: #ffffff !important;
    min-height: 100vh;
}

.main .block-container {
    background: transparent !important;
    padding-top: 1rem !important;
    animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.stColumn {
    background: transparent !important;
    animation: slideInUp 0.5s ease-out;
}

@keyframes slideInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.element-container {
    background: transparent !important;
}

.stMarkdown {
    background: transparent !important;
}

/* Enhanced chat container with more animations */
.chat-container {
    height: 520px;
    overflow-y: auto;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    margin-bottom: 20px;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    scrollbar-width: thin;
    scrollbar-color: #333 transparent;
    transition: all 0.4s ease;
    animation: chatContainerSlide 0.8s ease-out;
}

@keyframes chatContainerSlide {
    from { 
        opacity: 0; 
        transform: translateX(-30px) scale(0.95); 
    }
    to { 
        opacity: 1; 
        transform: translateX(0) scale(1); 
    }
}

.chat-container:hover {
    box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.8),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
}

.chat-container::-webkit-scrollbar {
    width: 8px;
}

.chat-container::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
}

.chat-container::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #333 0%, #555 100%);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.chat-container::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #444 0%, #666 100%);
}

/* Enhanced chat bubbles with more animations */
.user-message {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 15px;
    animation: slideInRightBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.assistant-message {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 15px;
    animation: slideInLeftBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.user-bubble {
    background: linear-gradient(135deg, #0084ff 0%, #0066cc 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 20px 20px 5px 20px;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: 
        0 8px 25px rgba(0, 132, 255, 0.4),
        0 4px 10px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
    font-size: 14px;
    line-height: 1.5;
    position: relative;
    transition: all 0.3s ease;
    transform: translateZ(0);
    animation: messagePop 0.4s ease-out;
}

@keyframes messagePop {
    0% { transform: scale(0.8) rotate(5deg); opacity: 0; }
    50% { transform: scale(1.1) rotate(-2deg); opacity: 0.8; }
    100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

.user-bubble:hover {
    transform: translateY(-3px) scale(1.03) rotate(1deg);
    box-shadow: 
        0 15px 40px rgba(0, 132, 255, 0.6),
        0 8px 20px rgba(0, 0, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.3);
    animation: bubbleWiggle 0.6s ease-in-out;
}

@keyframes bubbleWiggle {
    0%, 100% { transform: translateY(-3px) scale(1.03) rotate(1deg); }
    25% { transform: translateY(-4px) scale(1.04) rotate(-1deg); }
    75% { transform: translateY(-2px) scale(1.02) rotate(2deg); }
}

.assistant-bubble {
    background: linear-gradient(135deg, #222 0%, #333 100%);
    color: #ffffff;
    padding: 15px 20px;
    border-radius: 20px 20px 20px 5px;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: 
        0 8px 25px rgba(0, 0, 0, 0.7),
        0 4px 10px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    font-size: 14px;
    line-height: 1.5;
    position: relative;
    transition: all 0.3s ease;
    animation: messageSlideIn 0.5s ease-out;
}

@keyframes messageSlideIn {
    0% { transform: translateX(-50px) scale(0.9); opacity: 0; }
    60% { transform: translateX(10px) scale(1.05); opacity: 0.8; }
    100% { transform: translateX(0) scale(1); opacity: 1; }
}

.assistant-bubble:hover {
    transform: translateY(-3px) scale(1.03) rotate(-1deg);
    box-shadow: 
        0 15px 40px rgba(0, 0, 0, 0.8),
        0 8px 20px rgba(0, 0, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
    animation: assistantBubbleFloat 1s ease-in-out infinite;
}

@keyframes assistantBubbleFloat {
    0%, 100% { transform: translateY(-3px) scale(1.03) rotate(-1deg); }
    50% { transform: translateY(-5px) scale(1.04) rotate(1deg); }
}

.process-indicator {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: #ffffff;
    padding: 15px 20px;
    border-radius: 20px 20px 20px 5px;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: 
        0 8px 25px rgba(0, 0, 0, 0.7),
        0 4px 10px rgba(0, 0, 0, 0.5);
    font-size: 12px;
    line-height: 1.4;
    position: relative;
    font-family: 'Courier New', monospace;
    animation: processingPulse 2s infinite ease-in-out;
}

@keyframes processingPulse {
    0%, 100% { 
        transform: scale(1); 
        opacity: 1; 
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.7);
    }
    50% { 
        transform: scale(1.05); 
        opacity: 0.9; 
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.8);
    }
}

/* Enhanced typing indicator with more animations */
.typing-indicator {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 15px;
    animation: typingSlideIn 0.4s ease-out;
}

@keyframes typingSlideIn {
    0% { opacity: 0; transform: translateX(-30px) scale(0.8); }
    100% { opacity: 1; transform: translateX(0) scale(1); }
}

.typing-bubble {
    background: linear-gradient(135deg, #222 0%, #333 100%);
    padding: 15px 20px;
    border-radius: 20px 20px 20px 5px;
    box-shadow: 
        0 8px 25px rgba(0, 0, 0, 0.6),
        0 4px 10px rgba(0, 0, 0, 0.4);
    animation: typingBreathe 2s infinite ease-in-out;
}

@keyframes typingBreathe {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.08); opacity: 0.8; }
}

.typing-dots {
    display: inline-block;
}

.typing-dots span {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, #666 0%, #888 100%);
    margin: 0 3px;
    animation: typingDots 1.6s infinite ease-in-out;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingDots {
    0%, 80%, 100% { 
        transform: scale(0.6) translateY(0);
        opacity: 0.3;
    }
    40% { 
        transform: scale(1.4) translateY(-10px);
        opacity: 1;
    }
}

/* Enhanced chat animations */
@keyframes slideInRightBounce {
    0% {
        opacity: 0;
        transform: translateX(100px) scale(0.3) rotate(10deg);
    }
    50% {
        opacity: 0.8;
        transform: translateX(-10px) scale(1.1) rotate(-5deg);
    }
    100% {
        opacity: 1;
        transform: translateX(0) scale(1) rotate(0deg);
    }
}

@keyframes slideInLeftBounce {
    0% {
        opacity: 0;
        transform: translateX(-100px) scale(0.3) rotate(-10deg);
    }
    50% {
        opacity: 0.8;
        transform: translateX(10px) scale(1.1) rotate(5deg);
    }
    100% {
        opacity: 1;
        transform: translateX(0) scale(1) rotate(0deg);
    }
}

/* Enhanced suggestion buttons with staggered animations */
.suggestion-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 15px;
    margin-left: 10px;
    margin-bottom: 15px;
    animation: suggestionsStagger 0.8s ease-out;
}

@keyframes suggestionsStagger {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.suggestion-button {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 25px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 
        0 4px 15px rgba(40, 167, 69, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
    outline: none;
    position: relative;
    overflow: hidden;
    animation: buttonPopIn 0.5s ease-out forwards;
    animation-delay: calc(var(--delay, 0) * 0.1s);
    opacity: 0;
    transform: scale(0.8) translateY(20px);
}

@keyframes buttonPopIn {
    0% { opacity: 0; transform: scale(0.8) translateY(20px) rotate(10deg); }
    70% { opacity: 1; transform: scale(1.1) translateY(-5px) rotate(-2deg); }
    100% { opacity: 1; transform: scale(1) translateY(0) rotate(0deg); }
}

.suggestion-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.6s;
}

.suggestion-button:hover::before {
    left: 100%;
}

.suggestion-button:hover {
    background: linear-gradient(135deg, #218838 0%, #1e7e34 100%);
    transform: translateY(-5px) scale(1.1) rotate(3deg);
    box-shadow: 
        0 12px 30px rgba(40, 167, 69, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.3);
    animation: suggestionHoverBounce 0.4s ease-in-out;
}

@keyframes suggestionHoverBounce {
    0%, 100% { transform: translateY(-5px) scale(1.1) rotate(3deg); }
    50% { transform: translateY(-8px) scale(1.15) rotate(-1deg); }
}

.suggestion-button:active {
    transform: translateY(-2px) scale(1.05) rotate(1deg);
    transition: all 0.1s ease;
}

.enum-button {
    background: linear-gradient(135deg, #6f42c1 0%, #6610f2 100%);
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 25px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 
        0 4px 15px rgba(111, 66, 193, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
    outline: none;
    position: relative;
    overflow: hidden;
    animation: buttonPopIn 0.5s ease-out forwards;
    animation-delay: calc(var(--delay, 0) * 0.1s);
    opacity: 0;
    transform: scale(0.8) translateY(20px);
}

.enum-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.6s;
}

.enum-button:hover::before {
    left: 100%;
}

.enum-button:hover {
    background: linear-gradient(135deg, #5a2d91 0%, #5a23c8 100%);
    transform: translateY(-5px) scale(1.1) rotate(-3deg);
    box-shadow: 
        0 12px 30px rgba(111, 66, 193, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.3);
    animation: enumHoverBounce 0.4s ease-in-out;
}

@keyframes enumHoverBounce {
    0%, 100% { transform: translateY(-5px) scale(1.1) rotate(-3deg); }
    50% { transform: translateY(-8px) scale(1.15) rotate(1deg); }
}

.enum-button:active {
    transform: translateY(-2px) scale(1.05) rotate(-1deg);
    transition: all 0.1s ease;
}

/* Static form container - no animations */
.form-container {
    height: 600px;
    overflow-y: auto;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    scrollbar-width: thin;
    scrollbar-color: #333 transparent;
}

.form-container::-webkit-scrollbar {
    width: 8px;
}

.form-container::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
}

.form-container::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #333 0%, #555 100%);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.form-container::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #444 0%, #666 100%);
}

/* Static form elements - no animations */
.stTextInput > div > div > input {
    background: rgba(10, 10, 10, 0.9) !important;
    color: #ffffff !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    box-shadow: 
        0 4px 15px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.stTextInput > div > div > input:focus {
    border-color: #0084ff !important;
    box-shadow: 
        0 0 0 3px rgba(0, 132, 255, 0.1),
        0 6px 20px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

.stTextInput > div > div > input[value]:not([value=""]) {
    background: linear-gradient(135deg, #0066cc 0%, #0084ff 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: 
        0 6px 20px rgba(0, 132, 255, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

.stSelectbox > div > div > div {
    background: rgba(10, 10, 10, 0.9) !important;
    color: #ffffff !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    box-shadow: 
        0 4px 15px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.stCheckbox > label {
    color: #ffffff !important;
}

.stNumberInput > div > div > input {
    background: rgba(10, 10, 10, 0.9) !important;
    color: #ffffff !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    box-shadow: 
        0 4px 15px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.stNumberInput > div > div > input:focus {
    border-color: #0084ff !important;
    box-shadow: 
        0 0 0 3px rgba(0, 132, 255, 0.1),
        0 6px 20px rgba(0, 0, 0, 0.5) !important;
}

.stNumberInput > div > div > input[value]:not([value="0"]) {
    background: linear-gradient(135deg, #0066cc 0%, #0084ff 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: 
        0 6px 20px rgba(0, 132, 255, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

/* Static expanders - no animations */
.stExpander {
    background: rgba(10, 10, 10, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 15px !important;
    box-shadow: 
        0 6px 20px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    margin: 10px 0 !important;
}

.stExpander > div {
    background: transparent !important;
}

/* Headers styling */
h1, h2, h3 {
    color: #ffffff !important;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;
    animation: fadeInDown 0.6s ease-out !important;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Static buttons - no hover animations */
.stButton > button {
    background: linear-gradient(135deg, #0084ff 0%, #0066cc 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    box-shadow: 
        0 6px 20px rgba(0, 132, 255, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

/* Override all white backgrounds */
div[data-testid="stVerticalBlock"] {
    background: transparent !important;
}

div[data-testid="column"] {
    background: transparent !important;
}

/* Next field highlighting - static */
.last-updated-field {
    animation: pulseNextField 3s ease-in-out infinite;
    border: 3px solid #28a745 !important;
    border-radius: 15px !important;
    background: rgba(40, 167, 69, 0.1) !important;
    box-shadow: 
        0 0 20px rgba(40, 167, 69, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    padding: 12px !important;
    margin: 8px 0 !important;
}

@keyframes pulseNextField {
    0% {
        border-color: #28a745;
        box-shadow: 0 0 20px rgba(40, 167, 69, 0.4);
        background-color: rgba(40, 167, 69, 0.1);
    }
    50% {
        border-color: #20c997;
        box-shadow: 0 0 30px rgba(40, 167, 69, 0.7);
        background-color: rgba(40, 167, 69, 0.2);
    }
    100% {
        border-color: #28a745;
        box-shadow: 0 0 20px rgba(40, 167, 69, 0.4);
        background-color: rgba(40, 167, 69, 0.1);
    }
}

/* Alert boxes - static */
div[data-testid="stAlert"] {
    border-radius: 15px !important;
    box-shadow: 
        0 6px 20px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    animation: slideInDown 0.4s ease-out !important;
}

@keyframes slideInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Success messages - static */
div[data-testid="stSuccess"] {
    background: linear-gradient(135deg, rgba(40, 167, 69, 0.2) 0%, rgba(32, 201, 151, 0.2) 100%) !important;
    border: 1px solid rgba(40, 167, 69, 0.3) !important;
    color: #28a745 !important;
    animation: successPulse 0.6s ease-out !important;
}

@keyframes successPulse {
    0% { transform: scale(0.95); opacity: 0; }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); opacity: 1; }
}

/* Chat input enhancement */
div[data-testid="stChatInput"] > div {
    background: rgba(0, 0, 0, 0.9) !important;
    border-radius: 15px !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 
        0 6px 20px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stChatInput"] > div:focus-within {
    border-color: #0084ff !important;
    box-shadow: 
        0 0 0 3px rgba(0, 132, 255, 0.1),
        0 8px 25px rgba(0, 0, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    transform: translateY(-2px) !important;
}
</style>
""", unsafe_allow_html=True)

# Session state for chat history and form
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "form_snapshot" not in st.session_state and "session_data" in st.session_state:
    st.session_state.form_snapshot = json.loads(json.dumps(st.session_state.session_data.data))
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
if not st.session_state.greeted and "session_data" in st.session_state:
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
        st.text_input(label, value=value or "", disabled=True, key=field_id)
    
    elif field_type == "boolean":
        label = f"{indent}{description}" + (" *" if is_required else "")
        st.checkbox(label, value=bool(value), disabled=True, key=field_id)
    
    elif field_type == "date":
        label = f"{indent}{description}" + (" *" if is_required else "")
        if value:
            st.text_input(label, value=str(value), disabled=True, key=field_id)
        else:
            st.text_input(label, value="", placeholder="DD-MM-YYYY", disabled=True, key=field_id)
    
    elif field_type == "integer":
        label = f"{indent}{description}" + (" *" if is_required else "")
        # Convert to float for st.number_input compatibility, handle empty strings and invalid values
        try:
            number_value = float(value) if value is not None and value != '' else 0.0
        except (ValueError, TypeError):
            number_value = 0.0
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
            processed_message = loop.run_until_complete(language_processor(st.session_state.session_data, st.session_state.current_user_message))
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
            json_response = loop.run_until_complete(json_agent(st.session_state.session_data, st.session_state.processed_data))
            loop.close()

            st.session_state.form_snapshot = json.loads(json.dumps(st.session_state.session_data.data))

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
                st.session_state.validation_tries = 5

            processed_data = st.session_state.processed_data
            if isinstance(processed_data, dict) and processed_data.get('command_type', '') != 'find':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                validation_response = loop.run_until_complete(validation_agent(st.session_state.session_data))
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
                        st.session_state.validation_tries = 5  # Reset for next time
                        st.session_state.processing_step = 5  # Proceed to reply anyway
                        st.rerun()
                else:
                    st.session_state.processing_message = "✅ Validation passed"
                    st.session_state.validation_tries = 5  # Reset for next time

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
            reply_response = loop.run_until_complete(reply_agent(st.session_state.session_data, st.session_state.json_response))
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
            st.session_state.form_snapshot = json.loads(json.dumps(st.session_state.session_data.data))
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

# Add a reset button at the top right corner
col_spacer, col_reset = st.columns([10, 1])
with col_reset:
    if st.button('Reset', key='reset_all', help='Reset form, chat, and logs'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Clear the live logs as well
        from main import LIVE_LOGS
        LIVE_LOGS.clear()
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
                    
                    # Show suggestions first
                    if suggestions:
                        with st.container():
                            st.write("**💡 Smart Suggestions:**")
                            
                            # Display suggestions
                            suggestion_list = [s for s in suggestions if s]
                            if suggestion_list:
                                num_suggestions = len(suggestion_list)
                                if num_suggestions <= 2:
                                    cols = st.columns(num_suggestions)
                                elif num_suggestions <= 4:
                                    cols = st.columns(2)
                                else:
                                    cols = st.columns(3)
                                
                                for idx, suggestion in enumerate(suggestion_list):
                                    col_idx = idx % len(cols)
                                    with cols[col_idx]:
                                        button_label = f"💡 {suggestion}"
                                        if st.button(button_label, key=f"suggestion_{i}_{idx}_{suggestion}", use_container_width=True):
                                            st.session_state.suggestion_clicked = suggestion
                                            st.rerun()
                    
                    # Show enums second
                    if enums:
                        with st.container():
                            st.write("**🔘 Available Options:**")
                            
                            # Display enums
                            enum_list = [e for e in enums if e]
                            if enum_list:
                                num_enums = len(enum_list)
                                if num_enums <= 2:
                                    cols = st.columns(num_enums)
                                elif num_enums <= 4:
                                    cols = st.columns(2)
                                else:
                                    cols = st.columns(3)
                                
                                for idx, enum_val in enumerate(enum_list):
                                    col_idx = idx % len(cols)
                                    with cols[col_idx]:
                                        button_label = f"🔘 {enum_val}"
                                        if st.button(button_label, key=f"enum_{i}_{idx}_{enum_val}", use_container_width=True):
                                            st.session_state.suggestion_clicked = enum_val
                                            st.rerun()
        
        # Show detailed processing indicator
        if st.session_state.is_typing:
            with st.chat_message("assistant"):
                # Current status
                st.write(f"**{st.session_state.processing_message}**")
    
    # Chat input
    if "session_data" in st.session_state and next_field(st.session_state.session_data.data) is not None:
        user_input = st.chat_input("Type your message and press Enter...")
    else:
        st.success("🎉 Thank you! All required fields are completed.")
        user_input = None

with col2:
    st.subheader("📋 Form Data")
    
    # Create a scrollable container for form data that takes full height
    with st.container(height=750):  # Large height to use most of screen space
        # Add scroll trigger point for next field
        if st.session_state.focus_next_field and next_field(st.session_state.form_snapshot):
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
                        // 1) Inject <style> (once) with both the pulsing and fade-out animations.
                        const parentHead = window.parent.document.head;
                        if (parentHead && !window.parent.document.getElementById('pulse-highlight-styles')) {{
                            const styleTag = window.parent.document.createElement('style');
                            styleTag.id = 'pulse-highlight-styles';
                            styleTag.innerHTML = `
                                /* --------------- PULSING GLOW --------------- */
                                @keyframes pulseHighlight {{
                                    0%   {{ box-shadow: 0 0 5px rgba(40,167,69,0.5); }}
                                    50%  {{ box-shadow: 0 0 20px rgba(40,167,69,0.8); }}
                                    100% {{ box-shadow: 0 0 5px rgba(40,167,69,0.5); }}
                                }}

                                .pulse-highlight {{
                                    border: 3px solid #28a745;
                                    border-radius: 7px;
                                    background-color: rgba(40, 167, 69, 0.1);
                                    animation: pulseHighlight 2s ease-in-out infinite;
                                }}

                                /* --------------- FADE OUT --------------- */
                                .fade-out {{
                                    transition: all 1s ease-out;
                                    border: 0 solid transparent !important;
                                    background-color: transparent !important;
                                    box-shadow: none !important;
                                    opacity: 0;
                                }}
                            `;
                            parentHead.appendChild(styleTag);
                        }}

                        // 2) Wait a bit so Streamlit finishes rendering.
                        setTimeout(function() {{
                            const parentDoc = window.parent.document;
                            let foundElement = null;

                            // 2A) Look for a <label> containing the next-field description
                            const labels = parentDoc.querySelectorAll('label');
                            for (let lbl of labels) {{
                                if (lbl.textContent && lbl.textContent.includes('{next_field_desc}')) {{
                                    // Grab the Streamlit container for that label
                                    foundElement = lbl.closest('[data-testid^="st"]') || lbl.parentElement;
                                    break;
                                }}
                            }}

                            // 2B) Fallback: if no matching label, search for an alert/info box with "NEXT:"
                            if (!foundElement) {{
                                const infoBoxes = parentDoc.querySelectorAll('[data-testid="stAlert"]');
                                for (let box of infoBoxes) {{
                                    if (box.textContent && box.textContent.includes('NEXT:')) {{
                                        foundElement = box;
                                        break;
                                    }}
                                }}
                            }}

                            if (foundElement) {{
                                // 3) Compute which element to highlight: the next sibling if it exists,
                                //    otherwise fall back to the foundElement itself.
                                let highlightEl = foundElement.nextElementSibling || foundElement;

                                // 4) Scroll highlightEl into view if it's not fully visible
                                const rect = highlightEl.getBoundingClientRect();
                                const parentHeight = window.parent.innerHeight;
                                const isFullyVisible = rect.top >= 0 && rect.bottom <= parentHeight;

                                if (!isFullyVisible) {{
                                    highlightEl.scrollIntoView({{
                                        behavior: 'smooth',
                                        block: 'center'
                                    }});
                                }}

                                // 5) Add pulsing highlight
                                highlightEl.classList.add('pulse-highlight');

                                // 6) After 4 seconds, remove pulsing and start fade-out
                                setTimeout(() => {{
                                    highlightEl.classList.remove('pulse-highlight');
                                    highlightEl.classList.add('fade-out');

                                    // 7) Once fade-out (1s) completes, remove the fade-out class
                                    setTimeout(() => {{
                                        highlightEl.classList.remove('fade-out');
                                    }}, 1000);

                                }}, 4000);
                            }}
                        }}, 1500);
                    }}
                }} catch (e) {{
                    // Silent failure
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