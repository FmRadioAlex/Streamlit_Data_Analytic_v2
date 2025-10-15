import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "silver_data.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Date", "Nick", "Silver", "Given"])

st.set_page_config(page_title="Silver Manager", page_icon="💰", layout="centered")

tabs = st.tabs(["💰 Головна", "📊 Статистика"])

with tabs[0]:
    st.header("💰 Silver Manager")
    st.sidebar.subheader("📂 Завантажити CSV")
    uploaded_file = st.sidebar.file_uploader("Оберіть файл CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("✅ Файл завантажено та збережено!")
    with st.sidebar:
        st.subheader("➕ Додати компенсацію")
        with st.form("add_form"):
            nick = st.text_input("Нік")
            silver = st.number_input("Сума Silver", min_value=0, step=10000)
            date_input = st.date_input("Дата", datetime.now().date())
            submitted = st.form_submit_button("Додати")

            if submitted:
                if nick and silver > 0:
                    new_row = {
                        "Date": date_input.strftime("%Y-%m-%d"),
                        "Nick": nick.strip(),
                        "Silver": silver,
                        "Given": False
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success(f"✅ Додано {nick} ({silver:,} silver)")
                else:
                    st.warning("⚠️ Введи нік і суму!")

        st.subheader("✅ Відмітити як виданого")
        not_given = df[df["Given"] == False]

        if not not_given.empty:
            selected_nick = st.selectbox("Оберіть нік", not_given["Nick"].unique())
            sum_silver = not_given[not_given["Nick"] == selected_nick]["Silver"].sum()
            st.write(f"Сума до видачі: **{int(sum_silver):,} silver**")
            if st.button("Видано ✅"):
                df.loc[df["Nick"] == selected_nick, "Given"] = True
                df.to_csv(DATA_FILE, index=False)
                st.success(f"{selected_nick} відмічено як виданого!")
        else:
            st.info("🎉 Усі компенсації видані!")

    st.subheader("📋 Поточні компенсації")
    st.dataframe(df, use_container_width=True)

with tabs[1]:
    st.header("📊 Статистика компенсацій")
    if df.empty:
        st.info("Немає даних для відображення.")
    else:
        total_silver = df["Silver"].sum()
        given_count = df[df["Given"] == True].shape[0]
        not_given_count = df[df["Given"] == False].shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Всього Silver", f"{int(total_silver):,}")
        col2.metric("✅ Видано", given_count)
        col3.metric("⏳ Не видано", not_given_count)

        st.subheader("🏆 Топ отримувачів (за сумою)")
        top_chart = df.groupby("Nick")["Silver"].sum().sort_values(ascending=False).head(10)
        st.bar_chart(top_chart)
