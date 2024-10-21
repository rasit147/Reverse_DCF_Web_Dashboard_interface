import streamlit as st  # Streamlit is used for building interactive web applications
import requests  # Requests is used to send HTTP requests for web scraping
from bs4 import BeautifulSoup  # BeautifulSoup is used to parse HTML content from web scraping
import plotly.graph_objects as go  # Plotly is used for creating interactive plots
import numpy as np  # Numpy is used for array and numerical operations

# Set the page title and layout of the web application
st.set_page_config(page_title="Reverse DCF Valuation Tool", layout="wide")

# Function to scrape stock data from Screener.in
def fetch_stock_data(symbol):
    # Used the Screener.in URL pattern for fetching company-specific data
    url = f"https://www.screener.in/company/{symbol}/"
    response = requests.get(url)  # Sending a GET request to the website
    if response.status_code != 200:  # Check if the response is successful
        st.error("Failed to fetch data. Please check the stock symbol.")
        return None, None, None, [], [], []

    # separate the response content with BeautifulSoup to extract HTML elements
    soup = BeautifulSoup(response.content, 'html.parser')

    stock_pe, fy23_pe, market_cap, current_price, roce_values = None, None, None, None, []

    # Scraping basic financial metrics from the company page
    list_items = soup.find_all('li', class_='flex flex-space-between')
    for li in list_items:
        # Extracting the name and value of each financial metric
        name_span = li.find('span', class_='name')
        value_span = li.find('span', class_='number')
        if name_span and value_span:
            name = name_span.get_text(strip=True)
            value = value_span.get_text(strip=True).replace('₹', '').replace(',', '').replace('×', '').strip()
            try:
                # Extracting the Stock P/E, Current Price, and Market Cap values
                if "Stock P/E" in name:
                    stock_pe = float(value) if value else None
                elif "Current Price" in name:
                    current_price = float(value) if value else None
                elif "Market Cap" in name:
                    market_cap = float(value) if value else None
            except ValueError:
                st.error(f"Could not convert value for {name}: {value}")

    # Calculating FY23 P/E ratio if Market Cap and Current Price are available
    if market_cap and current_price:
        fy23_pe = round(market_cap / (current_price * 10), 1)

    # Scraping ROCE values from the ratios section of the company page
    section_ratios = soup.find('section', id='ratios')
    if section_ratios:
        table = section_ratios.find('table', class_='data-table')
        for row in table.find_all('tr'):
            if "ROCE %" in row.text:
                cells = row.find_all('td')
                # Extracting ROCE values over the last five years
                roce_values.extend([float(cell.text.strip('%')) for cell in cells[1:6] if cell.text.strip('%')])

    # Calculating the median ROCE if values are available
    median_roce = round(sorted(roce_values)[len(roce_values) // 2]) if roce_values else None

    # Scraping growth data (sales and profit growth) over different time periods
    sales_growth_data, profit_growth_data, years = [], [], [10, 5, 3, 'TTM']

    # Looking for tables that contain sales and profit growth data
    tables = soup.find_all('table', class_='ranges-table')
    for table in tables:
        title = table.find('th').text.strip()
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) == 2:
                growth_value = cells[1].text.strip().replace('%', '')
                # Checking for Sales Growth and Profit Growth values
                if title == "Compounded Sales Growth":
                    sales_growth_data.append(float(growth_value))
                elif title == "Compounded Profit Growth":
                    profit_growth_data.append(float(growth_value))

    return stock_pe, fy23_pe, median_roce, sales_growth_data, profit_growth_data, years

# Function to calculate the intrinsic P/E using reverse DCF approach
def calculate_intrinsic_pe(cost_of_capital, roce, growth_rate, high_growth_period, fade_period, terminal_growth_rate):
    # Using a default tax rate of 25%
    tax_rate = 0.25
    # Converting cost of capital to a discount rate
    discount_rate = cost_of_capital / 100
    
    # Calculating the present value of cash flows during the high growth period
    cash_flows_high_growth = sum(
        (roce * (1 - tax_rate) * (1 + growth_rate / 100) ** year) / ((1 + discount_rate) ** year)
        for year in range(1, high_growth_period + 1)
    )

    # Calculating the present value of cash flows during the fade period where growth reduces
    fade_growth_rate = np.linspace(growth_rate, terminal_growth_rate, fade_period)
    cash_flows_fade = sum(
        (roce * (1 - tax_rate) * (1 + fade_growth_rate[year - high_growth_period - 1] / 100)) /
        ((1 + discount_rate) ** year)
        for year in range(high_growth_period + 1, high_growth_period + fade_period + 1)
    )

    # Calculating terminal value based on terminal growth rate
    terminal_value = (roce * (1 - tax_rate) * (1 + terminal_growth_rate / 100)) / (discount_rate - terminal_growth_rate / 100)
    # Present value of terminal value
    present_value_terminal = terminal_value / ((1 + discount_rate) ** (high_growth_period + fade_period))
    
    # Summing up all present values to get total present value
    total_present_value = cash_flows_high_growth + cash_flows_fade + present_value_terminal
    
    # Calculating intrinsic P/E ratio by dividing present value by ROCE
    intrinsic_pe = total_present_value / roce  # Assuming earnings are proportional to RoCE

    return intrinsic_pe

# Function to calculate the degree of overvaluation based on intrinsic and current P/E which you mention in problem statement
def calculate_overvaluation(current_pe, fy23_pe, intrinsic_pe):
    # If current P/E is lower than FY23 P/E, the comparison is made with intrinsic P/E
    if current_pe < fy23_pe:
        degree_of_overvaluation = (current_pe / intrinsic_pe) - 1
    else:
        degree_of_overvaluation = (fy23_pe / intrinsic_pe) - 1
    return degree_of_overvaluation

# Sidebar for user input
st.sidebar.title("Reverse DCF")
# Navigation options for different pages
page = st.sidebar.selectbox("Navigate", ["Home", "DCF Valuation"])

# Home page content
if page == "Home":
    st.title("Reverse DCF Valuation")
    st.write("""This site provides interactive tools to valuate and analyze stocks through Reverse DCF model. Check the navigation bar for more.""")

# DCF Valuation page
elif page == "DCF Valuation":
    st.title("Valuing Consistent Compounders")
    st.write("""This page will help you calculate intrinsic PE of consistent compounders through growth-RoCE DCF model.
                We then compare this with ccurrent PE of the after changes in inputs to calculate degree of overvaluation.""")

    # Input field for the stock symbol, with a default value for NESTLEIND
    symbol = st.text_input("Enter NSE/BSE Symbol", value='NESTLEIND')

    # Session state for tracking if data has been fetched
    if 'fetched' not in st.session_state:
        st.session_state['fetched'] = False
        st.session_state['current_pe'] = None

    # Fetch stock data when the user clicks the button
    if st.button("Get Valuation"):
        stock_data = fetch_stock_data(symbol)
        
        if stock_data:
            stock_pe, fy23_pe, median_roce, sales_growth_data, profit_growth_data, years = stock_data
            
            # Store fetched data in session state
            st.session_state['symbol'] = symbol
            st.session_state['stock_pe'] = stock_pe
            st.session_state['fy23_pe'] = fy23_pe
            st.session_state['median_roce'] = median_roce
            st.session_state['fetched'] = True
            st.session_state['sales_growth_data'] = sales_growth_data
            st.session_state['profit_growth_data'] = profit_growth_data
            st.session_state['years'] = years

            # Set default values for input sliders
            st.session_state['CoC'] = 10.0
            st.session_state['RoCE'] = float(median_roce) if median_roce else 40.0
            st.session_state['growth_rate'] = 10.0
            st.session_state['high_growth_period'] = 12
            st.session_state['fade_period'] = 10
            st.session_state['terminal_growth_rate'] = 2.0
            st.session_state['current_pe'] = float(stock_pe) if stock_pe else 45.0  # Default current P/E value

    # Display fetched data and inputs for the valuation model
    if st.session_state['fetched']:
        st.subheader(f"Stock Valuation for {st.session_state['symbol']}")
        # Display fetched financial data
        st.write(f"Current P/E Ratio: {st.session_state['current_pe']}")
        st.write(f"FY23 P/E Ratio: {st.session_state['fy23_pe']}")
        st.write(f"Median RoCE: {st.session_state['median_roce']}%")

        # Display growth data in a bar chart using Plotly
        fig = go.Figure()
        fig.add_trace(go.Bar(x=st.session_state['years'], y=st.session_state['sales_growth_data'], name='Sales Growth (%)'))
        fig.add_trace(go.Bar(x=st.session_state['years'], y=st.session_state['profit_growth_data'], name='Profit Growth (%)'))
        fig.update_layout(barmode='group', title='Sales and Profit Growth Over the Years')
        st.plotly_chart(fig)

        # Input sliders dashboard for the reverse DCF model 
        st.subheader("DCF Inputs")
        CoC = st.slider("Cost of Capital (%)", min_value=8.0, max_value=16.0, value=st.session_state['CoC'])
        RoCE = st.slider("RoCE (%)", min_value=10.0, max_value=100.0, value=st.session_state['RoCE'])
        growth_rate = st.slider("Growth Rate (%)", min_value=0.0, max_value=20.0, value=st.session_state['growth_rate'])
        high_growth_period = st.slider("High Growth Period (Years)", min_value=5, max_value=25, value=st.session_state['high_growth_period'])
        fade_period = st.slider("Fade Period (Years)", min_value=5, max_value=15, value=st.session_state['fade_period'])
        terminal_growth_rate = st.slider("Terminal Growth Rate (%)", min_value=0.0, max_value=7.5, value=st.session_state['terminal_growth_rate'])

        # Calculating the intrinsic P/E ratio
        intrinsic_pe = calculate_intrinsic_pe(CoC, RoCE, growth_rate, high_growth_period, fade_period, terminal_growth_rate)
        st.write("Update input to see changes in intrinsic PE and overvaluation:")
        st.write(f" Calculated Intrinsic P/E Ratio: {intrinsic_pe:.2f}")

        # Calculating the degree of overvaluation
        overvaluation = calculate_overvaluation(st.session_state['current_pe'], st.session_state['fy23_pe'], intrinsic_pe)
        st.write(f"Degree of Overvaluation: {overvaluation * 100:.2f}%")
