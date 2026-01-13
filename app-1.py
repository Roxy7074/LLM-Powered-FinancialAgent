import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
import altair as alt

# Setup
st.set_page_config(page_title="AI Budget Agent", layout="wide", page_icon="🤑")
load_dotenv(override=True)

st.markdown("""
<style>
    /* Force Dark Theme Colors */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* HIDE STREAMLIT DEFAULT MENUS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700;
        color: #4facfe;
    }
    div[data-testid="stMetricLabel"] {
        color: #FAFAFA;
    }
    
    /* Navigation Radio Button Styling */
    div[role="radiogroup"] {
        background-color: #262730;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: center;
    }
    div[data-testid="stRadio"] > label {
        color: white !important;
        font-weight: bold;
        cursor: pointer;
    }
    
    /* Expander/Cards */
    .stExpander {
        border: 1px solid #4a4a4a;
        background-color: #262730;
        color: white;
    }
    
    /* Info Boxes */
    .stAlert {
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #4facfe;
    }
    
    /* NOTE: REMOVED THE .stChatInput CSS THAT WAS BREAKING THE LAYOUT */
    
    /* Add padding to main content so it doesn't get hidden behind chat bar */
    .main .block-container {
        padding-bottom: 100px;
    }
</style>
""", unsafe_allow_html=True)

# the Brain
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def categorize_50_30_20(category):
    cat_lower = str(category).lower()
    needs = ['rent', 'mortgage', 'utilities', 'groceries', 'insurance', 'medical', 'transport', 'gas', 'electric', 'water', 'bill', 'health', 'education']
    savings = ['save', 'investment', 'stock', '401k', 'roth', 'transfer']
    
    if any(word in cat_lower for word in savings):
        return "Savings", 0.20, "#00CC96" # Green
    elif any(word in cat_lower for word in needs):
        return "Needs", 0.50, "#EF553B" # Red
    else:
        return "Wants", 0.30, "#AB63FA" # Purple

def get_grade(needs_pct, wants_pct, savings_pct):
    score = 100
    if needs_pct > 0.50: score -= (needs_pct - 0.50) * 100
    if wants_pct > 0.30: score -= (wants_pct - 0.30) * 100
    if savings_pct < 0.20: score -= (0.20 - savings_pct) * 100
    
    if score >= 90: return "A+ (Excellent)"
    elif score >= 80: return "A (Great)"
    elif score >= 70: return "B (Good)"
    elif score >= 60: return "C (Fair)"
    else: return "Needs Work"

#Main App
def main():
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I am your AI Financial Agent. I can see your budget data. How can I help?"})
    
    if "current_view" not in st.session_state:
        st.session_state.current_view = "📊 Analytics Dashboard"

    st.title("🤑 AI Financial Agent")
    st.caption("Powered by Gemini 2.0 Flash | RAG Enabled")
    st.divider()

  
    st.sidebar.header("⚙️ User Profile")
    income = st.sidebar.number_input("Monthly Income ($)", value=6000, step=100)
    st.sidebar.divider()
    
    st.sidebar.header("📥 Data Input")
    input_method = st.sidebar.radio("Choose Input Method:", ["Upload CSV", "Manual Entry", "No Data (Chat Only)"])
    
    transactions = pd.DataFrame()
    num_months = 1
    
    if input_method == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Upload Transaction CSV", type=["csv"])
        if uploaded_file:
            try:
                transactions = pd.read_csv(uploaded_file)
                # Normalize columns
                transactions.columns = [c.strip().title() for c in transactions.columns]
                if 'Date' in transactions.columns:
                    transactions['Date'] = pd.to_datetime(transactions['Date'])
                    if not transactions['Date'].empty:
                         num_months = transactions['Date'].dt.to_period('M').nunique()
                         if num_months < 1: num_months = 1
            except:
                st.error("Invalid CSV format.")
    elif input_method == "Manual Entry":
        st.sidebar.info("📝 Add transactions one by one.")
        with st.sidebar.form("manual_entry"):
            date = st.date_input("Date")
            desc = st.text_input("Description")
            cat = st.selectbox("Category", ["Rent", "Groceries", "Dining", "Utilities", "Transport", "Entertainment", "Shopping"])
            amt = st.number_input("Amount ($)", min_value=0.01)
            submitted = st.form_submit_button("Add Transaction")
            
            if submitted:
                new_row = pd.DataFrame([[date, desc, cat, amt]], columns=['Date', 'Description', 'Category', 'Amount'])
                if 'manual_data' not in st.session_state:
                    st.session_state.manual_data = new_row
                else:
                    st.session_state.manual_data = pd.concat([st.session_state.manual_data, new_row])
        
        if 'manual_data' in st.session_state:
            transactions = st.session_state.manual_data
            if 'Date' in transactions.columns:
                 transactions['Date'] = pd.to_datetime(transactions['Date'])
                 num_months = transactions['Date'].dt.to_period('M').nunique()
                 if num_months < 1: num_months = 1

    # Load Benchmarks 
    try:
        benchmarks_df = pd.read_csv("benchmarks.csv")
    except:
        benchmarks_df = pd.DataFrame()
    options = ["📊 Analytics Dashboard", "🎛️ Savings Simulator", "🤖 Gemini Chat Agent"]
    
    try:
        nav_index = options.index(st.session_state.current_view)
    except ValueError:
        nav_index = 0

    selected_option = st.radio(
        "Navigate",
        options,
        index=nav_index,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if selected_option != st.session_state.current_view:
        st.session_state.current_view = selected_option
        st.rerun()

    grade = "N/A"
    monthly_spend = 0
    needs_monthly = 0
    wants_monthly = 0
    savings_monthly = 0
    cat_str = "No data"
    
    if not transactions.empty and 'Category' in transactions.columns and 'Amount' in transactions.columns:
        results = transactions['Category'].apply(lambda x: categorize_50_30_20(x))
        transactions['Type'] = [r[0] for r in results]
        
        monthly_spend = round(transactions['Amount'].sum() / num_months, 2)
        leftover = round(income - monthly_spend, 2)
        
        type_group = transactions.groupby('Type')['Amount'].sum()
        needs_monthly = round(type_group.get('Needs', 0) / num_months, 2)
        wants_monthly = round(type_group.get('Wants', 0) / num_months, 2)
        savings_monthly = round((type_group.get('Savings', 0) / num_months) + max(0, leftover), 2)
        
        grade = get_grade(needs_monthly/income, wants_monthly/income, savings_monthly/income)
        
        cat_series = transactions.groupby('Category')['Amount'].sum() / num_months
        cat_str = cat_series.apply(lambda x: f"${x:.2f}").to_string()

    if st.session_state.current_view == "📊 Analytics Dashboard":
        if transactions.empty:
            st.info("👋 Upload a CSV file or add data manually to see your Dashboard.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Monthly Income", f"${income:,.0f}")
            c2.metric("💸 Monthly Avg Spent", f"${monthly_spend:,.2f}")
            c3.metric("🏦 Avg Remaining", f"${leftover:,.2f}")
            c4.metric("🎓 Grade", grade)
            
            st.divider()
            
            r1c1, r1c2 = st.columns([2, 1])
            with r1c1:
                st.subheader("Monthly Spending by Category")
                chart_data = transactions.groupby('Category')['Amount'].sum().reset_index()
                chart_data['Amount'] = chart_data['Amount'] / num_months
                chart_data = chart_data.sort_values('Amount', ascending=False)
                
                top_cat = chart_data.iloc[0]['Category']
                top_amt = chart_data.iloc[0]['Amount']
                st.info(f"**Insight:** On average, your biggest expense is **{top_cat}** (${top_amt:,.2f}/mo).")
                
                bar_chart = alt.Chart(chart_data).mark_bar(cornerRadius=5).encode(
                    x=alt.X('Amount', title='Avg Monthly Spent ($)'),
                    y=alt.Y('Category', sort='-x', title=''),
                    color=alt.Color('Category', legend=None),
                    tooltip=['Category', 'Amount']
                ).properties(height=300)
                st.altair_chart(bar_chart, use_container_width=True)
                
            with r1c2:
                st.subheader("50/30/20 Rule")
                st.info("""
                **What the colors mean:**
                🔴 **Needs (50%):** Rent, Bills, Groceries.
                🟣 **Wants (30%):** Dining, Shopping, Fun.
                🟢 **Savings (20%):** Investments, Leftover Cash.
                """)
                breakdown_data = pd.DataFrame({
                    'Type': ['Needs', 'Wants', 'Savings'],
                    'Amount': [needs_monthly, wants_monthly, savings_monthly]
                })
                donut = alt.Chart(breakdown_data).mark_arc(innerRadius=60).encode(
                    theta="Amount", 
                    color=alt.Color("Type", scale=alt.Scale(domain=['Needs', 'Wants', 'Savings'], range=['#EF553B', '#AB63FA', '#00CC96'])), 
                    tooltip=['Type', 'Amount']
                )
                st.altair_chart(donut, use_container_width=True)

            st.divider()
            
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                st.subheader("📅 Spending Trend (Daily)")
                st.info("**Why this is useful:** Spikes in the line show exactly *when* you overspent.")
                if 'Date' in transactions.columns:
                    trend_data = transactions.groupby('Date')['Amount'].sum().reset_index()
                    line_chart = alt.Chart(trend_data).mark_line(point=True).encode(
                        x='Date', y='Amount', tooltip=['Date', 'Amount']
                    ).properties(height=300)
                    st.altair_chart(line_chart, use_container_width=True)
                else:
                    st.info("Upload CSV with 'Date' column to see trends.")

            with r2c2:
                st.subheader("🆚 You vs. National Average")
                st.info("""
                **How to read this (RAG):**
                🟥 **Red Bar:** Your Monthly Avg.
                🟦 **Teal Bar:** National Avg (BLS Data).
                *Goal: Keep Red lower than Teal!*
                """)
                if not benchmarks_df.empty:
                    user_cat = transactions.groupby('Category')['Amount'].sum().reset_index()
                    user_cat['Amount'] = user_cat['Amount'] / num_months
                    comparison = pd.merge(user_cat, benchmarks_df, on='Category', how='inner')
                    if not comparison.empty:
                        comp_melt = comparison.melt(id_vars='Category', value_vars=['Amount', 'Average_Monthly_Cost'], var_name='Source', value_name='Cost')
                        comp_chart = alt.Chart(comp_melt).mark_bar().encode(
                            x=alt.X('Category', axis=alt.Axis(labelAngle=-45)),
                            y='Cost',
                            color=alt.Color('Source', scale=alt.Scale(domain=['Amount', 'Average_Monthly_Cost'], range=['#EF553B', '#4ECDC4']), legend=None),
                            tooltip=['Category', 'Cost', 'Source']
                        ).properties(height=300)
                        st.altair_chart(comp_chart, use_container_width=True)
                    else:
                        st.info("Spending categories didn't match National Benchmark labels exactly.")
                else:
                    st.warning("Benchmark data missing. Run fetch_data.py")

    elif st.session_state.current_view == "🎛️ Savings Simulator":
        if transactions.empty:
            st.info("👋 Upload data to use the Savings Simulator.")
        else:
            st.subheader("🎛️ Interactive Savings Simulator")
            st.info("**What is this?** This tool uses your average monthly 'Wants' spending. Move the slider to see potential savings.")
            
            col_sim_1, col_sim_2 = st.columns(2)
            with col_sim_1:
                st.markdown("#### Adjust Reduction Goal")
                cut_percentage = st.slider("I want to cut my 'Wants' spending by:", 0, 50, 10, format="%d%%")
            
            with col_sim_2:
                potential_savings = wants_monthly * (cut_percentage / 100)
                annual_savings = potential_savings * 12
                st.markdown("#### Projected Results")
                st.metric(f"Monthly Savings", f"${potential_savings:,.2f}")
                st.metric(f"Yearly Savings", f"${annual_savings:,.2f}", delta="Extra Cash!")


    elif st.session_state.current_view == "🤖 Gemini Chat Agent":
        st.subheader("💬 Chat with Gemini")
        st.caption("The agent analyzes your MONTHLY AVERAGE data to answer questions.")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Ask: 'Where can I save money?'"):
        
        st.session_state.current_view = "🤖 Gemini Chat Agent"
      
        st.session_state.messages.append({"role": "user", "content": prompt})
        rag_context = ""
        if not benchmarks_df.empty:
             rag_context = f"\nOFFICIAL US BENCHMARKS (BLS 2023):\n{benchmarks_df.to_string(index=False)}"

        data_context = ""
        if not transactions.empty:
            data_context = f"""
            DATA PERIOD: {num_months} Months
            USER MONTHLY INCOME: ${income:,.2f}
            USER AVG MONTHLY SPEND: ${monthly_spend:,.2f}
            GRADE: {grade}
            MONTHLY 50/30/20 BREAKDOWN (Averages):
            - NEEDS: ${needs_monthly:,.2f}
            - WANTS: ${wants_monthly:,.2f}
            - SAVINGS: ${savings_monthly:,.2f}
            CATEGORY BREAKDOWN (Monthly Averages):
            {cat_str}
            """
        else:
            data_context = "User has NOT uploaded specific data yet. Answer general financial questions."

        try:
            full_prompt = f"""
            You are an expert Financial Agent powered by Gemini. 
            
            DATA CONTEXT (Use these exact numbers):
            {data_context}
            
            EXTERNAL KNOWLEDGE (RAG):
            {rag_context}
            
            USER QUESTION: {prompt}
            
            INSTRUCTIONS:
            1. FORMATTING: Use Markdown. Bullet points for lists.
            2. NO BOLDING: Do NOT bold currency values (e.g., write $500.00).
            3. CITATION: Cite specific numbers from the data context.
            4. TONE: Professional and helpful.
            """
            
            with st.spinner("Analyzing your finances..."):
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(full_prompt)
                
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # 5. FORCE RERUN TO UPDATE VIEW
                st.rerun()
                
        except Exception as e:
            st.error(f"Agent Error: {e}")

if __name__ == "__main__":
    main()
    
