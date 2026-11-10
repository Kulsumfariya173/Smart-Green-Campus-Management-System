import sqlite3
import hashlib
import hmac
import os
import secrets
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Smart Green Campus",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = Path(__file__).with_name("campus.db")


# =====================================================
# 2. GREEN THEME AND CSS
# =====================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    --green-dark: #153c2b;
    --green-main: #26734a;
    --green-light: #e7f3e8;
    --green-card: #e2f1e5;
    --green-border: #b9d8c0;
    --page: #f5f8f4;
    --text: #20392a;
    --muted: #526b59;
}

.stApp {
    background: var(--page);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1450px;
    padding-top: 1.7rem;
    padding-bottom: 3rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--green-dark);
}

[data-testid="stSidebar"] * {
    color: #ffffff;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: var(--green-dark) !important;
    font-family: 'Manrope', sans-serif;
}

p, label, .stMarkdown, .stCaption {
    color: var(--text);
}

/* Dashboard hero */
.hero {
    background: linear-gradient(115deg, #153c2b, #368957);
    padding: 35px;
    border-radius: 20px;
    color: #ffffff;
    margin-bottom: 25px;
}

.hero h1, .hero p {
    color: #ffffff !important;
}

.eyebrow {
    color: #bce8c8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: var(--green-card) !important;
    border: 1px solid var(--green-border) !important;
    border-radius: 15px;
    padding: 19px;
}

/* Force metric labels and values to dark green */
div[data-testid="stMetric"] [data-testid="stMetricLabel"],
div[data-testid="stMetric"] [data-testid="stMetricLabel"] *,
div[data-testid="stMetric"] [data-testid="stMetricValue"],
div[data-testid="stMetric"] [data-testid="stMetricValue"] *,
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] p {
    color: #173d27 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #173d27 !important;
    font-weight: 800 !important;
}

div[data-testid="stMetricDelta"] {
    color: #26734a !important;
}

/* Forms */
div[data-testid="stForm"] {
    background: #edf7ee !important;
    border: 1px solid var(--green-border) !important;
    border-radius: 15px;
    padding: 24px;
}

.login-card {
    background: #edf7ee !important;
    border: 1px solid var(--green-border);
    border-radius: 20px;
    padding: 25px;
    max-width: 600px;
    margin: auto;
}

.login-note {
    background: #dcefe0;
    border-left: 4px solid var(--green-main);
    padding: 12px;
    border-radius: 8px;
    color: #244c32 !important;
    font-size: 13px;
}

/* Input fields */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: #f0f7f1 !important;
    color: #153c2b !important;
    border: 1px solid #b8d8bf !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #627968 !important;
    opacity: 1;
}

div[data-baseweb="select"] > div {
    background-color: #f0f7f1 !important;
    color: #153c2b !important;
    border-color: #b8d8bf !important;
}

div[data-baseweb="select"] * {
    color: #153c2b !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: #244c32 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #153c2b !important;
    border-bottom-color: #26734a !important;
}

/* Tables */
div[data-testid="stDataFrame"],
div[data-testid="stTable"] {
    background: #edf7ee !important;
    border: 1px solid var(--green-border) !important;
    border-radius: 10px;
}

/* Buttons */
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background: #26734a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 9px;
    font-weight: 700;
}

div.stButton > button,
div.stDownloadButton > button {
    border-radius: 9px;
}

/* Footer */
.footer {
    text-align: center;
    padding: 24px;
    color: #526b59;
}

hr {
    border-color: #cbdccb;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. DATABASE CONNECTION
# =====================================================

def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():

    with get_db() as db:

        db.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource TEXT NOT NULL,
                amount REAL NOT NULL,
                unit TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS waste_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                waste_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS administrators (
                username TEXT PRIMARY KEY,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        count = db.execute(
            "SELECT COUNT(*) FROM resources"
        ).fetchone()[0]

        if count == 0:

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            db.executemany("""
                INSERT INTO resources
                (resource, amount, unit, created_at)
                VALUES (?, ?, ?, ?)
            """, [
                ("Electricity", 1250, "kWh", now),
                ("Water", 3400, "litres", now)
            ])

        username = os.environ.get("GREEN_ADMIN_USER", "").strip()
        password = os.environ.get("GREEN_ADMIN_PASSWORD", "")

        if username and password:

            existing = db.execute(
                "SELECT username FROM administrators WHERE username = ?",
                (username,)
            ).fetchone()

            if not existing:

                salt = secrets.token_bytes(16)

                password_hash = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt,
                    600000
                ).hex()

                db.execute("""
                    INSERT INTO administrators
                    (username, password_salt, password_hash)
                    VALUES (?, ?, ?)
                """, (username, salt.hex(), password_hash))


initialize_database()


# =====================================================
# 4. DATABASE FUNCTIONS
# =====================================================

def get_latest_reading(resource):

    with get_db() as db:

        row = db.execute("""
            SELECT amount, unit, created_at
            FROM resources
            WHERE resource = ?
            ORDER BY id DESC
            LIMIT 1
        """, (resource,)).fetchone()

    return dict(row) if row else {"amount": 0, "unit": ""}


def get_all_readings():

    with get_db() as db:

        rows = db.execute("""
            SELECT * FROM resources
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]


def get_complaints():

    with get_db() as db:

        rows = db.execute("""
            SELECT * FROM complaints
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]


def get_waste_records():

    with get_db() as db:

        rows = db.execute("""
            SELECT * FROM waste_records
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]


def get_waste_total():

    with get_db() as db:

        return db.execute("""
            SELECT COALESCE(SUM(quantity), 0)
            FROM waste_records
        """).fetchone()[0]


def fmt(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")


# =====================================================
# 5. ADMIN AUTHENTICATION
# =====================================================

def verify_admin(username, password):

    with get_db() as db:

        row = db.execute("""
            SELECT password_salt, password_hash
            FROM administrators
            WHERE username = ?
        """, (username,)).fetchone()

    if not row:
        return False

    salt = bytes.fromhex(row["password_salt"])

    attempted_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600000
    ).hex()

    return hmac.compare_digest(
        attempted_hash,
        row["password_hash"]
    )


# =====================================================
# 6. SESSION STATE
# =====================================================

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = ""

if "display_name" not in st.session_state:
    st.session_state.display_name = ""

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False


# =====================================================
# 7. LOGIN PAGE
# =====================================================

def show_login_page():

    st.markdown("""
    <div style="text-align:center;padding:15px;">
        <div style="font-size:50px;">🌿</div>
        <h1>Smart Green Campus</h1>
        <p style="color:#687b6d;">
            Management System
            <br>
            Sustainable Today, Greener Tomorrow
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="login-card">',
        unsafe_allow_html=True
    )

    st.subheader("Sign In")
    st.caption("Select your access type to continue.")

    user_tab, admin_tab = st.tabs([
        "🎓 Student / Staff",
        "🔐 Administrator"
    ])

    with user_tab:

        with st.form("user_login_form"):

            name = st.text_input(
                "Your Name",
                placeholder="Enter your name"
            )

            role = st.selectbox(
                "Login As",
                ["Student", "Staff"]
            )

            submitted = st.form_submit_button(
                "Continue to Campus Portal",
                type="primary",
                use_container_width=True
            )

        if submitted:

            if not name.strip():

                st.error("Please enter your name.")

            else:

                st.session_state.user_logged_in = True
                st.session_state.user_role = role
                st.session_state.display_name = name.strip()
                st.session_state.admin_logged_in = False

                st.rerun()

        st.markdown("""
        <div class="login-note">
            Student/Staff access is a role-selection demonstration.
            Individual accounts are not verified in this prototype.
        </div>
        """, unsafe_allow_html=True)

    with admin_tab:

        with st.form("admin_login_form"):

            username = st.text_input("Administrator Username")

            password = st.text_input(
                "Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Administrator Login",
                type="primary",
                use_container_width=True
            )

        if submitted:

            if verify_admin(username.strip(), password):

                st.session_state.user_logged_in = True
                st.session_state.user_role = "Administrator"
                st.session_state.display_name = username.strip()
                st.session_state.admin_logged_in = True

                st.rerun()

            else:

                st.error("Invalid username or password.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        🌱 Smart Green Campus Management System
    </div>
    """, unsafe_allow_html=True)


if not st.session_state.user_logged_in:

    show_login_page()
    st.stop()


# =====================================================
# 8. SIDEBAR NAVIGATION
# =====================================================

st.sidebar.markdown("# 🌿 GreenCampus")
st.sidebar.caption("SMART SUSTAINABILITY PORTAL")
st.sidebar.divider()

st.sidebar.write(
    f"Welcome, **{st.session_state.display_name}**"
)

st.sidebar.caption(
    f"Access: {st.session_state.user_role}"
)

pages = [
    "🏠 Dashboard",
    "⚡ Resource Monitoring",
    "♻️ Waste Management",
    "📝 Report an Issue",
    "📋 Complaint Tracking"
]

if st.session_state.admin_logged_in:
    pages.append("🔐 Administrator")

page = st.sidebar.radio("NAVIGATION", pages)

st.sidebar.divider()

if st.sidebar.button("Log Out", use_container_width=True):

    st.session_state.user_logged_in = False
    st.session_state.user_role = ""
    st.session_state.display_name = ""
    st.session_state.admin_logged_in = False

    st.rerun()

st.sidebar.success("Small actions create a greener campus.")
st.sidebar.caption("Academic project prototype")


# =====================================================
# 9. DASHBOARD
# =====================================================

if page == "🏠 Dashboard":

    st.markdown("""
    <div class="hero">
        <span class="eyebrow">
            SMART GREEN CAMPUS MANAGEMENT SYSTEM
        </span>
        <h1>Building a Greener Campus 🌱</h1>
        <p>
            Monitor resources, reduce waste, manage environmental issues,
            and make our campus more sustainable.
        </p>
    </div>
    """, unsafe_allow_html=True)

    electricity = get_latest_reading("Electricity")
    water = get_latest_reading("Water")
    complaints = get_complaints()
    waste_total = get_waste_total()

    pending_count = sum(
        item["status"] == "Pending"
        for item in complaints
    )

    st.subheader("Campus at a Glance")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "⚡ Electricity Usage",
        f'{fmt(electricity["amount"])} kWh'
    )

    col2.metric(
        "💧 Water Consumption",
        f'{fmt(water["amount"])} L'
    )

    col3.metric(
        "♻️ Waste Logged",
        f"{fmt(waste_total)} kg"
    )

    col4.metric(
        "📝 Pending Reports",
        str(pending_count)
    )

    st.caption(
        "Initial electricity and water readings are illustrative demo data."
    )

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:

        st.subheader("📈 Resource Consumption")

        readings = get_all_readings()
        history_df = pd.DataFrame(readings)

        if not history_df.empty:

            history_df["created_at"] = pd.to_datetime(
                history_df["created_at"],
                errors="coerce"
            )

            chart_df = history_df.pivot_table(
                index="created_at",
                columns="resource",
                values="amount",
                aggfunc="last"
            ).sort_index()

            st.line_chart(chart_df)

        else:

            st.info("Add resource readings to view the chart.")

    with right:

        st.subheader("🎯 Sustainability Goals")

        goals = [
            ("♻️ Waste Recycling", 78),
            ("💧 Water Conservation", 65),
            ("⚡ Energy Efficiency", 82)
        ]

        for name, percentage in goals:

            st.write(f"**{name}**")
            st.progress(percentage / 100)
            st.caption(f"{percentage}% illustrative progress")

    st.divider()

    st.subheader("📋 Recent Environmental Reports")

    if complaints:

        recent_df = pd.DataFrame(complaints[:5])

        st.dataframe(
            recent_df[
                ["id", "category", "location", "status", "created_at"]
            ].rename(columns={
                "id": "Report ID",
                "category": "Category",
                "location": "Location",
                "status": "Status",
                "created_at": "Submitted At"
            }),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No reports submitted yet.")


# =====================================================
# 10. RESOURCE MONITORING
# =====================================================

elif page == "⚡ Resource Monitoring":

    st.title("⚡ Resource Monitoring")

    st.write(
        "Record and analyse campus electricity and water consumption."
    )

    electricity = get_latest_reading("Electricity")
    water = get_latest_reading("Water")

    col1, col2 = st.columns(2)

    col1.metric(
        "Electricity",
        f'{electricity["amount"]} kWh'
    )

    col2.metric(
        "Water",
        f'{water["amount"]} litres'
    )

    st.divider()

    st.subheader("Add a New Reading")

    with st.form("resource_form"):

        resource = st.selectbox(
            "Resource",
            ["Electricity", "Water"]
        )

        amount = st.number_input(
            "Reading",
            min_value=0.0,
            max_value=100000000.0,
            value=100.0,
            step=10.0
        )

        submitted = st.form_submit_button(
            "Save Reading",
            type="primary"
        )

        if submitted:

            unit = "kWh" if resource == "Electricity" else "litres"

            with get_db() as db:

                db.execute("""
                    INSERT INTO resources
                    (resource, amount, unit, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    resource,
                    amount,
                    unit,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            st.success("Resource reading saved successfully!")
            st.rerun()

    st.subheader("Resource Reading History")

    readings = get_all_readings()

    if readings:

        df = pd.DataFrame(readings)

        st.dataframe(
            df.rename(columns={
                "id": "Record ID",
                "resource": "Resource",
                "amount": "Reading",
                "unit": "Unit",
                "created_at": "Date"
            }),
            use_container_width=True,
            hide_index=True
        )

        selected = st.selectbox(
            "Chart Resource",
            ["Electricity", "Water"]
        )

        chart_df = pd.DataFrame([
            row for row in readings
            if row["resource"] == selected
        ])

        if not chart_df.empty:

            chart_df["created_at"] = pd.to_datetime(
                chart_df["created_at"],
                errors="coerce"
            )

            chart_df = chart_df.sort_values("created_at")

            st.line_chart(
                chart_df.set_index("created_at")["amount"]
            )

    else:

        st.info("No readings available.")


# =====================================================
# 11. WASTE MANAGEMENT
# =====================================================

elif page == "♻️ Waste Management":

    st.title("♻️ Smart Waste Management")

    st.write(
        "Record waste collection and review waste categories."
    )

    st.info(
        "Separate waste into recyclable, organic, general, and electronic waste."
    )

    with st.form("waste_form"):

        waste_type = st.selectbox(
            "Waste Category",
            ["Recyclable", "Organic", "General", "E-waste"]
        )

        quantity = st.number_input(
            "Quantity Collected (kg)",
            min_value=0.01,
            max_value=100000.0,
            value=1.0,
            step=0.5
        )

        submitted = st.form_submit_button(
            "Save Waste Record",
            type="primary"
        )

        if submitted:

            with get_db() as db:

                db.execute("""
                    INSERT INTO waste_records
                    (waste_type, quantity, created_at)
                    VALUES (?, ?, ?)
                """, (
                    waste_type,
                    quantity,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            st.success("Waste record saved successfully!")
            st.rerun()

    records = get_waste_records()

    st.metric(
        "Total Waste Logged",
        f"{fmt(get_waste_total())} kg"
    )

    if records:

        waste_df = pd.DataFrame(records)

        summary = waste_df.groupby(
            "waste_type"
        )["quantity"].sum()

        st.subheader("Waste by Category")
        st.bar_chart(summary)

        st.subheader("Collection History")

        st.dataframe(
            waste_df.rename(columns={
                "id": "Record ID",
                "waste_type": "Waste Type",
                "quantity": "Quantity (kg)",
                "created_at": "Date"
            }),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No waste records available.")


# =====================================================
# 12. ENVIRONMENTAL ISSUE REPORTING
# =====================================================

elif page == "📝 Report an Issue":

    st.title("📝 Report an Environmental Issue")

    st.write(
        "Report water leaks, overflowing bins, energy wastage, "
        "or green-space maintenance problems."
    )

    with st.form("complaint_form", clear_on_submit=True):

        category = st.selectbox(
            "Issue Category",
            [
                "Select a category",
                "Water Leakage",
                "Overflowing Waste Bin",
                "Electricity Wastage",
                "Green Space Maintenance",
                "Other"
            ]
        )

        location = st.text_input(
            "Campus Location",
            placeholder="e.g. Block A, Ground Floor",
            max_chars=150
        )

        description = st.text_area(
            "Description",
            placeholder="Describe the environmental issue...",
            max_chars=1000
        )

        submitted = st.form_submit_button(
            "Submit Report",
            type="primary"
        )

        if submitted:

            if category == "Select a category":

                st.error("Please select a valid category.")

            elif not location.strip():

                st.error("Please enter the campus location.")

            elif not description.strip():

                st.error("Please describe the issue.")

            else:

                with get_db() as db:

                    cursor = db.execute("""
                        INSERT INTO complaints
                        (category, location, description, status, created_at)
                        VALUES (?, ?, ?, 'Pending', ?)
                    """, (
                        category,
                        location.strip(),
                        description.strip(),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                    report_id = cursor.lastrowid

                st.success(
                    "Environmental report submitted successfully!"
                )

                st.info(
                    f"Reference Number: GC-{report_id:04d} | Status: Pending"
                )

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.info("💧 **Water Issues**\n\nLeaks and water wastage.")
    col2.warning("♻️ **Waste Issues**\n\nOverflowing bins and segregation.")
    col3.success("⚡ **Energy Issues**\n\nUnnecessary electricity usage.")


# =====================================================
# 13. COMPLAINT TRACKING
# =====================================================

elif page == "📋 Complaint Tracking":

    st.title("📋 Complaint Tracking")

    complaints = get_complaints()

    if not complaints:

        st.info("No complaints have been submitted yet.")

    else:

        total = len(complaints)

        pending = sum(
            item["status"] == "Pending"
            for item in complaints
        )

        progress_count = sum(
            item["status"] == "In Progress"
            for item in complaints
        )

        resolved = sum(
            item["status"] == "Resolved"
            for item in complaints
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Reports", total)
        col2.metric("Pending", pending)
        col3.metric("In Progress", progress_count)
        col4.metric("Resolved", resolved)

        st.subheader("All Environmental Reports")

        df = pd.DataFrame(complaints)

        st.dataframe(
            df.rename(columns={
                "id": "Report ID",
                "category": "Category",
                "location": "Location",
                "description": "Description",
                "status": "Status",
                "created_at": "Submitted At"
            }),
            use_container_width=True,
            hide_index=True
        )

        if st.session_state.admin_logged_in:

            st.divider()

            st.subheader("Administrator: Update Report Status")

            selected_id = st.selectbox(
                "Select Report ID",
                [item["id"] for item in complaints]
            )

            selected_report = next(
                item for item in complaints
                if item["id"] == selected_id
            )

            status_options = [
                "Pending",
                "In Progress",
                "Resolved"
            ]

            new_status = st.selectbox(
                "New Status",
                status_options,
                index=status_options.index(
                    selected_report["status"]
                )
            )

            if st.button("Update Status", type="primary"):

                with get_db() as db:

                    db.execute("""
                        UPDATE complaints
                        SET status = ?
                        WHERE id = ?
                    """, (new_status, selected_id))

                st.success("Complaint status updated!")
                st.rerun()

        else:

            st.info(
                "Administrator login is required to update complaint statuses."
            )


# =====================================================
# 14. ADMINISTRATOR PORTAL
# =====================================================

elif page == "🔐 Administrator":

    st.title("🔐 Administrator Portal")

    if not st.session_state.admin_logged_in:

        st.error("Administrator authentication required.")

    else:

        st.success("You are signed in as administrator.")

        complaints = get_complaints()
        resources = get_all_readings()
        waste = get_waste_records()

        col1, col2, col3 = st.columns(3)

        col1.metric("Environmental Reports", len(complaints))
        col2.metric("Resource Readings", len(resources))
        col3.metric("Waste Records", len(waste))

        st.subheader("Environmental Report Overview")

        if complaints:

            st.dataframe(
                pd.DataFrame(complaints),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No environmental reports have been submitted.")

        st.subheader("Export Environmental Reports")

        if complaints:

            csv = pd.DataFrame(complaints).to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "Download Reports as CSV",
                data=csv,
                file_name="campus_environmental_reports.csv",
                mime="text/csv"
            )


# =====================================================
# 15. FOOTER
# =====================================================

st.divider()

st.markdown("""
<div class="footer">
    <h3>🌱 Smart Green Campus Management System</h3>
    <p>Sustainable Today, Greener Tomorrow</p>
    <small>
        Academic project prototype · Initial resource readings and
        sustainability targets are illustrative.
    </small>
</div>
""", unsafe_allow_html=True)