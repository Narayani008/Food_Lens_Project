import streamlit as st
import requests
import base64
from pymongo import MongoClient
from datetime import datetime
from openai_utils import ask_openai
import pandas as pd
st.set_page_config(
    page_title="FreshLens –",
    layout="wide"
)
if "prediction_done" not in st.session_state:
    st.session_state.prediction_done = False
if "mongo_id" not in st.session_state:
    st.session_state.mongo_id = None
def calculate_carbon_footprint(distance, transport):
    factors = {
        "Truck": 0.12,
        "Train": 0.04,
        "Air": 0.60,
        "Other": 0.15
    }
    return round(distance * factors.get(transport, 0.15), 2)
def calculate_water_footprint(temp, humidity):
    base_water = 500
    return round(base_water * (temp / 20) * (humidity / 50), 2)
def calculate_energy_usage(distance, temp):
    base_energy = distance * 0.02
    storage_energy = 5 if temp > 20 else 2
    return round(base_energy + storage_energy, 2)
def calculate_food_waste_risk(distance, temp, confidence):
    risk = (distance / 10) + (temp * 2) + (100 - confidence * 10)
    return min(100, round(risk, 2))
def set_bg(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0b1c2d, #142f43, #1f4b63);
        }}

        section[data-testid="stSidebar"] * {{
            color: white !important;
            font-weight: 800 !important;
            font-size: 16px !important;
        }}

        h1, h2, h3, p, label {{
            color: white !important;
        }}

        .stButton button {{
            border: 2px solid white;
            background: transparent;
            color: white;
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
set_bg("background_img.png")
client = MongoClient(
    "mongodb+srv://Coding_user:code2222@cluster0.pt3uwk6.mongodb.net/foodlens_db"
)
db = client["foodlens_db"]
collection = db["food_data"]
st.sidebar.title("Navigation")
pages = ["Home"]
if st.session_state.prediction_done:
    pages += [
        "Supply Chain Impact",
        "Environmental Effects",
        "Farmer Produce Standardization Score",
        "Personal Nutritional Analysis"
    ]
else:
    pages += [
        "Locked: Supply Chain Impact",
        "Locked: Environmental Effects",
        "Locked: Farmer Produce Standardization Score",
        "Locked: Personal Nutritional Analysis"
    ]

page = st.sidebar.radio("Go to", pages)

# ---------------- HOME PAGE ----------------
if page == "Home":
    st.markdown("<h1 style='text-align:center;'>FreshLens</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'> Freshness at your fingertips.Measuring freshness, reducing waste, sustaining tomorrow</p>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Metadata for shelf-life analysis")
    with st.form("metadata_form"):
        harvest_date = st.date_input("Harvest Date")
        purchase_date = st.date_input("Purchase Date")
        storage_temp = st.number_input("Storage Temperature (°C)", value=25.0)
        storage_humidity = st.number_input("Storage Humidity (%)", value=60.0)
        transport_type = st.selectbox("Transport Type", ["Truck", "Train", "Air", "Other"])
        distance_travelled = st.number_input("Distance Travelled (km)", value=0.0)
        submit = st.form_submit_button("Submit Metadata")
    if submit:
        record = {
            "harvest_date": str(harvest_date),
            "purchase_date": str(purchase_date),
            "storage_temp": storage_temp,
            "storage_humidity": storage_humidity,
            "transport_type": transport_type,
            "distance_travelled": distance_travelled,
            "timestamp": datetime.utcnow()
        }
        st.session_state.mongo_id = collection.insert_one(record).inserted_id
        st.success("Metadata stored successfully")
    st.markdown("</div>", unsafe_allow_html=True)
    if st.session_state.mongo_id:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Upload Food Image")
        file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
        if file:
            st.image(file, use_container_width=True)
            if st.button("Analyze"):
                response = requests.post(
                    "http://127.0.0.1:8000/predict",
                    files={"file": file}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.prediction_done = True
                    carbon = calculate_carbon_footprint(distance_travelled, transport_type)
                    water = calculate_water_footprint(storage_temp, storage_humidity)
                    energy = calculate_energy_usage(distance_travelled, storage_temp)
                    waste_risk = calculate_food_waste_risk(distance_travelled, storage_temp, data["confidence"])
                    collection.update_one(
                        {"_id": st.session_state.mongo_id},
                        {"$set": {
                            **data,
                            "carbon_kg_co2": carbon,
                            "water_liters": water,
                            "energy_kwh": energy,
                            "food_waste_risk": waste_risk
                        }}
                    )
                    st.success(f"Prediction: {data['prediction']}")
                    st.info(f"Confidence: {data['confidence']}")
        st.markdown("</div>", unsafe_allow_html=True)
elif page == "Supply Chain Impact":
    record = collection.find_one({"_id": st.session_state.mongo_id})
    st.header("Supply Chain Impact")
    st.write(
        ask_openai(
            f"Briefly analyze supply chain risk for food transported via "
            f"{record['transport_type']} over {record['distance_travelled']} km."
        )
    )
    risk_score = min(100, record["distance_travelled"] / 10 + record["storage_temp"] * 2)
    st.progress(int(risk_score))
elif page == "Environmental Effects":
    record = collection.find_one({"_id": st.session_state.mongo_id})
    st.header("Environmental Sustainability")
    st.write(
        ask_openai(
            "Explain how food spoilage affects carbon emissions and water usage in two lines."
        )
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Carbon Footprint (kg CO₂)", record["carbon_kg_co2"])
    col2.metric("Water Footprint (liters)", record["water_liters"])
    col3.metric("Energy Usage (kWh)", record["energy_kwh"])
    df = pd.DataFrame({
        "Metric": ["Carbon", "Water", "Energy"],
        "Impact": [
            record["carbon_kg_co2"],
            record["water_liters"],
            record["energy_kwh"]
        ]
    })
    st.bar_chart(df.set_index("Metric"))
    st.progress(int(record["food_waste_risk"]))
elif page == "Farmer Produce Standardization Score":
    record = collection.find_one({"_id": st.session_state.mongo_id})
    score = max(0, 100 - abs(record["storage_temp"] - 20) * 2)
    st.header("Farmer Produce Quality Score")
    st.metric("Standardization Score", f"{int(score)} / 100")
    st.write(
        ask_openai("Explain how proper storage improves farmer income and grading.")
    )
elif page == "Personal Nutritional Analysis":
    record = collection.find_one({"_id": st.session_state.mongo_id})
    retention = record["confidence"] * 10
    st.header("Nutritional Impact")
    st.metric("Nutrient Retention (%)", f"{retention:.1f}")
    st.write(
        ask_openai(
            f"Give brief nutrition advice for food predicted as {record['prediction']}."
        )
    )
elif "Locked" in page:
    st.warning("Please complete food analysis on Home page to unlock this section.")
