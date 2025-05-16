import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv

# # Load environment variables from .env file (for local development)
# load_dotenv()

# App title and configuration
st.set_page_config(page_title="Heygen Avatar in Streamlit", layout="wide")
st.title("Heygen Avatar Integration")

# Sidebar for API configuration
with st.sidebar:
    st.header("Heygen API Configuration")
    
    # Get API key from environment variable or user input
    default_api_key = "OTc2YWI1NTQ2MTkzNDJiM2E5ZTMxOTkxN2Y1NDljMGQtMTc0NzM0OTc0Ng=="
    api_key = st.text_input("Heygen API Key", value=default_api_key, type="password")
    
    st.markdown("---")
    st.markdown("### Avatar Settings")
    
    # Avatar selection
    avatar_id = st.selectbox(
        "Select Avatar ID",
        ["6461d4c4cf397b85c58ae66c", "645fc069aeea690ddecaad56", "Custom"],  # Example avatar IDs
        index=0
    )
    
    if avatar_id == "Custom":
        avatar_id = st.text_input("Enter Custom Avatar ID")
    
    # Voice selection
    voice_id = st.selectbox(
        "Select Voice",
        ["female-us-1", "male-us-1", "female-uk-1", "male-uk-1"],
        index=0
    )

# Main content area
st.markdown("## Generate Avatar Video")

# Text input for avatar speech
text_input = st.text_area(
    "Enter text for the avatar to speak:",
    "Hello! I'm an AI avatar integrated into Streamlit using Heygen's API. How can I help you today?",
    height=100
)

# Generate video button
if st.button("Generate Avatar Video") and api_key and avatar_id and text_input:
    with st.spinner("Generating avatar video..."):
        # API endpoint
        url = "https://api.heygen.com/v1/video.generate"
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
        
        # Payload for the API request
        payload = {
            "video_inputs": [
                {
                    "avatar": {
                        "avatar_id": avatar_id,
                        "voice_id": voice_id
                    },
                    "background": {
                        "type": "color",
                        "value": "#ffffff"
                    },
                    "caption": False,
                    "script": {
                        "type": "text",
                        "input": text_input
                    }
                }
            ]
        }
        
        try:
            # Send the request to generate the video
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            # Check response and handle appropriately
            if response.status_code == 200 and "data" in response_data:
                task_id = response_data["data"].get("task_id")
                st.success(f"Video generation initiated. Task ID: {task_id}")
                
                # Poll for video status
                status_url = f"https://api.heygen.com/v1/video.status?task_id={task_id}"
                video_url = None
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(30):  # Try for up to 30 iterations (adjust as needed)
                    status_text.text(f"Checking video status... Attempt {i+1}")
                    status_response = requests.get(status_url, headers=headers)
                    status_data = status_response.json()
                    
                    if "data" in status_data and status_data["data"].get("status") == "completed":
                        video_url = status_data["data"].get("video_url")
                        break
                    
                    progress_bar.progress((i + 1) / 30)
                    time.sleep(2)  # Wait 2 seconds between checks
                
                if video_url:
                    st.success("Video generated successfully!")
                    st.video(video_url)
                    st.markdown(f"**Direct Video URL:** {video_url}")
                else:
                    st.warning("Video generation is taking longer than expected. Please check the Heygen dashboard.")
            else:
                st.error(f"Error: {response_data.get('message', 'Unknown error')}")
                st.json(response_data)
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display sample avatar image
st.markdown("## Sample Avatar")
st.image("https://via.placeholder.com/640x360.png?text=Heygen+Avatar+Preview", 
         caption="Example avatar (placeholder)", 
         use_column_width=True)

# Instructions section
st.markdown("## How to Use")
st.markdown("""
1. Enter your Heygen API key in the sidebar
2. Select an avatar ID and voice
3. Enter the text you want the avatar to speak
4. Click "Generate Avatar Video"
5. Wait for the video to be generated and displayed

**Note:** Video generation typically takes 10-30 seconds, depending on the length of the text and Heygen's current processing load.
""")

# Troubleshooting tips
with st.expander("Troubleshooting Tips"):
    st.markdown("""
    - Make sure your Heygen API key is valid and has not expired
    - Check that the avatar ID exists in your Heygen account
    - Keep text inputs reasonably sized for faster processing
    - If videos fail to generate, check your Heygen dashboard for any account limitations
    - For persistent issues, check the Heygen API documentation or contact their support
    """)

# Footer
st.markdown("---")
st.markdown("Powered by Heygen API & Streamlit | Learn more about [Heygen](https://www.heygen.com)")