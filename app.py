import streamlit as st
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
st.set_page_config(layout="wide")
st_autorefresh(interval=1000, key="refresh")
st.markdown("""
<style>
body {background:#0e1117;}
.card {background:#1c1f26;padding:20px;border-radius:15px;text-align:center;color:white;}
.green {color:#00ff00;font-weight:bold;}
.red {color:#ff4c4c;font-weight:bold;}
.big {font-size:22px;font-weight:bold;}
</style>
""", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;color:white;'>🚦 SLUTO – Self-Learning Urban Traffic Optimizer (Advanced)</h1>", unsafe_allow_html=True)
# -------------------------
# TRAFFIC MODE
# -------------------------
mode = st.sidebar.selectbox("Traffic Mode", ["Normal", "Rush Hour", "Night Mode"])
def get_arrival(mode):
    if mode == "Normal":
        return np.random.randint(1,4)
    if mode == "Rush Hour":
        return np.random.randint(3,8)
    if mode == "Night Mode":
        return np.random.randint(0,2)
MAX_CAPACITY = 300
BASE_GREEN = 6
SERVICE_BASE = 5
HORIZON = 5

# -------------------------
# SESSION STATE
# -------------------------
if "queue" not in st.session_state:
    st.session_state.queue = {"N":20,"S":15,"E":18,"W":10}

if "queue_fixed" not in st.session_state:
    st.session_state.queue_fixed = {"N":20,"S":15,"E":18,"W":10}

if "waiting" not in st.session_state:
    st.session_state.waiting = {"N":0,"S":0,"E":0,"W":0}

if "active_lane" not in st.session_state:
    st.session_state.active_lane = "N"

if "timer" not in st.session_state:
    st.session_state.timer = BASE_GREEN

if "passed" not in st.session_state:
    st.session_state.passed = 0

if "passed_fixed" not in st.session_state:
    st.session_state.passed_fixed = 0

if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------
# ARRIVAL LOGIC
# -------------------------
for lane in st.session_state.queue:
    arrivals = get_arrival(mode)

    if st.session_state.queue[lane] < MAX_CAPACITY:
        st.session_state.queue[lane] += arrivals
        st.session_state.queue_fixed[lane] += arrivals

# -------------------------
# FIXED CONTROLLER (Baseline)
# -------------------------
fixed_lane = max(st.session_state.queue_fixed, key=st.session_state.queue_fixed.get)
cleared_fixed = min(SERVICE_BASE, st.session_state.queue_fixed[fixed_lane])
st.session_state.queue_fixed[fixed_lane] -= cleared_fixed
st.session_state.passed_fixed += cleared_fixed

# -------------------------
# ADAPTIVE CONTROLLER
# -------------------------
if st.session_state.timer <= 0:

    # Predictive priority
    predicted = {
        lane: st.session_state.queue[lane] + get_arrival(mode)*HORIZON
        for lane in st.session_state.queue
    }

    st.session_state.active_lane = max(predicted, key=predicted.get)

    total_q = sum(st.session_state.queue.values())
    ratio = st.session_state.queue[st.session_state.active_lane] / (total_q + 1)
    green = BASE_GREEN + int(20 * ratio)

    st.session_state.timer = max(5, min(green, 30))

# -------------------------
# SERVICE LOGIC (Adaptive)
# -------------------------
for lane in st.session_state.queue:

    if lane == st.session_state.active_lane:

        # congestion boost
        if st.session_state.queue[lane] > 200:
            service = 10
        else:
            service = SERVICE_BASE

        cleared = min(service, st.session_state.queue[lane])
        st.session_state.queue[lane] -= cleared
        st.session_state.passed += cleared
        st.session_state.waiting[lane] = 0
    else:
        st.session_state.waiting[lane] += 1

st.session_state.timer -= 1

# Save stability history
total_queue = sum(st.session_state.queue.values())
st.session_state.history.append(total_queue)

# -------------------------
# DISPLAY SIGNALS
# -------------------------
st.markdown("---")
cols = st.columns(4)

for i, lane in enumerate(["N","S","E","W"]):
    signal = "<span class='green'>🟢 GREEN</span>" if lane == st.session_state.active_lane else "<span class='red'>🔴 RED</span>"

    with cols[i]:
        st.markdown(f"""
        <div class='card'>
        <div class='big'>Lane {lane}</div>
        Signal: {signal}<br><br>
        Queue: {st.session_state.queue[lane]}<br>
        Waiting: {st.session_state.waiting[lane]} sec
        </div>
        """, unsafe_allow_html=True)

# -------------------------
# CONTROLLER COMPARISON
# -------------------------
st.markdown("---")
st.subheader("⚖ Controller Performance Comparison")

col1, col2 = st.columns(2)

col1.metric("Adaptive Vehicles Passed", st.session_state.passed)
col1.metric("Adaptive Total Queue", total_queue)

col2.metric("Fixed Vehicles Passed", st.session_state.passed_fixed)
col2.metric("Fixed Total Queue", sum(st.session_state.queue_fixed.values()))

# -------------------------
# NETWORK HEALTH
# -------------------------
st.markdown("---")
st.subheader("📊 Network Stability")

stability = 1 - (total_queue / MAX_CAPACITY)
st.metric("Network Stability Score", round(stability,2))

# -------------------------
# PREDICTION GRAPH
# -------------------------
st.markdown("---")
st.subheader("📈 Queue Prediction (Next 10 Steps)")

future = []
temp = total_queue

for _ in range(10):
    temp += get_arrival(mode)
    temp -= SERVICE_BASE
    future.append(max(temp,0))

fig = go.Figure()
fig.add_trace(go.Scatter(y=future, mode="lines", name="Predicted Queue"))
fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# STABILITY TREND
# -------------------------
st.markdown("---")
st.subheader("📉 Stability Trend")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(y=st.session_state.history, mode="lines", name="Total Queue"))
fig2.update_layout(template="plotly_dark")

st.plotly_chart(fig2, use_container_width=True)
