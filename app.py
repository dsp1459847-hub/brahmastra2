import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Cross Shift Subtraction", layout="wide")

st.title("MAYA AI ⚔️: Cross-Shift Subtraction Engine")
st.markdown("Yeh AI sabhi shifton ke 28 Tiers check karke **'Sabse Best Tier'** mein se **'Zero Hit (Dead) Tiers'** ke numbers ko MINUS karke final result deta hai.")

# --- 1. Sidebar ---
st.sidebar.header("📁 Upload File")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
shift_names = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]
target_shift_name = st.sidebar.selectbox("🎯 Target Shift (Kiska result chahiye?)", shift_names)
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

        # --- 3. CROSS-SHIFT HISTORICAL RELATION CHECK (30 Days) ---
        st.markdown("---")
        test_days = 30
        valid_dates = filtered_df.dropna(subset=[target_shift_name])['DATE'].tolist()
        test_dates = valid_dates[-test_days:] if len(valid_dates) > test_days else valid_dates
        
        # Track hits for all 28 tiers
        tier_performance = {f"{shift}_{tier}": 0 for shift in shift_names for tier in ["High", "Medium", "Low", "Eliminated"]}
        
        with st.spinner(f"Pichle {test_days} dinon mein Sabhi Shifton ke cross-relations check ho rahe hain..."):
            for t_date in test_dates:
                past_df = filtered_df[filtered_df['DATE'] < t_date]
                if len(past_df) < 15: continue
                
                actual_num = int(filtered_df[filtered_df['DATE'] == t_date][target_shift_name].values[0])
                
                # Har shift ka tier calculate karna us din ke liye
                for shift in shift_names:
                    if shift not in past_df.columns: continue
                    past_s = past_df[shift].tolist()
                    e, s = run_elimination(past_s, max_repeat_limit)
                    h, m, l, el = get_tiers(e, s)
                    
                    if actual_num in h: tier_performance[f"{shift}_High"] += 1
                    if actual_num in m: tier_performance[f"{shift}_Medium"] += 1
                    if actual_num in l: tier_performance[f"{shift}_Low"] += 1
                    if actual_num in el: tier_performance[f"{shift}_Eliminated"] += 1

        # Hero Tier and Dead Tiers identify karna
        hero_tier_name = max(tier_performance, key=tier_performance.get)
        hero_tier_hits = tier_performance[hero_tier_name]
        
        dead_tiers = [name for name, hits in tier_performance.items() if hits == 0]
        
        st.write("### 📊 Cross-Shift Relation Report")
        colA, colB = st.columns(2)
        with colA:
            st.success(f"**👑 HERO TIER (Sabse Zyada Aane Wala):**\n### {hero_tier_name}")
            st.write(f"*Pichle {test_days} dino me **{target_shift_name}** ka number {hero_tier_hits} baar is tier se aaya hai!*")
        with colB:
            st.error(f"**💀 DEAD TIERS (Zero Hit Wale):**\n### {len(dead_tiers)} Tiers Mile")
            st.write("*(In tiers ka number pichle 30 dino me ek baar bhi target shift me nahi aaya)*")
            with st.expander("Show Dead Tiers"):
                for dt in dead_tiers: st.write(f"- {dt}")

        # --- 4. LIVE SUBTRACTION LOGIC FOR NEXT DAY ---
        st.markdown("---")
        next_date = filtered_df['DATE'].iloc[-1] + timedelta(days=1)
        st.header(f"🎯 Master Prediction for {next_date.strftime('%d %B %Y')} ({target_shift_name})")
        
        with st.spinner("Hero Tier mein se Dead Tiers ke numbers MINUS kar raha hoon..."):
            # Calculate today's tiers for all shifts
            today_all_tiers = {}
            for shift in shift_names:
                if shift not in filtered_df.columns: continue
                s_list = filtered_df[shift].tolist()
                e, s = run_elimination(s_list, max_repeat_limit)
                h, m, l, el = get_tiers(e, s)
                today_all_tiers[f"{shift}_High"] = set(h)
                today_all_tiers[f"{shift}_Medium"] = set(m)
                today_all_tiers[f"{shift}_Low"] = set(l)
                today_all_tiers[f"{shift}_Eliminated"] = set(el)
            
            # Get Hero Numbers
            hero_numbers = today_all_tiers.get(hero_tier_name, set())
            
            # Collect all Dead Numbers
            dead_numbers = set()
            for dt in dead_tiers:
                dead_numbers.update(today_all_tiers.get(dt, set()))
            
            # The Magic: Subtraction
            final_pure_numbers = hero_numbers - dead_numbers
            
        # Display Math
        st.info(f"🧮 **The Subtraction Math:** [{hero_tier_name} ({len(hero_numbers)} nums)] MINUS [All Dead Tiers ({len(dead_numbers)} nums)] = {len(final_pure_numbers)} Pure Numbers")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"#### 👑 Original Hero Numbers")
            st.write(", ".join([f"{x:02d}" for x in sorted(hero_numbers)]) if hero_numbers else "None")
        with c2:
            st.markdown(f"#### 💀 Dead Numbers (Removed)")
            st.write(", ".join([f"{x:02d}" for x in sorted(hero_numbers.intersection(dead_numbers))]) if hero_numbers.intersection(dead_numbers) else "None")
        with c3:
            st.markdown(f"#### ✨ FINAL PURE NUMBERS")
            st.success(", ".join([f"{x:02d}" for x in sorted(final_pure_numbers)]) if final_pure_numbers else "No numbers left!")

    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.info("👈 Kripya apna data upload karein.")
    
