import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Joburg Load Trip Calculator",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# Custom CSS for a cleaner look
# -------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1F4E79;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #666;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E75B6;
    }
    .profit-positive {
        color: #006100;
        font-weight: 700;
        font-size: 1.4rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Session state defaults
# -------------------------------------------------
if "products" not in st.session_state:
    st.session_state.products = [
        {"name": "Chicken MDM", "brand": "", "cost": 0.58, "qty": 26400},
        {"name": "Chicken Feet", "brand": "", "cost": 1.45, "qty": 1840},
    ]

if "extra_fees" not in st.session_state:
    st.session_state.extra_fees = [
        {"name": "ZRA Taxes", "amount": 164564},
        {"name": "CPC", "amount": 15000},
        {"name": "Agent Fees", "amount": 5000},
        {"name": "Gate", "amount": 3000},
        {"name": "Scanner", "amount": 2000},
        {"name": "Kafue", "amount": 10000},
    ]

if "outbound" not in st.session_state:
    st.session_state.outbound = [
        {"desc": "Tolls Bridge Via Botswana", "amount": 2700, "currency": "ZMW"},
        {"desc": "Tolls Zam", "amount": 900, "currency": "ZMW"},
        {"desc": "Comesa", "amount": 945, "currency": "ZMW"},
        {"desc": "Tolls SA", "amount": 585, "currency": "ZMW"},
        {"desc": "Zambian Import Permit", "amount": 1500, "currency": "ZMW"},
        {"desc": "Driver Salary", "amount": 5000, "currency": "ZMW"},
        {"desc": "Driver Commission", "amount": 7500, "currency": "ZMW"},
    ]

if "fuel_entries" not in st.session_state:
    st.session_state.fuel_entries = [
        {"leg": "Outbound", "litres": 866.25, "price": 28.86, "currency": "ZMW"},
        {"leg": "Return", "litres": 750.0, "price": 25.40, "currency": "ZAR (RAND)"},
        {"leg": "Fridge Diesel", "litres": 200.0, "price": 26.86, "currency": "ZMW"},
    ]

if "return_exp" not in st.session_state:
    st.session_state.return_exp = [
        {"desc": "Mokopane Withdraw", "amount": 6350, "currency": "ZMW"},
        {"desc": "Joburg / Musina", "amount": 3810, "currency": "ZMW"},
        {"desc": "Toll Fees + Council Zambia", "amount": 1000, "currency": "ZMW"},
        {"desc": "Border & Permit Fees (USD converted)", "amount": 13014.40, "currency": "ZMW"},
    ]

if "sales" not in st.session_state:
    st.session_state.sales = [
        {"customer": "Wana", "product": "MDM", "qty": 5000, "price": 43},
        {"customer": "Phiroz", "product": "MDM", "qty": 10100, "price": 44},
        {"customer": "Coldroom/Sales", "product": "MDM", "qty": 5100, "price": 44},
        {"customer": "Coldroom/Sales", "product": "Chicken Feet", "qty": 1840, "price": 45},
        {"customer": "MDM Pre Payment", "product": "MDM", "qty": 6200, "price": 36},
    ]

# -------------------------------------------------
# Sidebar – Trip settings
# -------------------------------------------------
with st.sidebar:
    st.markdown("### 🚛 Trip Settings")
    
    trip_ref = st.text_input("Trip Reference / Date", value="24.AUG.26")
    trip_date = st.date_input("Trip Date", value=date(2026, 8, 24))
    
    st.markdown("---")
    st.markdown("### 🏢 Supplier, Driver & Truck")
    
    supplier_name = st.text_input("Supplier Name *", value="", placeholder="Enter supplier name")
    driver_name = st.text_input("Driver Full Name", value="", placeholder="Driver's full name")
    driver_id = st.text_input("Driver ID / Passport / Licence", value="", placeholder="ID number")
    truck_reg = st.text_input("Truck Registration", value="", placeholder="e.g. ABC 1234 ZM")
    
    st.markdown("---")
    st.markdown("### 🌍 Origin, Route & Currency")
    
    origin_country = st.selectbox(
        "Product origin country",
        ["South Africa (Joburg)", "Botswana", "Zimbabwe", "Namibia", "Other"],
        index=0
    )
    
    transit_route = st.radio(
        "Transit route",
        ["Via Botswana", "Via Zimbabwe"],
        index=0,
        horizontal=True
    )
    
    border_post = st.text_input("Border Post / Crossing", value="", placeholder="e.g. Chirundu, Kazungula, Beitbridge")
    
    purchase_currency = st.selectbox(
        "Currency you buy the product in",
        ["USD", "ZAR (RAND)", "ZMW (Kwacha)"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 💱 Exchange Rates")
    
    rate_usd_zmw = st.number_input("1 USD = ? ZMW", value=19.50, step=0.01, format="%.2f")
    rate_zar_zmw = st.number_input("1 ZAR = ? ZMW", value=1.27, step=0.01, format="%.2f")
    
    st.markdown("---")
    st.info("All final figures are shown in **ZMW (Zambian Kwacha)**")
    
    st.markdown("---")
    st.markdown("### 📝 Notes")
    trip_notes = st.text_area("Trip Notes / Comments", value="", placeholder="Any extra information about this trip...", height=100)
    
    if not supplier_name.strip():
        st.warning("⚠️ Please enter Supplier Name")

# -------------------------------------------------
# Helper: convert any amount to ZMW
# -------------------------------------------------
def to_zmw(amount, currency):
    if currency == "USD":
        return amount * rate_usd_zmw
    elif currency in ["ZAR (RAND)", "ZAR", "RAND"]:
        return amount * rate_zar_zmw
    else:  # already ZMW
        return amount

# -------------------------------------------------
# Header
# -------------------------------------------------
st.markdown('<p class="main-header">Joburg Load – Trip Calculator</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">Origin: <b>{origin_country}</b> &nbsp;|&nbsp; Route: <b>{transit_route}</b> &nbsp;|&nbsp; Currency: <b>{purchase_currency}</b> &nbsp;|&nbsp; Ref: {trip_ref}</p>', unsafe_allow_html=True)

# Show key trip info
info_cols = st.columns(4)
info_cols[0].markdown(f"**Supplier:** {supplier_name or '—'}")
info_cols[1].markdown(f"**Driver:** {driver_name or '—'}")
info_cols[2].markdown(f"**Truck:** {truck_reg or '—'}")
info_cols[3].markdown(f"**Border:** {border_post or '—'}")

# -------------------------------------------------
# Tabs
# -------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📦 Purchases", "🛣️ Trip Expenses", "💰 Sales", "📊 Final Trip Report"])

# ==================== TAB 1: PURCHASES ====================
with tab1:
    st.subheader("Products purchased")
    st.caption("Enter **Product Name**, **Brand**, **Quantity** and the **Price you bought it at**.")
    
    # Editable products table
    prod_df = pd.DataFrame(st.session_state.products)
    edited_prod = st.data_editor(
        prod_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Product Name", required=True),
            "brand": st.column_config.TextColumn("Brand"),
            "cost": st.column_config.NumberColumn(f"Buy Price ({purchase_currency})", min_value=0, format="%.2f"),
            "qty": st.column_config.NumberColumn("Quantity", min_value=0, format="%d"),
        },
        key="prod_editor"
    )
    st.session_state.products = edited_prod.to_dict("records")
    
    # Calculate product cost in ZMW
    product_cost_zmw = 0
    for p in st.session_state.products:
        product_cost_zmw += to_zmw(p["cost"] * p["qty"], purchase_currency)
    
    st.markdown("---")
    st.subheader("Additional product fees (already in ZMW)")
    
    fee_df = pd.DataFrame(st.session_state.extra_fees)
    edited_fees = st.data_editor(
        fee_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": "Fee Name",
            "amount": st.column_config.NumberColumn("Amount (ZMW)", format="%.2f"),
        },
        key="fee_editor"
    )
    st.session_state.extra_fees = edited_fees.to_dict("records")
    
    extra_fees_total = sum(f["amount"] for f in st.session_state.extra_fees)
    total_product_cost = product_cost_zmw + extra_fees_total
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Product cost (converted)", f"{product_cost_zmw:,.2f} ZMW")
    col2.metric("Extra fees", f"{extra_fees_total:,.2f} ZMW")
    col3.metric("TOTAL PRODUCT COST", f"{total_product_cost:,.2f} ZMW")

# ==================== TAB 2: EXPENSES ====================
with tab2:
    # ---- FUEL SECTION ----
    st.subheader("⛽ Fuel")
    st.caption("Enter litres loaded and the price you paid per litre. Total is calculated automatically.")
    
    fuel_df = pd.DataFrame(st.session_state.fuel_entries)
    edited_fuel = st.data_editor(
        fuel_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "leg": st.column_config.SelectboxColumn(
                "Leg / Type", options=["Outbound", "Return", "Fridge Diesel", "Other"], required=True
            ),
            "litres": st.column_config.NumberColumn("Litres Loaded", min_value=0, format="%.2f"),
            "price": st.column_config.NumberColumn("Price per Litre", min_value=0, format="%.2f"),
            "currency": st.column_config.SelectboxColumn(
                "Currency", options=["ZMW", "USD", "ZAR (RAND)"], required=True
            ),
        },
        key="fuel_editor"
    )
    st.session_state.fuel_entries = edited_fuel.to_dict("records")
    
    # Calculate fuel totals
    fuel_total_zmw = 0
    fuel_details = []
    for f in st.session_state.fuel_entries:
        line_cost = f["litres"] * f["price"]
        line_zmw = to_zmw(line_cost, f["currency"])
        fuel_total_zmw += line_zmw
        fuel_details.append({
            "Leg": f["leg"],
            "Litres": f["litres"],
            "Price": f["price"],
            "Currency": f["currency"],
            "Cost (original)": line_cost,
            "Cost (ZMW)": line_zmw
        })
    
    st.success(f"**Total Fuel Cost: {fuel_total_zmw:,.2f} ZMW**")
    
    st.markdown("---")
    
    # ---- OTHER EXPENSES ----
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Outbound expenses (other)")
        out_df = pd.DataFrame(st.session_state.outbound)
        edited_out = st.data_editor(
            out_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "desc": "Description",
                "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                "currency": st.column_config.SelectboxColumn(
                    "Currency", options=["ZMW", "USD", "ZAR (RAND)"], required=True
                ),
            },
            key="out_editor"
        )
        st.session_state.outbound = edited_out.to_dict("records")
        
        outbound_other = sum(to_zmw(r["amount"], r["currency"]) for r in st.session_state.outbound)
        st.info(f"Other outbound: {outbound_other:,.2f} ZMW")
    
    with col_b:
        st.subheader("Return expenses (other)")
        ret_df = pd.DataFrame(st.session_state.return_exp)
        edited_ret = st.data_editor(
            ret_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "desc": "Description",
                "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                "currency": st.column_config.SelectboxColumn(
                    "Currency", options=["ZMW", "USD", "ZAR (RAND)"], required=True
                ),
            },
            key="ret_editor"
        )
        st.session_state.return_exp = edited_ret.to_dict("records")
        
        return_other = sum(to_zmw(r["amount"], r["currency"]) for r in st.session_state.return_exp)
        st.info(f"Other return: {return_other:,.2f} ZMW")
    
    outbound_total = outbound_other   # fuel is shown separately but included in grand total
    return_total = return_other
    total_trip_exp = fuel_total_zmw + outbound_other + return_other
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Fuel", f"{fuel_total_zmw:,.0f} ZMW")
    c2.metric("Other Expenses", f"{outbound_other + return_other:,.0f} ZMW")
    c3.metric("TOTAL TRIP EXPENSES", f"{total_trip_exp:,.0f} ZMW")

# ==================== TAB 3: SALES ====================
with tab3:
    st.subheader("Sales – enter each customer")
    st.caption("Add or remove rows as needed. All prices are in ZMW.")
    
    sales_df = pd.DataFrame(st.session_state.sales)
    edited_sales = st.data_editor(
        sales_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "customer": st.column_config.TextColumn("Customer Name", required=True),
            "product": st.column_config.TextColumn("Product"),
            "qty": st.column_config.NumberColumn("Quantity", min_value=0, format="%d"),
            "price": st.column_config.NumberColumn("Sale Price (ZMW)", min_value=0, format="%.2f"),
        },
        key="sales_editor"
    )
    st.session_state.sales = edited_sales.to_dict("records")
    
    # Calculate totals
    sales_rows = []
    total_sales = 0
    total_qty_sold = 0
    for s in st.session_state.sales:
        line_total = s["qty"] * s["price"]
        total_sales += line_total
        total_qty_sold += s["qty"]
        sales_rows.append({
            "Customer": s["customer"],
            "Product": s["product"],
            "Qty": s["qty"],
            "Price": s["price"],
            "Line Total": line_total
        })
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Total quantity sold", f"{total_qty_sold:,}")
    c2.metric("TOTAL SALES", f"{total_sales:,.2f} ZMW")

# ==================== TAB 4: FINAL REPORT ====================
with tab4:
    # Re-calculate everything fresh
    product_cost_zmw = sum(to_zmw(p["cost"] * p["qty"], purchase_currency) for p in st.session_state.products)
    extra_fees_total = sum(f["amount"] for f in st.session_state.extra_fees)
    total_product_cost = product_cost_zmw + extra_fees_total
    
    # Fuel
    fuel_total_zmw = 0
    for f in st.session_state.fuel_entries:
        line_cost = f["litres"] * f["price"]
        fuel_total_zmw += to_zmw(line_cost, f["currency"])
    
    outbound_other = sum(to_zmw(r["amount"], r["currency"]) for r in st.session_state.outbound)
    return_other = sum(to_zmw(r["amount"], r["currency"]) for r in st.session_state.return_exp)
    total_trip_exp = fuel_total_zmw + outbound_other + return_other
    
    grand_total_cost = total_product_cost + total_trip_exp
    total_sales = sum(s["qty"] * s["price"] for s in st.session_state.sales)
    gross_profit = total_sales - grand_total_cost
    margin = (gross_profit / total_sales * 100) if total_sales > 0 else 0
    
    # ---- Report Header ----
    st.markdown(f"## 📋 Trip Report – {trip_ref}")
    st.markdown(f"**Date:** {trip_date.strftime('%d %B %Y')}")
    
    r1, r2, r3 = st.columns(3)
    r1.markdown(f"**Origin:** {origin_country}")
    r2.markdown(f"**Transit Route:** {transit_route}")
    r3.markdown(f"**Purchase Currency:** {purchase_currency}")
    
    r4, r5, r6 = st.columns(3)
    r4.markdown(f"**Supplier:** {supplier_name or '—'}")
    r5.markdown(f"**Driver:** {driver_name or '—'}")
    r6.markdown(f"**Driver ID:** {driver_id or '—'}")
    
    r7, r8, r9 = st.columns(3)
    r7.markdown(f"**Truck Reg:** {truck_reg or '—'}")
    r8.markdown(f"**Border Post:** {border_post or '—'}")
    r9.markdown("")
    
    if trip_notes.strip():
        st.info(f"**Notes:** {trip_notes}")
    
    st.markdown("---")
    
    # ---- Key Metrics ----
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Product Cost", f"{total_product_cost:,.0f} ZMW")
    m2.metric("Trip Expenses", f"{total_trip_exp:,.0f} ZMW")
    m3.metric("Total Sales", f"{total_sales:,.0f} ZMW")
    
    if gross_profit >= 0:
        m4.markdown(f"<div class='metric-card'><small>Gross Profit</small><br><span class='profit-positive'>{gross_profit:,.0f} ZMW</span><br><small>{margin:.1f}% margin</small></div>", unsafe_allow_html=True)
    else:
        m4.metric("Gross Profit", f"{gross_profit:,.0f} ZMW", delta=f"{margin:.1f}%")
    
    st.markdown("---")
    
    # ---- Detailed sections ----
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 Product Cost Breakdown")
        prod_report = []
        for p in st.session_state.products:
            line = to_zmw(p["cost"] * p["qty"], purchase_currency)
            prod_report.append({
                "Product": p["name"],
                "Brand": p.get("brand", ""),
                f"Cost ({purchase_currency})": p["cost"],
                "Qty": p["qty"],
                "Total ZMW": line
            })
        st.dataframe(pd.DataFrame(prod_report), use_container_width=True, hide_index=True)
        
        st.write(f"**Extra fees:** {extra_fees_total:,.2f} ZMW")
        st.write(f"**Total Product Cost: {total_product_cost:,.2f} ZMW**")
        
        st.markdown("### ⛽ Fuel")
        fuel_report = []
        for f in st.session_state.fuel_entries:
            line_cost = f["litres"] * f["price"]
            line_zmw = to_zmw(line_cost, f["currency"])
            fuel_report.append({
                "Leg": f["leg"],
                "Litres": f["litres"],
                "Price/L": f["price"],
                "Currency": f["currency"],
                "Total ZMW": round(line_zmw, 2)
            })
        st.dataframe(pd.DataFrame(fuel_report), use_container_width=True, hide_index=True)
        st.write(f"**Total Fuel: {fuel_total_zmw:,.2f} ZMW**")
        
        st.markdown("### 🛣️ Other Trip Expenses")
        st.write(f"Outbound (other): **{outbound_other:,.2f} ZMW**")
        st.write(f"Return (other): **{return_other:,.2f} ZMW**")
        st.write(f"**Total Trip Expenses (Fuel + Other): {total_trip_exp:,.2f} ZMW**")
    
    with col2:
        st.markdown("### 💰 Sales Breakdown")
        sales_report = []
        for s in st.session_state.sales:
            sales_report.append({
                "Customer": s["customer"],
                "Product": s["product"],
                "Qty": s["qty"],
                "Price": s["price"],
                "Total": s["qty"] * s["price"]
            })
        st.dataframe(pd.DataFrame(sales_report), use_container_width=True, hide_index=True)
        st.write(f"**Total Sales: {total_sales:,.2f} ZMW**")
    
    st.markdown("---")
    
    # ---- Final Summary Box ----
    st.markdown("### ✅ Final Summary")
    
    summary_data = {
        "Description": [
            "Total Product Cost",
            "Total Trip Expenses",
            "GRAND TOTAL COST",
            "Total Sales",
            "GROSS PROFIT",
            "Profit Margin"
        ],
        "Amount (ZMW)": [
            f"{total_product_cost:,.2f}",
            f"{total_trip_exp:,.2f}",
            f"{grand_total_cost:,.2f}",
            f"{total_sales:,.2f}",
            f"{gross_profit:,.2f}",
            f"{margin:.1f}%"
        ]
    }
    st.table(pd.DataFrame(summary_data))
    
    # ---- Download buttons ----
    st.markdown("---")
    st.markdown("### 📥 Download Report")
    
    # Create Excel report for download
    def create_excel_report():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Summary sheet
            summary_df = pd.DataFrame({
                "Item": ["Trip Reference", "Date", "Origin Country", "Transit Route", "Border Post",
                         "Supplier Name", "Driver Name", "Driver ID", "Truck Registration",
                         "Purchase Currency", "Notes",
                         "Product Cost (ZMW)", "Trip Expenses (ZMW)", "Grand Total Cost (ZMW)",
                         "Total Sales (ZMW)", "Gross Profit (ZMW)", "Profit Margin %"],
                "Value": [trip_ref, str(trip_date), origin_country, transit_route, border_post,
                          supplier_name, driver_name, driver_id, truck_reg,
                          purchase_currency, trip_notes,
                          round(total_product_cost, 2), round(total_trip_exp, 2),
                          round(grand_total_cost, 2), round(total_sales, 2),
                          round(gross_profit, 2), round(margin, 1)]
            })
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            # Products
            pd.DataFrame(prod_report).to_excel(writer, sheet_name="Products", index=False)
            
            # Sales
            pd.DataFrame(sales_report).to_excel(writer, sheet_name="Sales", index=False)
            
            # Fuel
            fuel_data = []
            for f in st.session_state.fuel_entries:
                line_cost = f["litres"] * f["price"]
                fuel_data.append({
                    "Leg": f["leg"],
                    "Litres": f["litres"],
                    "Price per Litre": f["price"],
                    "Currency": f["currency"],
                    "Cost (original)": line_cost,
                    "Cost ZMW": to_zmw(line_cost, f["currency"])
                })
            pd.DataFrame(fuel_data).to_excel(writer, sheet_name="Fuel", index=False)
            
            # Other Expenses
            exp_data = []
            for r in st.session_state.outbound:
                exp_data.append({"Leg": "Outbound", "Description": r["desc"],
                                 "Amount": r["amount"], "Currency": r["currency"],
                                 "ZMW": to_zmw(r["amount"], r["currency"])})
            for r in st.session_state.return_exp:
                exp_data.append({"Leg": "Return", "Description": r["desc"],
                                 "Amount": r["amount"], "Currency": r["currency"],
                                 "ZMW": to_zmw(r["amount"], r["currency"])})
            pd.DataFrame(exp_data).to_excel(writer, sheet_name="Other Expenses", index=False)
        
        return output.getvalue()
    
    excel_data = create_excel_report()
    
    st.download_button(
        label="📥 Download Full Trip Report (Excel)",
        data=excel_data,
        file_name=f"Trip_Report_{trip_ref.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.success("Report ready! You can also take a screenshot or print this page (Ctrl+P).")

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("---")
st.caption("Joburg Load Trip Calculator • Built for easy daily use • All figures in ZMW unless noted")
