import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile
import re

st.title("Transcription Audio en SRT")

def format_time(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def transcribe_audio(audio_file_path):
    # Charger le fichier audio
    audio = AudioSegment.from_file(audio_file_path)

    # Créer un fichier temporaire WAV
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_path = temp_audio_file.name
        audio.export(temp_audio_path, format="wav")

    # Initialiser le recognizer
    recognizer = sr.Recognizer()

    # Charger le fichier audio temporaire
    audio_file = sr.AudioFile(temp_audio_path)

    # Lire le fichier audio et transcrire
    with audio_file as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="fr-FR")
        except sr.UnknownValueError:
            st.error("Google Web Speech API could not understand the audio")
            text = ""
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Web Speech API; {e}")
            text = ""

    # Segmenter le texte en phrases
    sentences = re.split(r'(?<=[.!?])\s+', text) if text else [""]
    duration_ms = len(audio)
    # Attribuer un temps proportionnel à chaque phrase
    time_per_sentence = duration_ms / max(1, len(sentences)) # Éviter la division par zéro

    # Générer le contenu SRT
    srt_content = ""
    start_time_ms = 0
    for i, sentence in enumerate(sentences, 1):
        end_time_ms = start_time_ms + time_per_sentence
        start_time = format_time(int(start_time_ms))
        end_time = format_time(int(end_time_ms))
        srt_content += f"{i}\n{start_time} --> {end_time}\n{sentence}\n\n"
        start_time_ms = end_time_ms  # Le temps de début de la prochaine phrase est le temps de fin actuel

    # Supprimer le fichier WAV temporaire
    os.remove(temp_audio_path)

    return srt_content

# Interface Streamlit pour télécharger un fichier audio
uploaded_file = st.file_uploader("Choisissez un fichier audio", type=["mp3", "mp4", "wav"])

if uploaded_file is not None:
    # Sauvegarder le fichier téléchargé temporairement
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    # Transcrire l'audio
    srt_content = transcribe_audio(temp_file_path)

    # Afficher la transcription
    st.subheader("Transcription")
    st.text(srt_content)

    # Fournir un bouton pour télécharger le fichier SRT
    st.download_button(
        label="Télécharger la transcription SRT",
        data=srt_content,
        file_name="transcription.srt",
        mime="text/plain"
    )

    # Supprimer le fichier temporaire
    os.remove(temp_file_path)
