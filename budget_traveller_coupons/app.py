import io
import random
from typing import Dict, List, Tuple, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Budget Traveller with Coupons", page_icon="✈️", layout="wide")
st.title("Budget Traveller with Coupons")
st.caption("Find the cheapest one-way route with a stop limit and discount coupons.")

st.markdown("""
A coupon halves one flight's price using **floor(price / 2)**. At most one coupon can be used on a flight.
The destination is city **N** and the start is city **1**.
""")

def parse_flights(df: pd.DataFrame, n: int) -> List[Tuple[int, int, int]]:
    required = {"u", "v", "p"}
    if not required.issubset(set(df.columns.str.lower())):
        raise ValueError("CSV must contain columns named u, v, p (origin, destination, price).")
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    flights = []
    for _, row in df.iterrows():
        u, v, p = int(row["u"]), int(row["v"]), int(row["p"])
        if not (1 <= u <= n and 1 <= v <= n):
            raise ValueError(f"Flight {u} -> {v} has a city outside 1..{n}.")
        if p < 0:
            raise ValueError("Ticket prices must be non-negative.")
        flights.append((u, v, p))
    return flights

def solve(n: int, flights: List[Tuple[int, int, int]], k: int, coupons: int):
    """DP over number of flights and coupons used; at most k intermediate stops means k+1 flights."""
    max_flights = k + 1
    # dp[(city, flights_taken, coupons_used)] = cost
    dp = {(1, 0, 0): 0}
    parent = {}
    for used_flights in range(max_flights):
        current = [(state, cost) for state, cost in list(dp.items()) if state[1] == used_flights]
        for (city, f_count, c_used), cost in current:
            for idx, (u, v, price) in enumerate(flights):
                if u != city:
                    continue
                # Normal fare
                state = (v, f_count + 1, c_used)
                new_cost = cost + price
                if new_cost < dp.get(state, float("inf")):
                    dp[state] = new_cost
                    parent[state] = ((city, f_count, c_used), idx, False)
                # Discounted fare
                if c_used < coupons:
                    state = (v, f_count + 1, c_used + 1)
                    new_cost = cost + price // 2
                    if new_cost < dp.get(state, float("inf")):
                        dp[state] = new_cost
                        parent[state] = ((city, f_count, c_used), idx, True)

    candidates = [(cost, state) for state, cost in dp.items() if state[0] == n and state[1] <= max_flights]
    if not candidates:
        return None
    best_cost, state = min(candidates, key=lambda item: item[0])
    path_steps = []
    while state != (1, 0, 0):
        if state not in parent:
            break
        previous, flight_idx, coupon_used = parent[state]
        u, v, price = flights[flight_idx]
        path_steps.append({
            "u": u, "v": v, "price": price,
            "charged": price // 2 if coupon_used else price,
            "coupon": coupon_used, "flight_idx": flight_idx,
            "step": state[1]
        })
        state = previous
    path_steps.reverse()
    return {"cost": best_cost, "steps": path_steps}

def build_result_csv(flights, result):
    path_by_idx = {}
    if result:
        for s in result["steps"]:
            path_by_idx[s["flight_idx"]] = s
    rows = []
    for idx, (u, v, p) in enumerate(flights):
        chosen = path_by_idx.get(idx)
        rows.append({
            "u": u, "v": v, "p": p,
            "chosen_path": "x" if chosen else "",
            "coupon_used": "x" if chosen and chosen["coupon"] else "",
            "charged_price": chosen["charged"] if chosen else "",
            "path_order": chosen["step"] if chosen else ""
        })
    return pd.DataFrame(rows)

def make_graph(n, flights, result, active_step=None):
    pos = {}
    # Circle layout, stable for any number of cities
    import math
    for city in range(1, n + 1):
        angle = 2 * math.pi * (city - 1) / max(n, 1) - math.pi / 2
        pos[city] = (math.cos(angle), math.sin(angle))

    chosen = {}
    path_cities = set()
    if result:
        for s in result["steps"]:
            chosen[s["flight_idx"]] = s
            path_cities.add(s["u"])
            path_cities.add(s["v"])

    fig = go.Figure()
    # Draw edges individually so route/coupon colours are clear
    for idx, (u, v, price) in enumerate(flights):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        step_info = chosen.get(idx)
        is_route = step_info is not None
        visible_route = is_route and (active_step is None or step_info["step"] <= active_step)
        color = "#D4A017" if visible_route and step_info["coupon"] else (
            "#2563EB" if visible_route else "#B8C0CC")
        width = 4 if visible_route else 1.5
        # Offset the edge slightly from the node center
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(color=color, width=width),
            hoverinfo="text",
            text=[f"{u} → {v}: {price}", f"{u} → {v}: {price}"],
            showlegend=False
        ))
        # Arrow head as an annotation
        fig.add_annotation(
            x=x0 + (x1-x0)*0.84, y=y0 + (y1-y0)*0.84,
            ax=x0 + (x1-x0)*0.68, ay=y0 + (y1-y0)*0.68,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.1,
            arrowwidth=width, arrowcolor=color
        )
        label = f"{price}"
        if is_route and step_info["coupon"]:
            label = f"{price} → {step_info['charged']}"
        mx, my = (x0+x1)/2, (y0+y1)/2
        fig.add_trace(go.Scatter(
            x=[mx], y=[my], mode="text", text=[label],
            textposition="top center", textfont=dict(size=11, color=color),
            hoverinfo="skip", showlegend=False
        ))

    node_x, node_y, node_text, node_colors = [], [], [], []
    for city in range(1, n+1):
        x, y = pos[city]
        node_x.append(x); node_y.append(y); node_text.append(str(city))
        if city == 1:
            node_colors.append("#22C55E")
        elif city == n:
            node_colors.append("#EF4444")
        elif result and city in path_cities:
            node_colors.append("#F59E0B")
        else:
            node_colors.append("#64748B")
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=node_text, textposition="middle center",
        marker=dict(size=34, color=node_colors, line=dict(color="white", width=2)),
        textfont=dict(color="white", size=13),
        hovertemplate="City %{text}<extra></extra>", showlegend=False
    ))
    fig.update_layout(
        height=540, margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False, range=[-1.35, 1.35]),
        yaxis=dict(visible=False, range=[-1.35, 1.35], scaleanchor="x", scaleratio=1),
        plot_bgcolor="white", paper_bgcolor="white"
    )
    return fig

mode = st.radio("Choose input mode", [
    "Option 1 — Enter flights manually",
    "Option 2 — Upload a CSV graph",
    "Option 3 — Generate a graph"
], horizontal=False)

n = 5
k = 2
c = 1
flights = []

if mode.startswith("Option 1"):
    col1, col2, col3, col4 = st.columns(4)
    with col1: n = st.number_input("Number of cities (N)", min_value=2, max_value=30, value=5, step=1)
    with col2: m = st.number_input("Number of flights (M)", min_value=1, max_value=200, value=7, step=1)
    with col3: k = st.number_input("Maximum stops (K)", min_value=0, max_value=29, value=2, step=1)
    with col4: c = st.number_input("Coupons (C)", min_value=0, max_value=20, value=1, step=1)
    st.info("Enter one flight per row. Cities are numbered 1 through N.")
    starter = pd.DataFrame({"u":[1,1,2,2,3,4,3], "v":[2,3,3,4,4,5,5], "p":[200,300,100,250,100,150,500]})
    starter = starter.iloc[:int(m)].copy()
    if len(starter) < int(m):
        starter = pd.concat([starter, pd.DataFrame({"u":[1]* (int(m)-len(starter)), "v":[int(n)]*(int(m)-len(starter)), "p":[100]*(int(m)-len(starter))})], ignore_index=True)
    edited = st.data_editor(starter, num_rows="dynamic", use_container_width=True, key="manual_flights")
    if st.button("Find cheapest route", type="primary"):
        try:
            flights = parse_flights(edited, int(n))
            result = solve(int(n), flights, int(k), int(c))
            st.session_state["last_input"] = (int(n), flights, int(k), int(c))
            st.session_state["last_result"] = result
        except Exception as e:
            st.error(str(e))

elif mode.startswith("Option 2"):
    col1, col2 = st.columns(2)
    with col1: k = st.number_input("Maximum stops (K)", min_value=0, max_value=29, value=2, step=1)
    with col2: c = st.number_input("Coupons (C)", min_value=0, max_value=20, value=1, step=1)
    uploaded = st.file_uploader("Upload flights CSV (columns: u,v,p)", type=["csv"])
    n = st.number_input("Number of cities (N; destination is N)", min_value=2, max_value=30, value=5, step=1)
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            if st.button("Find cheapest route", type="primary"):
                flights = parse_flights(df, int(n))
                result = solve(int(n), flights, int(k), int(c))
                st.session_state["last_input"] = (int(n), flights, int(k), int(c))
                st.session_state["last_result"] = result
        except Exception as e:
            st.error(str(e))
    st.download_button("Download sample input CSV", data="u,v,p\n1,2,200\n1,3,300\n2,3,100\n2,4,250\n3,4,100\n4,5,150\n3,5,500\n", file_name="flights.csv", mime="text/csv")

else:
    col1, col2, col3 = st.columns(3)
    with col1: n = st.number_input("Number of cities (N)", min_value=2, max_value=20, value=6, step=1)
    with col2: k = st.number_input("Maximum stops (K)", min_value=0, max_value=19, value=2, step=1)
    with col3: c = st.number_input("Coupons (C)", min_value=0, max_value=10, value=1, step=1)
    density = st.slider("Flight density", min_value=15, max_value=70, value=35, step=5)
    seed = st.number_input("Random seed", min_value=0, max_value=99999, value=42, step=1)
    if st.button("Generate graph and solve", type="primary"):
        rng = random.Random(int(seed))
        generated = []
        # Ensure a guaranteed route 1 -> 2 -> ... -> N, plus random directed flights.
        for u in range(1, int(n)):
            generated.append((u, u+1, rng.randint(100, 900)))
        for u in range(1, int(n)+1):
            for v in range(1, int(n)+1):
                if u != v and rng.random() < density/100 and not any(a == u and b == v for a,b,_ in generated):
                    generated.append((u, v, rng.randint(80, 1200)))
        flights = generated
        result = solve(int(n), flights, int(k), int(c))
        st.session_state["last_input"] = (int(n), flights, int(k), int(c))
        st.session_state["last_result"] = result

if "last_input" in st.session_state:
    n_saved, flights_saved, k_saved, c_saved = st.session_state["last_input"]
    result_saved = st.session_state["last_result"]
    st.divider()
    st.subheader("Result")
    if result_saved is None:
        st.error("Output: -1 — destination cannot be reached within the stop limit.")
    else:
        st.success(f"Minimum total cost: {result_saved['cost']}")
        steps = result_saved["steps"]
        stops_used = max(0, len(steps)-1)
        st.write(f"Flights used: **{len(steps)}** · Intermediate stops used: **{stops_used} / {k_saved}** · Coupons used: **{sum(s['coupon'] for s in steps)} / {c_saved}**")
        st.markdown("**Chosen journey**")
        if steps:
            route = [str(steps[0]["u"])] + [str(s["v"]) for s in steps]
            st.write(" → ".join(route))
            detail = pd.DataFrame([{
                "Flight": f"{s['u']} → {s['v']}",
                "Original price": s["price"],
                "Coupon used": "Yes" if s["coupon"] else "No",
                "Price paid": s["charged"],
                "Running total": sum(x["charged"] for x in steps[:i+1])
            } for i,s in enumerate(steps)])
            st.dataframe(detail, use_container_width=True, hide_index=True)

    st.subheader("Flight network")
    if result_saved:
        max_step = len(result_saved["steps"])
        step_num = st.slider("Journey animation — reveal flights up to step", min_value=0, max_value=max_step, value=max_step, step=1)
        visible_cost = sum(s["charged"] for s in result_saved["steps"][:step_num])
        visible_stops = max(0, min(step_num, len(result_saved["steps"])) - 1)
        st.caption(f"Running cost: {visible_cost} · Flights taken: {step_num} · Intermediate stops so far: {visible_stops}")
        st.plotly_chart(make_graph(n_saved, flights_saved, result_saved, active_step=step_num), use_container_width=True)
        st.caption("Green = start · Red = destination · Orange = cities on chosen route · Blue = chosen flight · Gold = chosen flight using a coupon. Coupon edge labels show original → discounted price.")
    else:
        st.plotly_chart(make_graph(n_saved, flights_saved, None), use_container_width=True)

    result_df = build_result_csv(flights_saved, result_saved)
    st.download_button(
        "Download output CSV",
        data=result_df.to_csv(index=False).encode("utf-8"),
        file_name="budget_traveller_output.csv",
        mime="text/csv"
    )
    st.download_button(
        "Download graph input CSV",
        data=pd.DataFrame(flights_saved, columns=["u","v","p"]).to_csv(index=False).encode("utf-8"),
        file_name="flights.csv",
        mime="text/csv"
    )
