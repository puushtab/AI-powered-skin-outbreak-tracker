# AI-powered-skin-outbreak-tracker
AI-powered system that helps users better understand and manage their skin outbreaks 

## Backend 

### Authentication

Before running the code, you must export your Hugging Face access token as an environment variable so that the `from_pretrained` calls can authenticate:

```bash
# macOS/Linux (bash or zsh)
export HF_TOKEN="your_hf_access_token"

# Windows PowerShell
setx HF_TOKEN "your_hf_access_token"
