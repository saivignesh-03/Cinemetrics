import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# --------------------
# Database Connection Setup
# --------------------

def get_connection():
    return psycopg2.connect(
        host="dpg-d05ff0ili9vc738ohfbg-a.oregon-postgres.render.com",
        database="cinimetrics",
        user="cinimetrics_user",
        password="64c5SUsHLV9duIqELB3mSW4fl5pZBuDy",
        port="5432"
    )

# --------------------
# Helper Functions
# --------------------

@st.cache_data
def fetch_query(query, params=None):
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df.copy()

@st.cache_data
def fetch_custom_query(user_query):
    with get_connection() as conn:
        df = pd.read_sql_query(user_query, conn)
    return df.copy()

def display_dataframe(df):
    if not df.empty:
        filter_col = st.selectbox("Select column to filter", df.columns)
        filter_val = st.text_input(f"Search in {filter_col}")
        if filter_val:
            df = df[df[filter_col].astype(str).str.contains(filter_val, case=False)]
    st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)

# --------------------
# Streamlit App
# --------------------

def main():
    st.set_page_config(page_title="CineMetrics Dashboard", layout="wide")
    st.title("🎬 CineMetrics: Theatre Chain Management Dashboard")

    # Homepage Metrics
    st.header("📊 Quick Insights")
    col1, col2, col3 = st.columns(3)

    with col1:
        movie_counts = fetch_query("SELECT COUNT(*) FROM Movies")
        st.metric("Total Movies", movie_counts.iloc[0,0])

    with col2:
        customer_counts = fetch_query("SELECT COUNT(*) FROM Customer_Contacts")
        st.metric("Total Customers", customer_counts.iloc[0,0])

    with col3:
        transaction_counts = fetch_query("SELECT COUNT(*) FROM Transactions")
        st.metric("Total Transactions", transaction_counts.iloc[0,0])

    st.subheader("Revenue Trend (Sample)")
    revenue_data = fetch_query("""
        SELECT booking_date::date as date, SUM(total_amount) as revenue
        FROM Transactions
        GROUP BY date
        ORDER BY date
    """)
    fig = px.line(revenue_data, x="date", y="revenue", title="Daily Revenue")
    st.plotly_chart(fig, use_container_width=True)

    # Tabs
    tabs = st.tabs(["📽 Movies", "🏛️ Theatres", "👥 Customers", "👷 Staff", "🍟 Food Sales", "💳 Transactions", "🎁 Promotions", "🛠 Query Tool"])

    with tabs[0]:
        st.header("Movies and Screening Schedules")
        df = fetch_query("""
            SELECT m.name AS movie_name, m.rating, m.production_house,
                   s.show_date, s.show_time, s.available_seats,
                   sr.screen_no, t.name AS theatre_name, t.city
            FROM Screening_Schedule s
            JOIN Movies m ON s.movie_id = m.movie_id
            JOIN Screen_Registry sr ON s.screen_id = sr.screen_id
            JOIN Theatres t ON sr.theatre_id = t.theatre_id
            ORDER BY s.show_date, s.show_time
        """)
        display_dataframe(df)

    with tabs[1]:
        st.header("Theatres and Screens")
        df = fetch_query("""
            SELECT t.name AS theatre_name, t.address, t.city, t.state,
                   sd.screen_type, sd.capacity, sr.screen_no
            FROM Theatres t
            JOIN Screen_Registry sr ON t.theatre_id = sr.theatre_id
            JOIN Screen_Details sd ON sr.screen_id = sd.screen_id
            ORDER BY t.name, sr.screen_no
        """)
        display_dataframe(df)

    with tabs[2]:
        st.header("Customer Details")
        df = fetch_query("SELECT customer_name, email_id, contact_no FROM Customer_Contacts ORDER BY customer_name")
        display_dataframe(df)

    with tabs[3]:
        st.header("Staff and Shifts")
        df = fetch_query("""
            SELECT ts.staff_id, ts.email, ts.role, ts.salary,
                   t.name AS theatre_name,
                   ds.shift_date, ds.shift_start_time, ds.shift_end_time
            FROM Theatre_Staff_ID_Map ts
            JOIN Theatres t ON ts.theatre_id = t.theatre_id
            LEFT JOIN Daily_Shifts ds ON ts.staff_id = ds.staff_id
            ORDER BY ts.staff_id, ds.shift_date
        """)
        display_dataframe(df)

    with tabs[4]:
        st.header("Food Sales")
        df = fetch_query("""
            SELECT fd.food_name, fd.price, tr.transaction_id,
                   tr.booking_date, tr.total_amount
            FROM Food_Details fd
            JOIN Transactions tr ON fd.transaction_id = tr.transaction_id
            ORDER BY tr.booking_date
        """)
        display_dataframe(df)

    with tabs[5]:
        st.header("Transactions")
        df = fetch_query("""
            SELECT tr.transaction_id, cc.customer_name,
                   tr.seats_booked, tr.ticket_price,
                   tr.food_amount, tr.total_amount, tr.booking_date
            FROM Transactions tr
            JOIN Customer_ID_Map cim ON tr.customer_id = cim.customer_id
            JOIN Customer_Contacts cc ON cim.email_id = cc.email_id
            ORDER BY tr.booking_date DESC
        """)
        display_dataframe(df)

    with tabs[6]:
        st.header("Promotions")
        df = fetch_query("""
            SELECT p.promo_code, p.discount_applied,
                   tr.transaction_id, tr.booking_date,
                   cc.customer_name
            FROM Promotions p
            JOIN Transactions tr ON p.transaction_id = tr.transaction_id
            JOIN Customer_ID_Map cim ON tr.customer_id = cim.customer_id
            JOIN Customer_Contacts cc ON cim.email_id = cc.email_id
            ORDER BY tr.booking_date
        """)
        display_dataframe(df)

    with tabs[7]:
        st.header("🛠 Custom Query Tool")
        st.subheader("Database Structure")
        st.code("""
CineMetrics DB
├─ Movies (movie_id PK)
├─ Theatres (theatre_id PK)
│  └─ Screen_Registry (screen_id PK, theatre_id FK)
│     ├─ Screen_Details (screen_id PK FK)
│     └─ Screening_Schedule (schedule_id PK, screen_id FK, movie_id FK)
│        └─ Transactions (transaction_id PK, customer_id FK, schedule_id FK)
│           ├─ Food_Details (food_id PK, transaction_id FK)
│           └─ Promotions (promo_id PK, transaction_id FK)
├─ Customer_Contacts (email_id PK)
│  └─ Customer_ID_Map (customer_id PK, email_id FK)
│     └─ Transactions … (see above)
├─ Theatre_Staff_ID_Map (staff_id PK, theatre_id FK, email FK)
│  ├─ Staff_Contacts (email PK FK)
│  └─ Daily_Shifts (shift_id PK, staff_id FK)

Example JOIN Queries
1️⃣  Movies playing in each theatre on a given date:
    SELECT t.name   AS theatre,
           m.name   AS movie,
           s.show_date,
           s.show_time
    FROM Screening_Schedule s
    JOIN Movies m         ON s.movie_id   = m.movie_id
    JOIN Screen_Registry sr ON s.screen_id = sr.screen_id
    JOIN Theatres t       ON sr.theatre_id = t.theatre_id
    WHERE s.show_date = CURRENT_DATE;

2️⃣  Total ticket revenue per movie:
    SELECT m.name AS movie,
           SUM(tr.total_amount) AS total_revenue
    FROM Transactions tr
    JOIN Screening_Schedule s ON tr.schedule_id = s.schedule_id
    JOIN Movies m            ON s.movie_id     = m.movie_id
    GROUP BY m.name
    ORDER BY total_revenue DESC;

3️⃣  Staff shift roster for a specific theatre tomorrow:
    SELECT ts.staff_id,
           sc.full_name,
           ds.shift_date,
           ds.shift_start_time,
           ds.shift_end_time
    FROM Daily_Shifts ds
    JOIN Theatre_Staff_ID_Map ts ON ds.staff_id = ts.staff_id
    JOIN Staff_Contacts sc       ON ts.email    = sc.email
    WHERE ts.theatre_id = 1
      AND ds.shift_date = CURRENT_DATE + INTERVAL '1 day';
""")

        query = st.text_area("Enter your SQL Query")
        if st.button("Run Query") and query.strip():
            try:
                df = fetch_custom_query(query)
                st.success("Query successful!")
                display_dataframe(df)

                if not df.empty:
                    st.subheader("Plot Results")
                    cols = df.columns.tolist()
                    x_axis = st.selectbox("Select X-axis", cols)
                    y_axis = st.selectbox("Select Y-axis", [col for col in cols if col != x_axis])
                    chart_type = st.selectbox("Select Chart Type", ["Bar", "Line"])

                    if chart_type == "Bar":
                        fig = px.bar(df, x=x_axis, y=y_axis)
                    else:
                        fig = px.line(df, x=x_axis, y=y_axis)

                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {str(e)}")

# --------------------
# Run the App
# --------------------

if __name__ == "__main__":
    main()
