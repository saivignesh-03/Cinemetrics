import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# --------------------
# Database Connection Setup
# --------------------

def get_connection():
    """Return a new Postgres connection (Render)"""
    return psycopg2.connect(
        host="dpg-d05ff0ili9vc738ohfbg-a.oregon-postgres.render.com",
        database="cinimetrics",
        user="cinimetrics_user",
        password="64c5SUsHLV9duIqELB3mSW4fl5pZBuDy",
        port="5432"
    )

# --------------------
# Generic query helpers (results are cached)
# --------------------

@st.cache_data(show_spinner="Running SQL …")
def fetch_query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    """Run a read‑only query and cache the resulting DataFrame."""
    with get_connection() as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    return df.copy()

@st.cache_data(show_spinner="Running custom SQL …")
def fetch_custom_query(sql: str) -> pd.DataFrame:
    """User‑supplied query (keyed by the exact SQL string)."""
    with get_connection() as conn:
        df = pd.read_sql_query(sql, conn)
    return df.copy()

# --------------------
# UI helper
# --------------------

def display_dataframe(df: pd.DataFrame, key_prefix: str = "table") -> None:
    """Show df with simple column filter without re‑querying DB."""
    if df.empty:
        st.info("No rows returned.")
        return

    filter_col = st.selectbox(
        "Select column to filter", df.columns, key=f"{key_prefix}_filtercol"
    )
    filter_val = st.text_input(
        f"Search in {filter_col}", key=f"{key_prefix}_filterval"
    )
    if filter_val:
        df = df[df[filter_col].astype(str).str.contains(filter_val, case=False)]

    st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")

# --------------------
# Streamlit App
# --------------------

def main():
    st.set_page_config(page_title="CineMetrics Dashboard", layout="wide")
    st.title("🎬 CineMetrics: Theatre Chain Management Dashboard")

    # --------------------
    # Homepage Metrics (cached queries)
    # --------------------
    st.header("📊 Quick Insights")
    col1, col2, col3 = st.columns(3)

    with col1:
        movies_cnt = fetch_query("SELECT COUNT(*) FROM Movies")
        st.metric("Total Movies", movies_cnt.iat[0, 0])

    with col2:
        cust_cnt = fetch_query("SELECT COUNT(*) FROM Customer_Contacts")
        st.metric("Total Customers", cust_cnt.iat[0, 0])

    with col3:
        txn_cnt = fetch_query("SELECT COUNT(*) FROM Transactions")
        st.metric("Total Transactions", txn_cnt.iat[0, 0])

    st.subheader("Revenue Trend")
    rev_df = fetch_query(
        """
        SELECT booking_date::date AS day, SUM(total_amount) AS revenue
        FROM Transactions
        GROUP BY day
        ORDER BY day
        """
    )
    st.plotly_chart(px.line(rev_df, x="day", y="revenue"), use_container_width=True)

    # --------------------
    # Tabs
    # --------------------
    tabs = st.tabs([
        "📽 Movies", "🏛️ Theatres", "👥 Customers", "👷 Staff",
        "🍟 Food Sales", "💳 Transactions", "🎁 Promotions", "🛠 Query Tool", "🔐 Admin Console"
    ])

    # — Movies
    with tabs[0]:
        st.header("Movies and Screening Schedules")
        movies_df = fetch_query(
            """
            SELECT m.name AS movie_name, m.rating, m.production_house,
                   s.show_date, s.show_time, s.available_seats,
                   sr.screen_no, t.name AS theatre_name, t.city
            FROM Screening_Schedule s
            JOIN Movies m  ON s.movie_id   = m.movie_id
            JOIN Screen_Registry sr ON s.screen_id  = sr.screen_id
            JOIN Theatres t ON sr.theatre_id = t.theatre_id
            ORDER BY s.show_date, s.show_time
            """
        )
        display_dataframe(movies_df, key_prefix="movies")

    # — Theatres
    with tabs[1]:
        st.header("Theatres and Screens")
        th_df = fetch_query(
            """
            SELECT t.name AS theatre_name, t.address, t.city, t.state,
                   sd.screen_type, sd.capacity, sr.screen_no
            FROM Theatres t
            JOIN Screen_Registry sr ON t.theatre_id = sr.theatre_id
            JOIN Screen_Details sd ON sr.screen_id   = sd.screen_id
            ORDER BY t.name, sr.screen_no
            """
        )
        display_dataframe(th_df, key_prefix="theatres")

    # — Customers
    with tabs[2]:
        st.header("Customer Details")
        cust_df = fetch_query(
            "SELECT customer_name, email_id, contact_no FROM Customer_Contacts ORDER BY customer_name"
        )
        display_dataframe(cust_df, key_prefix="customers")

    # — Staff
    with tabs[3]:
        st.header("Staff and Shifts")
        staff_df = fetch_query(
            """
            SELECT ts.staff_id, ts.email, ts.role, ts.salary,
                   t.name AS theatre_name,
                   ds.shift_date, ds.shift_start_time, ds.shift_end_time
            FROM Theatre_Staff_ID_Map ts
            JOIN Theatres t ON ts.theatre_id = t.theatre_id
            LEFT JOIN Daily_Shifts ds ON ts.staff_id = ds.staff_id
            ORDER BY ts.staff_id, ds.shift_date
            """
        )
        display_dataframe(staff_df, key_prefix="staff")

    # — Food Sales
    with tabs[4]:
        st.header("Food Sales")
        food_df = fetch_query(
            """
            SELECT fd.food_name, fd.price, tr.transaction_id,
                   tr.booking_date, tr.total_amount
            FROM Food_Details fd
            JOIN Transactions tr ON fd.transaction_id = tr.transaction_id
            ORDER BY tr.booking_date
            """
        )
        display_dataframe(food_df, key_prefix="food")

    # — Transactions
    with tabs[5]:
        st.header("Transactions")
        txn_df = fetch_query(
            """
            SELECT tr.transaction_id, cc.customer_name,
                   tr.seats_booked, tr.ticket_price,
                   tr.food_amount, tr.total_amount, tr.booking_date
            FROM Transactions tr
            JOIN Customer_ID_Map cim ON tr.customer_id = cim.customer_id
            JOIN Customer_Contacts cc ON cim.email_id   = cc.email_id
            ORDER BY tr.booking_date DESC
            """
        )
        display_dataframe(txn_df, key_prefix="transactions")

    # — Promotions
    with tabs[6]:
        st.header("Promotions")
        promo_df = fetch_query(
            """
            SELECT p.promo_code, p.discount_applied,
                   tr.transaction_id, tr.booking_date,
                   cc.customer_name
            FROM Promotions p
            JOIN Transactions tr ON p.transaction_id = tr.transaction_id
            JOIN Customer_ID_Map cim ON tr.customer_id = cim.customer_id
            JOIN Customer_Contacts cc ON cim.email_id   = cc.email_id
            ORDER BY tr.booking_date
            """
        )
        display_dataframe(promo_df, key_prefix="promotions")

    # — Query Tool
    with tabs[7]:
        st.header("🛠 Custom Query Tool")
        st.markdown(
    """
<span style="color:#1f77b4"><b>Movies</b></span>
&nbsp;(movie_id PK, name, genre, rating, production_house)  
&nbsp;← <span style="color:#2ca02c"><b>Screening_Schedule</b></span>
&nbsp;(schedule_id PK, screen_id FK, movie_id FK, show_date, show_time, available_seats)  
&nbsp;← <span style="color:#2ca02c"><b>Screen_Registry</b></span>
&nbsp;(screen_id PK, theatre_id FK, screen_no)  
&nbsp;&nbsp;&nbsp;&nbsp;← <span style="color:#d62728"><b>Theatres</b></span>
&nbsp;(theatre_id PK, name, address, city, state)  
&nbsp;← <span style="color:#2ca02c"><b>Screen_Details</b></span>
&nbsp;(screen_id PK = FK, screen_type, capacity)  
&nbsp;← <span style="color:#2ca02c"><b>Transactions</b></span>
&nbsp;(transaction_id PK, customer_id FK, schedule_id FK, seats_booked, ticket_price, food_amount, total_amount, booking_date)  
&nbsp;&nbsp;&nbsp;&nbsp;├─ <span style="color:#9467bd"><b>Food_Details</b></span>
&nbsp;(food_id PK, transaction_id FK, food_name, price)  
&nbsp;&nbsp;&nbsp;&nbsp;└─ <span style="color:#9467bd"><b>Promotions</b></span>
&nbsp;(promo_id PK, transaction_id FK, promo_code, discount_applied)  

<br>

<span style="color:#1f77b4"><b>Customer_Contacts</b></span>
&nbsp;(email_id PK, customer_name, contact_no)  
&nbsp;← <span style="color:#2ca02c"><b>Customer_ID_Map</b></span>
&nbsp;(customer_id PK, email_id FK)  
&nbsp;← <span style="color:#2ca02c"><b>Transactions …</b></span> (see above)  

<br>

<span style="color:#1f77b4"><b>Theatre_Staff_ID_Map</b></span>
&nbsp;(staff_id PK, theatre_id FK, email FK, role, salary)  
&nbsp;↔ <span style="color:#8c564b"><b>Staff_Contacts</b></span>
&nbsp;(email PK, first_name, last_name, phone)  
&nbsp;← <span style="color:#8c564b"><b>Daily_Shifts</b></span>
&nbsp;(shift_id PK, staff_id FK, shift_date, shift_start_time, shift_end_time)
    """,
    unsafe_allow_html=True,
)
        query = st.text_area("Enter your SQL query here", key="sql_text")
        run_btn = st.button("Run Query", key="run_query_btn")

        if run_btn and query.strip():
            try:
                @st.cache_data(show_spinner=True)
                def _run_sql(q):
                    with get_connection() as conn:
                        df_ = pd.read_sql_query(q, conn)
                    return df_.copy()

                st.session_state["query_df"] = _run_sql(query)
                st.success("Query executed and cached!")

            except Exception as e:
                st.error(f"❌ {e}")

        if "query_df" in st.session_state:
            df = st.session_state["query_df"]
            st.subheader("Result")
            display_dataframe(df)

            if not df.empty:
                st.subheader("Plot Result")
                with st.form(key="plot_form"):
                    cols = df.columns.tolist()
                    x_axis = st.selectbox("X-axis column", cols, key="plot_x")
                    y_axis = st.selectbox(
                        "Y-axis column",
                        [c for c in cols if c != x_axis],
                        key="plot_y"
                    )
                    chart_type = st.radio("Chart type", ("Bar", "Line"), key="plot_type")
                    submitted = st.form_submit_button("Create chart")

                if submitted:
                    if chart_type == "Bar":
                        fig = px.bar(df, x=x_axis, y=y_axis)
                    else:
                        fig = px.line(df, x=x_axis, y=y_axis)

                    st.plotly_chart(fig, use_container_width=True)

    # — Admin Console
    with tabs[8]:
        st.header("🔐 Admin Console (Insert | Update | Delete)")
        st.markdown(
    """
<span style="color:#1f77b4"><b>Movies</b></span>
&nbsp;(movie_id PK, name, genre, rating, production_house)  
&nbsp;← <span style="color:#2ca02c"><b>Screening_Schedule</b></span>
&nbsp;(schedule_id PK, screen_id FK, movie_id FK, show_date, show_time, available_seats)  
&nbsp;← <span style="color:#2ca02c"><b>Screen_Registry</b></span>
&nbsp;(screen_id PK, theatre_id FK, screen_no)  
&nbsp;&nbsp;&nbsp;&nbsp;← <span style="color:#d62728"><b>Theatres</b></span>
&nbsp;(theatre_id PK, name, address, city, state)  
&nbsp;← <span style="color:#2ca02c"><b>Screen_Details</b></span>
&nbsp;(screen_id PK = FK, screen_type, capacity)  
&nbsp;← <span style="color:#2ca02c"><b>Transactions</b></span>
&nbsp;(transaction_id PK, customer_id FK, schedule_id FK, seats_booked, ticket_price, food_amount, total_amount, booking_date)  
&nbsp;&nbsp;&nbsp;&nbsp;├─ <span style="color:#9467bd"><b>Food_Details</b></span>
&nbsp;(food_id PK, transaction_id FK, food_name, price)  
&nbsp;&nbsp;&nbsp;&nbsp;└─ <span style="color:#9467bd"><b>Promotions</b></span>
&nbsp;(promo_id PK, transaction_id FK, promo_code, discount_applied)  

<br>

<span style="color:#1f77b4"><b>Customer_Contacts</b></span>
&nbsp;(email_id PK, customer_name, contact_no)  
&nbsp;← <span style="color:#2ca02c"><b>Customer_ID_Map</b></span>
&nbsp;(customer_id PK, email_id FK)  
&nbsp;← <span style="color:#2ca02c"><b>Transactions …</b></span> (see above)  

<br>

<span style="color:#1f77b4"><b>Theatre_Staff_ID_Map</b></span>
&nbsp;(staff_id PK, theatre_id FK, email FK, role, salary)  
&nbsp;↔ <span style="color:#8c564b"><b>Staff_Contacts</b></span>
&nbsp;(email PK, first_name, last_name, phone)  
&nbsp;← <span style="color:#8c564b"><b>Daily_Shifts</b></span>
&nbsp;(shift_id PK, staff_id FK, shift_date, shift_start_time, shift_end_time)
    """,
    unsafe_allow_html=True,
)
        st.markdown(
                """
**Allowed operations**

* `INSERT INTO customer_contacts
(email_id, customer_name, contact_no)
VALUES
('alice.wson@cie.com', 'Aice Wilon', '9-222-1234');`
* `UPDATE customer_contacts
SET contact_no = '9-222-1234'
WHERE email_id = 'alice.wilson@cine.com';`
* `DELETE FROM customer_contacts
WHERE email_id = 'alice.wson@cie.com';`
""")
        st.warning("⚠️ Write operations affect the live database – proceed carefully.")

        pwd_ok = st.text_input("Enter admin password", type="password") == "incredible"
        if pwd_ok:
            st.success("Authenticated!")

            sql_write = st.text_area("SQL (INSERT / UPDATE / DELETE)", key="write_sql")
            if st.button("Execute", key="exec_write") and sql_write.strip():
                try:
                    with get_connection() as conn, conn.cursor() as cur:
                        cur.execute(sql_write)
                        conn.commit()
                    st.success("✅ Statement executed.")
                    fetch_query.clear()
                    fetch_custom_query.clear()
                except Exception as e:
                    st.error(f"❌ {e}")
        else:
            st.info("Enter the password to unlock admin actions.")

# --------------------
# Run the App
# --------------------

if __name__ == "__main__":
    main()