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

def ms_to_time(ms):
    seconds = ms // 1000
    ms = ms % 1000
    minutes = seconds // 60
    seconds = seconds % 60
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

def time_to_ms(time_str):
    hours, minutes, rest = time_str.split(':')
    seconds, milliseconds = rest.split(',')
    total_ms = int(milliseconds) + 1000 * (int(seconds) + 60 * (int(minutes) + 60 * int(hours)))
    return total_ms

def parse_srt_content(srt_content):
    lines = srt_content.strip().split('\n')
    subtitles = []
    current_subtitle = {}
    for line in lines:
        if line.isdigit():
            if current_subtitle:
                subtitles.append(current_subtitle)
            current_subtitle = {'index': int(line)}
        elif '-->' in line:
            start_time_str, end_time_str = line.split(' --> ')
            current_subtitle['start_time'] = start_time_str
            current_subtitle['end_time'] = end_time_str
        elif line.strip():
            current_subtitle['text'] = line.strip()
    if current_subtitle:
        subtitles.append(current_subtitle)
    return subtitles

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

    sentences = re.split(r'(?<=[.!?])\s+', text) if text else [""]
    duration_ms = len(audio)
    time_per_sentence = duration_ms / max(1, len(sentences))

    srt_content = ""
    start_time_ms = 0
    for i, sentence in enumerate(sentences, 1):
        end_time_ms = start_time_ms + time_per_sentence
        start_time = format_time(int(start_time_ms))
        end_time = format_time(int(end_time_ms))
        srt_content += f"{i}\n{start_time} --> {end_time}\n{sentence}\n\n"
        start_time_ms = end_time_ms

    os.remove(temp_audio_path)
    return srt_content

def adjust_srt_content(srt_content):
    subtitles = parse_srt_content(srt_content)
    st.subheader("Ajuster les Sous-titres SRT")

    # Sélection du sous-titre à diviser
    subtitle_indices = [sub['index'] for sub in subtitles]
    selected_index = st.selectbox("Sélectionnez le sous-titre à diviser", subtitle_indices)

    num_splits = st.number_input("Nombre de divisions pour le sous-titre sélectionné", min_value=2, max_value=10, value=2)

    adjusted_subtitles = []

    if selected_index:
        selected_sub = next(sub for sub in subtitles if sub['index'] == selected_index)
        st.write(f"Sous-titre sélectionné {selected_sub['index']}:")
        st.text(selected_sub['text'])

        # Demander à l'utilisateur d'entrer les points de coupure
        cut_points = []
        for i in range(1, num_splits):
            cut_point = st.text_input(f"Point de coupure {i} (indice dans le texte):", key=f"cut_{i}")
            try:
                cut_points.append(int(cut_point))
            except ValueError:
                cut_points.append(None)  # Gérer les erreurs d'entrée ici

        # Demander à l'utilisateur d'entrer les nouveaux timestamps pour chaque segment
        new_subs = []
        last_pos = 0
        start_time = time_to_ms(selected_sub['start_time'])
        end_time = time_to_ms(selected_sub['end_time'])
        duration = end_time - start_time
        split_duration = duration // num_splits

        for i in range(num_splits):
            end_pos = cut_points[i - 1] if i < len(cut_points) else len(selected_sub['text'])
            split_text = selected_sub['text'][last_pos:end_pos].strip()

            split_start_time = ms_to_time(start_time + i * split_duration)
            split_end_time = ms_to_time(start_time + (i + 1) * split_duration)

            new_subs.append({
                'index': len(new_subs) + 1,
                'start_time': split_start_time,
                'end_time': split_end_time,
                'text': split_text
            })
            last_pos = end_pos

        for sub in subtitles:
            if sub['index'] == selected_index:
                adjusted_subtitles.extend(new_subs)
            else:
                adjusted_subtitles.append(sub)
    else:
        adjusted_subtitles = subtitles

    # Générer le contenu SRT
    new_srt_content = ""
    for sub in adjusted_subtitles:
        new_srt_content += f"{sub['index']}\n{sub['start_time']} --> {sub['end_time']}\n{sub['text']}\n\n"

    return new_srt_content

uploaded_file = st.file_uploader("Choisissez un fichier audio", type=["mp3", "mp4", "wav"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    srt_content = transcribe_audio(temp_file_path)
    adjusted_srt_content = adjust_srt_content(srt_content)

    st.subheader("Transcription Ajustée")
    st.text(adjusted_srt_content)

    st.download_button(
        label="Télécharger la transcription SRT ajustée",
        data=adjusted_srt_content,
        file_name="transcription_ajustée.srt",
        mime="text/plain"
    )

    os.remove(temp_file_path)
