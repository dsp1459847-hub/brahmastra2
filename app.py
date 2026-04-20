import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - 4 Tier Engine", layout="wide")

st.title("MAYA AI 🚀: 4-Tier Complete Predictor (High/Med/Low/Eliminated)")

# --- 1. Sidebar Controls ---
st.sidebar.header("📁 Upload File")
uploaded_file = st.sidebar.file_uploader("Apni CSV ya Excel File upload karein", type=['csv', 'xlsx'])

shift_names = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]

st.sidebar.markdown("---")
st.sidebar.header("🎯 Target Settings")
target_shift_name = st.sidebar.selectbox("Main Target Shift", shift_names)
selected_end_date = st.sidebar.date_input("Calculation Date (Past data limit)")
max_repeat_limit = st.sidebar.slider("Max Repeat Limit", 2, 5, 4)

if uploaded_file is not None:
    try:
        # --- 2. Data Cleaning & Loading ---
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.sort_values(by='DATE').reset_index(drop=True)
        
        for col in shift_names:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        filtered_df = df[df['DATE'].dt.date <= selected_end_date].copy()
        
        if len(filtered_df) == 0:
            st.warning("Selected date tak koi data nahi mila.")
            st.stop()

        # --- 3. Core Engine: Elimination & Scoring ---
        def run_elimination(shift_list, limit):
            shift_list = [int(x) for x in shift_list if pd.notna(x)]
            eliminated = set()
            scores = Counter()
            for days in range(1, 31):
                if len(shift_list) < days: continue
                sheet = shift_list[-days:]
                counts = Counter(sheet)
                
                # Zero-Repeat
                if len(counts) == len(sheet) and len(sheet) > 1:
                    eliminated.update(sheet)
                
                # Max Hit
                for num, freq in counts.items():
                    if freq >= limit: eliminated.add(num)
                    else: scores[num] += 1
            return eliminated, scores

        def get_tiers(elim_set, score_dict):
            safe = sorted([n for n in range(100) if n not in elim_set], key=lambda x: score_dict[x], reverse=True)
            elim_list = sorted(list(elim_set)) # NAYA: Eliminated ko bhi list bana liya
            
            if not safe: return [], [], [], elim_list
            n_s = len(safe)
            return safe[:int(n_s*0.33)], safe[int(n_s*0.33):int(n_s*0.66)], safe[int(n_s*0.66):], elim_list

        # --- 4. ENGINE: MARKOV CHAIN HISTORY MATCHER (With Eliminated Pool) ---
        st.markdown("---")
        st.header(f"🧠 AI Markov Chain Logic for [{target_shift_name}]")
        
        target_list = filtered_df[target_shift_name].tolist()
        elim_final, scores_final = run_elimination(target_list, max_repeat_limit)
        ht, mt, lt, et = get_tiers(elim_final, scores_final)
        
        # Pichle dinon ka sequence nikalna (Data train karne ke liye)
        with st.spinner("Itihas (History) check kar raha hoon... (Including Eliminated Breakouts)"):
            historical_tiers = []
            valid_target_data = [x for x in target_list if pd.notna(x)]
            
            test_range = min(100, len(valid_target_data))
            
            for i in range(test_range, 0, -1):
                past_data = valid_target_data[:-i]
                if not past_data: continue
                actual = valid_target_data[-i]
                
                e, s = run_elimination(past_data, max_repeat_limit)
                h, m, l, eliminated_past = get_tiers(e, s)
                
                # Ab hum track kar rahe hain ki kya number eliminated me tha
                if actual in h: historical_tiers.append("High")
                elif actual in m: historical_tiers.append("Medium")
                elif actual in l: historical_tiers.append("Low")
                else: historical_tiers.append("Eliminated") # NAYA: Pehle isko fail likhte the

            # Check last 2 days pattern
            if len(historical_tiers) >= 2:
                last_2_pattern = (historical_tiers[-2], historical_tiers[-1])
                
                # Find this pattern in history
                next_day_results = {"High": 0, "Medium": 0, "Low": 0, "Eliminated": 0}
                for i in range(len(historical_tiers) - 2):
                    if (historical_tiers[i], historical_tiers[i+1]) == last_2_pattern:
                        next_day_results[historical_tiers[i+2]] += 1
                
                total_matches = sum(next_day_results.values())
                if total_matches > 0:
                    best_historical = max(next_day_results, key=next_day_results.get)
                    win_prob = (next_day_results[best_historical] / total_matches) * 100
                    
                    st.info(f"**History Match:** Jab bhi pehle **[{last_2_pattern[0]} ➔ {last_2_pattern[1]}]** aaya hai, toh uske agle din sabse zyada **{best_historical.upper()} TIER** nikla hai ({win_prob:.0f}% times).")
                else:
                    best_historical = "High" # Default if no pattern match
            else:
                best_historical = "High"

        # --- 5. FINAL UI WITH 4 COLUMNS ---
        len_h, len_m, len_l, len_e = len(ht), len(mt), len(lt), len(et)
        
        st.markdown("---")
        target_date = filtered_df['DATE'].iloc[-1] + timedelta(days=1)
        st.subheader(f"🎯 Complete 100-Number View for {target_date.strftime('%d %B %Y')}")
        
        # AI Final Decision
        final_recommendation = best_historical 
        
        if final_recommendation == "Eliminated":
            st.error(f"### ⚠️ AI WARNING & VERDICT: Aapko aaj [{final_recommendation.upper()} TIER] par dhyan dena chahiye!")
            st.write("*(Kyonki AI ka pattern bata raha hai ki aaj safe numbers fail ho sakte hain aur eliminated numbers mein se 'Breakout' hone ka bahut zyada chance hai!)*")
        else:
            st.success(f"### 🏆 AI Final Verdict: Aapko [{final_recommendation.upper()} TIER] par lagana chahiye!")

        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f"#### 🔥 High ({len_h}) {'✅' if final_recommendation=='High' else ''}")
            st.write(", ".join([f"{x:02d}" for x in ht]))
            
        with c2:
            st.markdown(f"#### ⚡ Medium ({len_m}) {'✅' if final_recommendation=='Medium' else ''}")
            st.write(", ".join([f"{x:02d}" for x in mt]))
            
        with c3:
            st.markdown(f"#### ❄️ Low ({len_l}) {'✅' if final_recommendation=='Low' else ''}")
            st.write(", ".join([f"{x:02d}" for x in lt]))
            
        with c4:
            st.markdown(f"#### 🚫 Eliminated ({len_e}) {'⚠️ RECOMMENDED' if final_recommendation=='Eliminated' else ''}")
            st.write(", ".join([f"{x:02d}" for x in et]))

    except Exception as e:
        st.error(f"Error processing the file: {e}")
else:
    st.info("👈 Kripya apna data upload karein.")
      
