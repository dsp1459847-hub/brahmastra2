import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Frequency Tracker", layout="wide")

st.title("MAYA AI 📊: Historical Frequency Tracker Engine")
st.markdown("Yeh engine pichle 30-60 dinon ka itihas padhkar batayega ki kis 'Frequency Group' (Jaise 2 Baar ya 4 Baar) se sach mein sabse zyada number aate hain!")

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

        # --- 3. THE HISTORICAL BACKTEST ENGINE (Finding what hits most) ---
        target_list = filtered_df[target_shift_name].tolist()
        valid_dates = filtered_df.dropna(subset=[target_shift_name])['DATE'].tolist()
        
        test_days_count = 30 # Pichle 30 din ka test karenge
        test_dates = valid_dates[-test_days_count:] if len(valid_dates) > test_days_count else valid_dates
        
        freq_hit_history = Counter()

        with st.spinner(f"Pichle {test_days_count} dinon ka data scan kar raha hoon taaki sabse strong 'Frequency (Baar)' dhoondh sakun..."):
            for test_date in test_dates:
                past_df = filtered_df[filtered_df['DATE'] < test_date]
                if len(past_df) < 15: continue
                
                # Best tiers nikalna (Fast mode)
                best_t_dict = {}
                for shift in shift_names:
                    if shift not in past_df.columns: continue
                    best_t_dict[shift] = "High" # Fast assumption for speed in backtest
                
                all_nums = []
                for shift in shift_names:
                    if shift not in past_df.columns: continue
                    s_list = past_df[shift].tolist()
                    e, s = run_elimination(s_list, max_repeat_limit)
                    h, m, l, el = get_tiers(e, s)
                    all_nums.extend(h) # Checking High tier for intersection

                f_counts = Counter(all_nums)
                
                # Actual Number of that day
                actual_val = filtered_df[filtered_df['DATE'] == test_date][target_shift_name].values[0]
                if pd.notna(actual_val):
                    actual_res = int(actual_val)
                    freq_of_actual = f_counts.get(actual_res, 0)
                    freq_hit_history[freq_of_actual] += 1

        # --- 4. DISPLAY HISTORICAL RESULTS ---
        st.markdown("---")
        st.header(f"📈 History Check: Pichle {test_days_count} dinon mein kahan se number aaye?")
        
        if freq_hit_history:
            best_frequency = max(freq_hit_history, key=freq_hit_history.get)
            
            # Simple chart data preparation
            chart_data = {"Group": [], "Kitni Baar Paas Hua": []}
            for k in sorted(freq_hit_history.keys(), reverse=True):
                if k > 0:
                    chart_data["Group"].append(f"{k} Baar Aaye")
                    chart_data["Kitni Baar Paas Hua"].append(freq_hit_history[k])
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.success(f"**Sabse Zordaar Group:**\n### {best_frequency} Baar Wale")
                st.write("*(Pichle dino mein sabse zyada target numbers isi frequency se nikle hain)*")
            with c2:
                st.bar_chart(pd.DataFrame(chart_data).set_index("Group"))
        else:
            best_frequency = 2 # Default
            st.warning("History check ke liye data kam hai.")

        # --- 5. LIVE PREDICTION FOR TARGET DATE ---
        st.markdown("---")
        target_date = filtered_df['DATE'].iloc[-1] + timedelta(days=1)
        st.header(f"🎯 Live Numbers for {target_date.strftime('%d %B %Y')}")
        
        # Step 1: Find best tier of target
        all_best_numbers_live = []
        with st.spinner("Aaj ke numbers calculate ho rahe hain..."):
            for shift in shift_names:
                if shift not in filtered_df.columns: continue
                s_list = filtered_df[shift].tolist()
                e, s = run_elimination(s_list, max_repeat_limit)
                h, m, l, el = get_tiers(e, s)
                
                # For high accuracy grouping, we gather all tiers and group them
                # But for safety, we focus on High and Medium intersections
                all_best_numbers_live.extend(h)
                all_best_numbers_live.extend(m)

        live_counts = Counter(all_best_numbers_live)
        
        freq_groups_live = {
            "7 Baar": [], "6 Baar": [], "5 Baar": [], 
            "4 Baar": [], "3 Baar": [], "2 Baar": [], "1 Baar": []
        }
        
        for num, count in live_counts.items():
            if count >= 7: freq_groups_live["7 Baar"].append(num)
            elif count == 6: freq_groups_live["6 Baar"].append(num)
            elif count == 5: freq_groups_live["5 Baar"].append(num)
            elif count == 4: freq_groups_live["4 Baar"].append(num)
            elif count == 3: freq_groups_live["3 Baar"].append(num)
            elif count == 2: freq_groups_live["2 Baar"].append(num)
            elif count == 1: freq_groups_live["1 Baar"].append(num)

        st.info(f"💡 **AI Recommendation:** History ke hisab se aaj aapko **[{best_frequency} Baar]** aane wale numbers par sabse zyada focus karna chahiye!")

        t1, t2 = st.columns(2)
        with t1:
            st.markdown(f"#### 🏆 Recommended Groups (History Match)")
            
            # Show the groups that match the best historical frequency (e.g., 2 and 3)
            best_label = f"{best_frequency} Baar"
            st.success(f"**{best_label} Aaye Hue Numbers ({len(freq_groups_live.get(best_label, []))} Nums):**")
            st.write(", ".join([f"{x:02d}" for x in sorted(freq_groups_live.get(best_label, []))]) if freq_groups_live.get(best_label, []) else "None")
            
            # Additional close matches
            alt_label = f"{best_frequency + 1} Baar"
            st.warning(f"**{alt_label} Aaye Hue Numbers ({len(freq_groups_live.get(alt_label, []))} Nums):**")
            st.write(", ".join([f"{x:02d}" for x in sorted(freq_groups_live.get(alt_label, []))]) if freq_groups_live.get(alt_label, []) else "None")

        with t2:
            st.markdown(f"#### 📊 Other High Frequency Groups")
            st.error(f"**4 Baar Aaye:** {len(freq_groups_live['4 Baar'])} Nums")
            st.write(", ".join([f"{x:02d}" for x in sorted(freq_groups_live['4 Baar'])]) if freq_groups_live['4 Baar'] else "None")
            
            st.info(f"**5-7 Baar Aaye (Rare):**")
            rare_nums = freq_groups_live['5 Baar'] + freq_groups_live['6 Baar'] + freq_groups_live['7 Baar']
            st.write(", ".join([f"{x:02d}" for x in sorted(rare_nums)]) if rare_nums else "None")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👈 Kripya apna data upload karein.")
        
