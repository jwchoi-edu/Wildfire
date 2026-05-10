import streamlit as st
import numpy as np
import math
import time

st.set_page_config(page_title="산불 확산 시뮬레이터", layout="wide")

GRID_SIZE = 50
EMPTY, TREE, FIRE, ASH = 0, 1, 2, 3

COLOR_MAP = {
    EMPTY: [131, 103, 72],
    TREE: [120, 160, 46],
    FIRE: [255, 0, 0],
    ASH: [47, 79, 79],
}

if "grid" not in st.session_state:
    st.session_state.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
if "running" not in st.session_state:
    st.session_state.running = False
if "step_count" not in st.session_state:
    st.session_state.step_count = 0
if "applied_density" not in st.session_state:
    st.session_state.applied_density = None
if "frames" not in st.session_state:
    st.session_state.frames = []
if "frame_idx" not in st.session_state:
    st.session_state.frame_idx = 0
if "sim_params" not in st.session_state:
    st.session_state.sim_params = None


def reset_simulation(density_pct: int):
    density = density_pct / 100.0
    st.session_state.grid = np.random.choice(
        [TREE, EMPTY], size=(GRID_SIZE, GRID_SIZE), p=[density, 1 - density]
    )
    center = GRID_SIZE // 2
    st.session_state.grid[center, center] = FIRE

    st.session_state.step_count = 0
    st.session_state.running = False
    st.session_state.applied_density = float(density_pct)

    st.session_state.frames = []
    st.session_state.frame_idx = 0


def calculate_base_probability(temp: int, humidity: int) -> float:
    z = (0.2 * temp) - (0.15 * humidity) - 1.5
    prob = 1 / (1 + math.exp(-z))

    return max(0.001, min(prob, 0.95))


def build_frames(temp: int, humidity: int, wind_speed_val: float, wind_dir_deg: int):
    grid = st.session_state.grid.copy()
    frames = [grid.copy()]

    base_prob = calculate_base_probability(temp, humidity)
    wind_speed = wind_speed_val / 10.0
    wind_angle_rad = math.radians(wind_dir_deg)
    wind_dx = -math.cos(wind_angle_rad)
    wind_dy = math.sin(wind_angle_rad)

    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    step = 0
    MAX_STEPS = 1000

    with st.spinner("🔥 시뮬레이션 경로를 미리 계산 중입니다..."):
        while np.any(grid == FIRE) and step < MAX_STEPS:
            new_grid = grid.copy()
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if grid[r, c] == FIRE:
                        new_grid[r, c] = ASH
                    elif grid[r, c] == TREE:
                        for dr, dc in neighbors:
                            nr, nc = r + dr, c + dc
                            if (
                                0 <= nr < GRID_SIZE
                                and 0 <= nc < GRID_SIZE
                                and grid[nr, nc] == FIRE
                            ):
                                prob = base_prob
                                dist = math.hypot(-dc, -dr)
                                spread_dx = -dc / dist
                                spread_dy = -dr / dist

                                dot_product = (spread_dx * wind_dx) + (
                                    spread_dy * wind_dy
                                )

                                prob += (
                                    (1 if dot_product > 0 else 0.2)
                                    * wind_speed
                                    * dot_product
                                )

                                if np.random.rand() < prob:
                                    new_grid[r, c] = FIRE
                                    break
            grid = new_grid.copy()
            frames.append(grid.copy())
            step += 1

    st.session_state.frames = frames
    st.session_state.frame_idx = 0
    st.session_state.sim_params = (temp, humidity, wind_speed_val, wind_dir_deg)


st.title("🌲 산불 확산 시뮬레이터")

st.sidebar.header("⚙️ 환경 설정")
density = st.sidebar.slider("식생 밀도 (%)", 0, 100, 80, 1)
st.sidebar.divider()
temp = st.sidebar.slider("온도 (°C)", -20, 50, 25, 1)
humidity = st.sidebar.slider("습도 (%)", 0, 100, 30, 1)
base_prob_pct = calculate_base_probability(temp, humidity) * 100
st.sidebar.caption(f"계산된 발화 확률: {base_prob_pct:.1f}%")
st.sidebar.divider()
wind_speed = st.sidebar.slider("풍속 (가중치)", 0.0, 10.0, 3.0, 0.1)
wind_dir = st.sidebar.slider("풍향 (각도°)", 0, 360, 0, 1)
st.sidebar.caption("0°: 동풍, 90°: 북풍, 180°: 서풍, 270°: 남풍")
st.sidebar.divider()
delay = st.sidebar.slider("진행 속도 (초/step)", 0.05, 2.0, 0.1, 0.05)

current_params = (temp, humidity, wind_speed, wind_dir)
if st.session_state.sim_params != current_params:
    st.session_state.frames = []
    st.session_state.frame_idx = 0
    st.session_state.sim_params = current_params

if (
    st.session_state.applied_density is None
    or st.session_state.applied_density != float(density)
):
    reset_simulation(density)

reset, run, indicator = st.columns([1, 1, 3])

with reset:
    if st.button("🔄 초기화", width="stretch"):
        reset_simulation(density)
        st.rerun()

with run:
    if st.session_state.running:
        if st.button("⏸ 일시정지", width="stretch"):
            st.session_state.running = False
            st.rerun()
    else:
        if st.button("▶ 진행", type="primary", width="stretch"):
            st.session_state.running = True
            st.rerun()

with indicator:
    st.markdown(f"Current step: {st.session_state.step_count}")

plot_col, wind_col = st.columns([5, 2])
with plot_col:
    plot_placeholder = st.empty()
with wind_col:
    wind_placeholder = st.empty()


def draw_grid():
    grid = st.session_state.grid

    img_array = np.zeros((GRID_SIZE, GRID_SIZE, 3), dtype=np.uint8)
    for state, color in COLOR_MAP.items():
        img_array[grid == state] = color

    scale_factor = 15
    high_res_img = np.repeat(
        np.repeat(img_array, scale_factor, axis=0), scale_factor, axis=1
    )

    plot_placeholder.image(high_res_img, width="content", output_format="PNG")


def draw_wind_indicator(wind_dir_deg: int, placeholder):
    arrow_rotation = 90 - wind_dir_deg

    placeholder.markdown(
        f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 280px;
            padding: 14px;
            border-radius: 16px;
            background: #0e1117;
            border: 1px solid rgba(255, 255, 255, 0.08);
        ">
            <div style="
                font-size: 15px;
                font-weight: 700;
                color: #ffffff;
                margin-bottom: 12px;
                letter-spacing: 0.02em;
            ">풍향계</div>
            <div style="
                position: relative;
                width: 150px;
                height: 150px;
                border-radius: 50%;
                background: #262730;
                border: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <svg
                    viewBox="0 0 120 120"
                    width="104"
                    height="104"
                    style="
                        position: absolute;
                        left: 50%;
                        top: 50%;
                        transform: translate(-50%, -50%) rotate({arrow_rotation}deg);
                        transform-origin: center;
                        overflow: visible;
                    "
                >
                    <g>
                        <line x1="60" y1="22" x2="60" y2="76" stroke="#ff4b4b" stroke-width="4.5" stroke-linecap="round" />
                        <polygon points="60,12 52,28 68,28" fill="#ff4b4b" />
                        <line x1="60" y1="76" x2="43" y2="96" stroke="#ff4b4b" stroke-width="4.5" stroke-linecap="round" />
                        <line x1="60" y1="76" x2="77" y2="96" stroke="#ff4b4b" stroke-width="4.5" stroke-linecap="round" />
                        <line x1="60" y1="76" x2="48" y2="92" stroke="#ff4b4b" stroke-width="3.25" stroke-linecap="round" opacity="0.88" />
                        <line x1="60" y1="76" x2="72" y2="92" stroke="#ff4b4b" stroke-width="3.25" stroke-linecap="round" opacity="0.88" />
                    </g>
                </svg>
                <div style="
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    width: 10px;
                    height: 10px;
                    transform: translate(-50%, -50%);
                    border-radius: 50%;
                    background: #c9d1d9;
                    box-shadow: 0 0 0 3px rgba(14, 17, 23, 0.7);
                "></div>
            </div>
            <div style="margin-top: 12px; font-size: 15px; font-weight: 700; color: #ffffff;">
                {wind_dir_deg}°
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


draw_grid()
draw_wind_indicator(wind_dir, wind_placeholder)

if st.session_state.running:
    if not st.session_state.frames:
        build_frames(temp, humidity, wind_speed, wind_dir)

    if st.session_state.frame_idx < len(st.session_state.frames) - 1:
        time.sleep(delay)
        st.session_state.frame_idx += 1
        st.session_state.grid = st.session_state.frames[st.session_state.frame_idx]
        st.session_state.step_count += 1
        st.rerun()
    else:
        st.session_state.running = False
        st.rerun()
