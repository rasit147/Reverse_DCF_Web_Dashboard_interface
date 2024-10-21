# Reverse DCF Valuation Tool

## Overview

The **Reverse DCF Valuation Tool** is an interactive web application built with Streamlit that allows users to evaluate and analyze stocks using the Reverse Discounted Cash Flow (DCF) model. This tool provides users with the ability to calculate the intrinsic P/E ratio of consistent compounders based on various financial metrics and compare it with current market valuations.

### Live Demo

You can access the live version of the tool [here](https://revdcfinterface.streamlit.app/).

## Features

- Fetches stock data from Screener.in for real-time financial metrics.
- Calculates intrinsic P/E ratio using a reverse DCF approach.
- Visualizes historical sales and profit growth using interactive Plotly charts.
- Provides inputs for customizable DCF parameters such as cost of capital, ROCE, growth rates, and more.

## Technologies Used

- **Python**: The programming language used for the backend logic.
- **Streamlit**: A framework for building interactive web applications.
- **Requests**: For making HTTP requests to fetch stock data.
- **BeautifulSoup**: For web scraping to extract financial metrics.
- **Plotly**: For creating interactive visualizations of data.
- **NumPy**: For numerical operations and calculations.

## Installation

To run this application locally, follow these steps:

1. Clone the repository:
   bash
   git clone https://github.com/rasit147/Reverse_DCF_Web_Dashboard_interface.git
   cd reverse-dcf-valuation-tool
