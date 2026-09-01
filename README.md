# Joburg Load – Trip Calculator App

Simple web app to calculate costs and profit for loads from Joburg / neighbouring countries.

## Features

### Trip details (Sidebar)
- Trip Reference & Date
- **Supplier Name** (required)
- **Driver Name + Driver ID**
- **Truck Registration**
- Origin Country
- **Transit Route** (Via Botswana / Via Zimbabwe)
- **Border Post**
- Purchase Currency (USD / ZAR / ZMW)
- Exchange rates
- **Notes / Comments**

### Tabs
1. **Purchases** – Product Name, Brand, Quantity, Buy Price + extra fees
2. **Trip Expenses** – Dedicated **Fuel** section (Litres + Price per litre) + other expenses
3. **Sales** – Customer, Product, Quantity, Sale Price
4. **Final Trip Report** – Full summary + Download Excel

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens in your browser at http://localhost:8501

All final figures are shown in **ZMW**.
