import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px

st.title("Dashboard de Noticias")

def load_data():
    try:
        return pd.read_json("scraped_summaries.jsonl", lines=True)
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None

data = load_data()

if data is not None:
    st.subheader("Vista previa de datos")
    st.dataframe(data.head())

    st.subheader("Distribución de vocales en los títulos")

    def count_vowels(df):
        counts = {v: 0 for v in "aeiou"}
        for title in df["title"]:
            t = str(title).lower()
            for v in counts:
                counts[v] += t.count(v)
        return counts

    vowel_counts = count_vowels(data)
    st.write("Valores usados para la distribución de vocales:")
    vowel_df = pd.DataFrame(vowel_counts.items(), columns=["Vocal", "Cantidad"])

    plt.figure(figsize=(6,4))
    plt.bar(vowel_df["Vocal"], vowel_df["Cantidad"])
    plt.xlabel("Vocal")
    plt.ylabel("Cantidad")
    plt.title("Distribución de vocales en los títulos")
    st.pyplot(plt)

    st.subheader("Nube de palabras de títulos")
    st.write("Primeros 300 caracteres usados para nube de palabras:")
    all_titles = " ".join(data["title"])
    st.code(all_titles[:300])

    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_titles)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)

    st.subheader("Scatter: largo del título vs largo del link")

    data["title_length"] = data["title"].apply(lambda x: len(str(x)))
    data["link_length"] = data["link"].apply(lambda x: len(str(x)))

    fig, ax = plt.subplots()
    ax.scatter(data["title_length"], data["link_length"])
    ax.set_xlabel("Largo del título")
    ax.set_ylabel("Largo del link")
    ax.set_title("Scatter: largo del título vs largo del link")
    st.pyplot(fig)

else:
    st.warning("No se pudieron cargar los datos.")