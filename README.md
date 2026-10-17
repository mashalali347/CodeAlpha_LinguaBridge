# CodeAlpha_LinguaBridge

A language translation app built for the CodeAlpha AI internship (Task 1), using Python and Streamlit. Also known as LinguaBridge.

## Features
- Enter text and choose the source and target languages (25 languages, plus language detection)
- Translation through the MyMemory translation API, with Google Translate as a backup
- Voice input: speak into the microphone and the text is typed and translated for you
- Text-to-speech (Listen) for the original and translated text
- Copy button for the translated text
- Swap languages, clear text, and a character counter
- Other translation suggestions
- History, saved translations, and search
- Dark navy interface

## Run locally
pip install -r requirements.txt
python -m streamlit run app.py

## Built with
Python, Streamlit, requests, deep-translator, gTTS, SpeechRecognition