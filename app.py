import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Self Correcting", layout="wide")

st.title("MAYA AI 🤖: Self-Correcting Predictor (Galti Sudharne Wala AI)")

# --- 1. Sidebar ---
st.sidebar.header("📁 Upload File")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
shift_names = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]
target_shift_name = st.sidebar.selectbox("Target Shift", shift_names)
selected_end_date = st.sidebar.date_input("Calculation Date")
max_repeat_limit = st.sidebar.slider("Max Repeat Limit", 2, 5, 4)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.sort_values(by='DATE').reset_index(drop=True)
        for col in shift_names:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')

        filtered_df = df[df['DATE'].dt.date <= selected_end_date].copy()
        if len(filtered_df) == 0: st.stop()

        # --- 2. Core Engine ---
        def run_elimination(shift_list, limit):
            shift_list = [int(x) for x in shift_list if pd.notna(x)]
            eliminated = set()
            scores = Counter()
            for days in range(1, 31):
                if len(shift_list) < days: continue
                sheet = shift_list[-days:]
                counts = Counter(sheet)
                if len(counts) == len(sheet) and len(sheet) > 1: eliminated.update(sheet)
                for num, freq in counts.items():
                    if freq >= limit: eliminated.add(num)
                    else: scores[num] += 1
            return eliminated, scores

        def get_tiers(elim_set, score_dict):
            safe = sorted([n for n in range(100) if n not in elim_set], key=lambda x: score_dict[x], reverse=True)
            elim_list = sorted(list(elim_set))
            if not safe: return [], [], [], elim_list
            n_s = len(safe)
            return safe[:int(n_s*0.33)], safe[int(n_s*0.33):int(n_s*0.66)], safe[int(n_s*0.66):], elim_list

        # --- 3. RAW MARKOV & ERROR TRACKING ---
        target_list = filtered_df[target_shift_name].tolist()
        valid_data = [x for x in target_list if pd.notna(x)]
        
        raw_predictions = []
        actual_results = []
        
        # Piche 30 din ka data check karke Error Mapping banana
        test_range = min(60, len(valid_data))
        
        with st.spinner("AI apni pichli galtiyon (errors) ko padh raha hai..."):
            for i in range(test_range, 0, -1):
                past_data = valid_data[:-i]
                if len(past_data) < 2: continue
                actual = valid_data[-i]
                
                e, s = run_elimination(past_data, max_repeat_limit)
                h, m, l, el = get_tiers(e, s)
                
                if actual in h: actual_tier = "High"
                elif actual in m: actual_tier = "Medium"
                elif actual in l: actual_tier = "Low"
                else: actual_tier = "Eliminated"
                
                actual_results.append(actual_tier)
                
                # Raw prediction base logic (Simplistic history check)
                if len(actual_results) >= 3:
                    last_2 = (actual_results[-3], actual_results[-2])
                    # Simple raw guess
                    raw_pred = "High" # Default
                    # Very basic raw mapping for simulation
                    if last_2[1] == "High": raw_pred = "Medium"
                    elif last_2[1] == "Medium": raw_pred = "Low"
                    elif last_2[1] == "Low": raw_pred = "High"
                    raw_predictions.append(raw_pred)
                else:
                    raw_predictions.append("High")

        # --- 4. SELF-CORRECTION LOGIC (The Magic) ---
        # AI dekhega ki jab usne "X" bola tha, toh sach me kya aaya "Y"
        error_map = {"High": [], "Medium": [], "Low": [], "Eliminated": []}
        for rp, ar in zip(raw_predictions, actual_results[2:]):
            if rp in error_map:
                error_map[rp].append(ar)
                
        # Aaj ki Raw Prediction
        if len(actual_results) >= 2:
            last_2_today = (actual_results[-2], actual_results[-1])
            today_raw_pred = "High"
            if last_2_today[1] == "High": today_raw_pred = "Medium"
            elif last_2_today[1] == "Medium": today_raw_pred = "Low"
            elif last_2_today[1] == "Low": today_raw_pred = "High"
        else:
            today_raw_pred = "High"

        # Apply Correction
        correction_history = error_map.get(today_raw_pred, [])
        if correction_history:
            counts = Counter(correction_history)
            
            # ELIMINATED SPIKE ALERT (Agar eliminated normally se zyada aaya hai is pattern me)
            total_cases = sum(counts.values())
            elim_chance = (counts.get("Eliminated", 0) / total_cases) * 100 if total_cases > 0 else 0
            
            # Agar eliminated ka chance 15% se upar hai, toh seedha alert maro!
            if elim_chance >= 15:
                final_pred = "Eliminated"
                reason = f"Raw AI ne {today_raw_pred} socha tha, par history batati hai ki is condition me {elim_chance:.0f}% chance 'Eliminated' (Breakout) aane ka hota hai!"
            else:
                final_pred = max(counts, key=counts.get)
                reason = f"Raw AI pehle '{today_raw_pred}' predict kar raha tha. Par usne pichli galtiyan dekhi aur paya ki jab wo {today_raw_pred} sochta hai, tab asal mein **{final_pred}** aata hai. Isliye usne apna answer badal liya."
        else:
            final_pred = today_raw_pred
            reason = "Data clear nahi hai, raw prediction apply ki gayi hai."

        # --- 5. FINAL UI ---
        st.markdown("---")
        target_date = filtered_df['DATE'].iloc[-1] + timedelta(days=1)
        st.subheader(f"🎯 Corrected Prediction for {target_date.strftime('%d %B %Y')}")
        
        if final_pred == "Eliminated":
            st.error(f"### ⚠️ AI WARNING: Aaj [{final_pred.upper()}] TIER se Breakout ka bada chance hai!")
            st.write(f"💡 **AI Logic:** {reason}")
        else:
            st.success(f"### 🏆 AI Final Verdict: Aapko [{final_pred.upper()} TIER] par khelna chahiye!")
            st.write(f"💡 **Self-Correction Logic:** {reason}")

        # Tiers calculation for display
        e_f, s_f = run_elimination(valid_data, max_repeat_limit)
        h_f, m_f, l_f, el_f = get_tiers(e_f, s_f)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"#### 🔥 High ({len(h_f)}) {'✅' if final_pred=='High' else ''}")
            st.write(", ".join([f"{x:02d}" for x in h_f]))
        with c2:
            st.markdown(f"#### ⚡ Medium ({len(m_f)}) {'✅' if final_pred=='Medium' else ''}")
            st.write(", ".join([f"{x:02d}" for x in m_f]))
        with c3:
            st.markdown(f"#### ❄️ Low ({len(l_f)}) {'✅' if final_pred=='Low' else ''}")
            st.write(", ".join([f"{x:02d}" for x in l_f]))
        with c4:
            st.markdown(f"#### 🚫 Eliminated ({len(el_f)}) {'⚠️' if final_pred=='Eliminated' else ''}")
            st.write(", ".join([f"{x:02d}" for x in el_f]))

    except Exception as e:
        st.error(f"Error processing the file: {e}")
else:
    st.info("👈 Kripya apna data upload karein.")
    
