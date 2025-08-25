import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv

# Setup:
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

st.title("🌦️ Simple City Weather")
st.caption("Enter a city and get current conditions via Open Weather.")

# Helper Functions:
def classify_pressure(p: float) -> str:
    if p > 1013.25:
        return "HIGH"
    if p < 1013.25:
        return "LOW"
    return "AVERAGE"

# Caches results for 5 minutes to avoid rate limits:
@st.cache_data(ttl=300)

def fetch_weather(city: str):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    return resp.status_code, data

def get_weather(city: str):
    status, data = fetch_weather(city)
    if status != 200:
        raise ValueError(data.get("message", "Failed to fetch weather."))
    return {
        "name": data["name"],
        "temp_c": float(data["main"]["temp"]),
        "temp_f": round((data["main"]["temp"] * 9/5) + 32, 2),
        "humidity": float(data["main"]["humidity"]),
        "description": data["weather"][0]["description"].capitalize(),
        "pressure": float(data["main"]["pressure"]),
        "hours_of_sun": round((data["sys"]["sunset"] - data["sys"]["sunrise"]) / 3600, 2),
    }

# UI: City Form:
with st.form("city_form"):
    city = st.text_input("What city do you want weather data for?", placeholder="e.g., Raleigh or Raleigh,US")
    submitted = st.form_submit_button("Get Weather")

if submitted:
    if not API_KEY:
        st.error("Missing OPENWEATHER_API_KEY. Add it to your .env or environment.")
    elif not city.strip():
        st.warning("Please type a city.")
    else:
        try:
            with st.spinner("Fetching weather…"):
                st.session_state["weather"] = get_weather(city)  # <-- persist result
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.pop("weather", None)

# Render results if they are there:
if "weather" in st.session_state:
    w = st.session_state["weather"]

    st.subheader(f"📍 {w['name']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("🌡️ Temp (°C)", f"{w['temp_c']:.1f}")
    c2.metric("🌡️ Temp (°F)", f"{w['temp_f']:.1f}")
    c3.metric("💧 Humidity", f"{w['humidity']:.0f}%")
    st.write(f"📝 **Conditions:** {w['description']}")
    st.write(f"☀️ **Daylight:** {w['hours_of_sun']} hours")
    st.write(f"🧭 **Pressure:** {classify_pressure(w['pressure'])} ({w['pressure']:.0f} mbar)")

    # Charts next to each other:
    st.markdown("### 📊 Weather Charts")
    col1, col2, col3 = st.columns(3)

    def mini_bar(label, value, ymin, ymax):
        fig, ax = plt.subplots(figsize=(2.3, 2.3))
        ax.bar([label], [value])
        ax.set_ylim(ymin, ymax)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="x", labelrotation=0)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col1:
        mini_bar("Temp °C", w["temp_c"], 0, max(40, w["temp_c"] + 5))
    with col2:
        mini_bar("Humidity %", w["humidity"], 0, 100)
    with col3:
        mini_bar("Pressure", w["pressure"], 950, 1050)

    # More Data Toggle:
    st.markdown("### More Data?")
    more = st.radio(
        "Do you want to see extra details?",
        options=["No", "Yes"],
        horizontal=True,
        key="more_details_radio",
    )

    if more == "Yes":
        st.success("Here are some extra facts:")
        st.markdown(
            f"- 🌡️ Temp (°F): **{w['temp_f']}**\n"
            f"- ☀️ Hours of Daylight: **{w['hours_of_sun']}**\n"
            f"- 🧭 Pressure: **{classify_pressure(w['pressure'])}** ({w['pressure']:.0f} mbar)"
        )
    else:
        st.info("Okay! Toggle 'Yes' above anytime to see more details.")
else:
    st.info("Submit a city to see weather.")
