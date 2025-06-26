import streamlit as st

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
    try:
        hours, minutes, rest = time_str.split(':')
        seconds, milliseconds = rest.split(',')
        total_ms = int(milliseconds) + 1000 * (int(seconds) + 60 * (int(minutes) + 60 * int(hours)))
        return total_ms
    except:
        return 0

def generate_srt_content(subtitles):
    srt_content = ""
    for idx, sub in enumerate(subtitles, start=1):
        srt_content += f"{idx}\n{sub['start_time']} --> {sub['end_time']}\n{sub['text']}\n\n"
    return srt_content

def main():
    st.title("Créer des Sous-titres SRT Personnalisés")

    # Demander à l'utilisateur d'entrer son texte
    full_text = st.text_area("Entrez votre texte ici:")

    if full_text:
        st.write("Définissez chaque sous-titre:")

        # Permettre à l'utilisateur de spécifier combien de sous-titres il veut
        num_subtitles = st.number_input("Nombre de sous-titres:", min_value=1, max_value=20, value=1)

        subtitles = []

        for i in range(1, num_subtitles + 1):
            st.write(f"Sous-titre {i}:")
            text = st.text_area(f"Texte du sous-titre {i}:", key=f"text_{i}")
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

if __name__ == "__main__":
    main()
