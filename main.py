import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "silver_data.csv"
LOG_FILE = "logs.csv"


if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Date", "Nick", "Silver", "Given"])
    df.to_csv(DATA_FILE, index=False)
else:
    df = pd.read_csv(DATA_FILE)

if not os.path.exists(LOG_FILE):
    logs_df = pd.DataFrame(columns=["Time", "User", "Action", "Nick", "Silver"])
    logs_df.to_csv(LOG_FILE, index=False)
else:
    logs_df = pd.read_csv(LOG_FILE)


st.set_page_config(page_title="Silver Manager", page_icon="💰", layout="centered")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

if not st.session_state.authenticated:
    nick = st.text_input("Нік:")
    pwd = st.text_input("Пароль:", type="password")

    if st.button("Увійти"):
        users = st.secrets["database"]["users"]

        if nick in users and pwd == users[nick]:
            st.session_state.authenticated = True
            st.session_state.user = nick

            
            if os.path.exists(LOG_FILE):
                logs_df = pd.read_csv(LOG_FILE)
            else:
                logs_df = pd.DataFrame(columns=["Time", "User", "Action", "Nick", "Silver"])

            new_entry = {
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "User": nick,
                "Action": "Успішний вхід у систему",
                "Nick": "",
                "Silver": ""
            }
            logs_df = pd.concat([logs_df, pd.DataFrame([new_entry])], ignore_index=True)
            logs_df.to_csv(LOG_FILE, index=False)

            st.success(f"✅ Вхід виконано ({nick})")
            st.rerun()
        else:
            st.error("❌ Невірний нік або пароль.")
    st.stop()



def log_action(user, action, nick=None, silver=None):
    entry = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User": user,
        "Action": action,
        "Nick": nick if nick else "",
        "Silver": silver if silver else ""
    }

    logs_df = pd.read_csv(LOG_FILE)
    logs_df = pd.concat([logs_df, pd.DataFrame([entry])], ignore_index=True)
    logs_df.to_csv(LOG_FILE, index=False)

tabs = st.tabs(["💰 Головна", "📊 Статистика", "🧾 Логи"])

with tabs[0]:
    st.write("🔐 Увійшов як:", st.session_state.user)
    st.header("💰 Silver Manager")

    st.sidebar.subheader("📂 Завантажити CSV")
    uploaded_file = st.sidebar.file_uploader("Оберіть файл CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("✅ Файл завантажено та збережено!")
        log_action(st.session_state.user, "Завантажив CSV файл")

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
                    log_action(st.session_state.user, "Додав компенсацію", nick, silver)
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
                log_action(st.session_state.user, "Відмітив як виданого", selected_nick, sum_silver)
                st.success(f"{selected_nick} відмічено як виданого!")
                st.rerun()
        else:
            st.info("🎉 Усі компенсації видані!")

    st.subheader("📋 Поточні компенсації")
    st.dataframe(df.style.format({"Silver": "{:,}"}), use_container_width=True)

    st.subheader("🗑️ Видалити запис")
    if not df.empty:
        df["Label"] = df.apply(lambda row: f"{row['Date']} | {row['Nick']} | {int(row['Silver']):,} silver", axis=1)
        row_to_delete = st.selectbox("Оберіть запис для видалення:", df["Label"].tolist())

        if st.button("Видалити вибраний запис ❌"):
            index_to_delete = df.index[df["Label"] == row_to_delete][0]
            deleted_row = df.loc[index_to_delete]
            df = df.drop(index_to_delete).drop(columns=["Label"])
            df.to_csv(DATA_FILE, index=False)
            log_action(st.session_state.user, "Видалив запис", deleted_row["Nick"], deleted_row["Silver"])
            st.success(f"🗑️ Видалено запис: {deleted_row['Nick']} ({int(deleted_row['Silver']):,} silver)")
            st.rerun()
    else:
        st.info("Немає даних для видалення.")



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



with tabs[2]:
    st.header("🧾 Історія дій користувачів")

    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)
        if not logs.empty:
            logs = logs.sort_values("Time", ascending=False)
            st.dataframe(logs, use_container_width=True)
        else:
            st.info("Поки що немає записів у логах.")
    else:
        st.info("Файл логів ще не створено.")
