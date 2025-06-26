import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile

st.title("Transcription Audio en SRT et Édition Manuel")

def transcribe_audio(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_path = temp_audio_file.name
        audio.export(temp_audio_path, format="wav")

    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(temp_audio_path)

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

    os.remove(temp_audio_path)
    return text

def generate_srt_content(subtitles):
    srt_content = ""
    for idx, sub in enumerate(subtitles, start=1):
        srt_content += f"{idx}\n{sub['start_time']} --> {sub['end_time']}\n{sub['text']}\n\n"
    return srt_content

def main():
    uploaded_file = st.file_uploader("Choisissez un fichier audio", type=["mp3", "mp4", "wav"])

    if uploaded_file is not None:
        # Sauvegarder le fichier téléchargé temporairement
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        # Transcrire l'audio
        transcription_text = transcribe_audio(temp_file_path)
        st.subheader("Transcription")
        st.text(transcription_text)

        # Permettre à l'utilisateur de créer des sous-titres
        st.write("Définissez chaque sous-titre:")

        # Permettre à l'utilisateur de spécifier combien de sous-titres il veut
        num_subtitles = st.number_input("Nombre de sous-titres:", min_value=1, max_value=20, value=1)

        subtitles = []

        for i in range(1, num_subtitles + 1):
            st.write(f"Sous-titre {i}:")
            text = st.text_area(f"Texte du sous-titre {i}:", value=transcription_text if i == 1 else "", key=f"text_{i}")
            start_time = st.text_input(f"Temps de début pour le sous-titre {i} (format: HH:MM:SS,mmm):", key=f"start_{i}", value="00:00:00,000")
            end_time = st.text_input(f"Temps de fin pour le sous-titre {i} (format: HH:MM:SS,mmm):", key=f"end_{i}", value="00:00:05,000")

            subtitles.append({
                'text': text,
                'start_time': start_time,
                'end_time': end_time
            })

        # Générer le contenu SRT
        srt_content = generate_srt_content(subtitles)

        st.subheader("Contenu SRT Généré")
        st.text(srt_content)

        st.download_button(
            label="Télécharger la transcription SRT",
            data=srt_content,
            file_name="transcription_custom.srt",
            mime="text/plain"
        )

        # Supprimer le fichier temporaire
        os.remove(temp_file_path)

if __name__ == "__main__":
    main()
