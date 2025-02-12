# SEC Filings & XBRL Downloader and Converter

This Streamlit app allows users to download SEC filings (such as 10-K and 10-Q forms) for specified ticker symbols, retrieve the associated XBRL-formatted company facts data, and automatically convert the downloaded XBRL JSON files to CSV format. A detailed log of all download and conversion activities is maintained and can be downloaded as a CSV file.

## Features

- **SEC Filings Download:**  
  Retrieve filings (e.g., 10-K and 10-Q) from the SEC EDGAR database for one or more ticker symbols. Filings are filtered by a specified start date.

- **XBRL Data Retrieval:**  
  Automatically download the corresponding XBRL-formatted company facts data for each ticker.

- **Automatic Conversion to CSV:**  
  Once the XBRL JSON file is downloaded, the app immediately converts it into a CSV file using a custom parser—eliminating the need for a separate conversion step.

- **Detailed Logging:**  
  All actions (downloads, skips, errors, and conversions) are logged with details (including file sizes and statuses) and can be downloaded as a CSV log file.

- **User-Friendly Interface:**  
  Built with Streamlit, the app offers an interactive web interface where users can easily configure inputs such as ticker symbols, filing forms, start date, and download directory.

## Getting Started

### Prerequisites

- **Python Version:** Python 3.8 or later.
- **Required Packages:**  
  - [Streamlit](https://streamlit.io/)  
  - [Requests](https://pypi.org/project/requests/)

Install the required Python packages using pip:

``` bash
pip install streamlit requests
``` 


### Running the App

1. **Clone the Repository:**

``` bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

2. **Run the Streamlit App:**

``` bash
streamlit run filings_downloader_app.py
```

3. **Use the App:**  
   The app will open in your default web browser.  
   - **Input Ticker Symbols:** Enter one or more ticker symbols (comma-separated).  
   - **Select Filing Forms:** Choose the filing types (e.g., 10-K, 10-Q).  
   - **Set Start Date:** Define the start date from which filings should be downloaded.  
   - **Download Directory:** Specify the directory where downloaded files should be stored.  
   - **Download & Convert:** Click the **Download Data** button. The app will download the SEC filings, retrieve the corresponding XBRL data, automatically convert the XBRL JSON to CSV, and generate a downloadable log file.

## How It Works

1. **Ticker Mapping:**  
   The app fetches a mapping between ticker symbols and their corresponding CIK (Central Index Key) from the SEC.

2. **Filing Downloads:**  
   For each specified ticker, the app downloads SEC filings that meet the selected criteria (form type and date) and saves them in a structured directory format.

3. **XBRL Data Retrieval:**  
   After filing downloads, the app retrieves the related XBRL JSON data for each ticker.

4. **Automatic CSV Conversion:**  
   The downloaded XBRL JSON file is parsed using a custom function that extracts fact records. These records are then converted into a CSV file and stored in the same folder as the XBRL JSON.

5. **Logging:**  
   Every action (download, skip, error, and conversion) is logged. The user can download a CSV file containing a detailed log of the entire process.

## Code Structure

- **`get_ticker_mapping()`**  
  Retrieves the SEC ticker-to-CIK mapping.

- **`collect_filings(submissions)`**  
  Combines filing records from different sections of the SEC submission JSON.

- **`download_filings_for_ticker()`**  
  Downloads SEC filings for a given ticker and logs the activity.

- **`download_xbrl_data_for_ticker()`**  
  Downloads the XBRL JSON data for a given ticker.

- **`parse_companyfacts()`**  
  Parses the downloaded XBRL JSON data to extract relevant fact records.

- **`convert_xbrl_to_csv()`**  
  Automatically converts the downloaded XBRL JSON file into a CSV file and logs the conversion.

## Contributing

Contributions are welcome! If you have suggestions, improvements, or bug fixes, please open an issue or submit a pull request.

## Acknowledgements

- **SEC EDGAR:** For providing free and public access to company filings.
- **Streamlit:** For the interactive and easy-to-use web application framework.
- **The Open Source Community:** For inspiring and supporting this project.

