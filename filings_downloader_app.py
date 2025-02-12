#!/usr/bin/env python3
import os
import requests
import json
import csv
import time
import datetime
import io
import streamlit as st

# Set your User-Agent as required by SEC guidelines.
USER_AGENT = "Aanchit Nayak (aanchit.nayak256677@gmail.com)"


def get_ticker_mapping():
    """
    Downloads the SEC ticker-to-CIK mapping.
    Returns a dict mapping tickers (uppercase) to their 10-digit padded CIK.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": USER_AGENT}
    mapping = {}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        for key, entry in data.items():
            ticker = entry["ticker"].upper()
            cik_str = str(entry["cik_str"]).zfill(10)
            mapping[ticker] = cik_str
    except Exception as e:
        st.error(f"Error fetching ticker mapping: {e}")
    return mapping


def collect_filings(submissions):
    """
    Combines filings from the "recent" section and additional "files" (if available)
    into a single list of filing dictionaries.
    """
    filings_list = []
    filings_data = submissions.get("filings", {})

    # Process filings in the "recent" section.
    recent = filings_data.get("recent", {})
    if recent:
        count = len(recent.get("accessionNumber", []))
        for i in range(count):
            filing = {
                "accessionNumber": recent.get("accessionNumber", [])[i],
                "filingDate": recent.get("filingDate", [])[i],
                "form": recent.get("form", [])[i],
                "primaryDocument": recent.get("primaryDocument", [])[i]
            }
            filings_list.append(filing)

    # Process filings in additional files (if available).
    additional_files = filings_data.get("files", [])
    for file_section in additional_files:
        file_filings = file_section.get("filings", {})
        count = len(file_filings.get("accessionNumber", []))
        for i in range(count):
            filing = {
                "accessionNumber": file_filings.get("accessionNumber", [])[i],
                "filingDate": file_filings.get("filingDate", [])[i],
                "form": file_filings.get("form", [])[i],
                "primaryDocument": file_filings.get("primaryDocument", [])[i]
            }
            filings_list.append(filing)
    return filings_list


def download_filings_for_ticker(ticker, forms, start_date, download_dir, log_rows):
    """
    Downloads filings for a given ticker from the SEC submissions JSON.
    Appends log rows (list of lists) instead of writing to a CSV directly.
    Returns the number of filings downloaded.
    """
    mapping = get_ticker_mapping()
    ticker_upper = ticker.upper()
    if ticker_upper not in mapping:
        st.warning(f"Ticker {ticker_upper} not found in SEC ticker mapping.")
        log_rows.insert(0, [ticker_upper, "", "", "", "Ticker not found"])
        return 0

    cik = mapping[ticker_upper]
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(submissions_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Error fetching submissions for {ticker_upper}: {e}")
        log_rows.insert(0, [ticker_upper, "", "", "", f"Error fetching submissions: {e}"])
        return 0

    try:
        submissions = response.json()
    except Exception as e:
        st.error(f"Error parsing JSON for {ticker_upper}: {e}")
        log_rows.insert(0, [ticker_upper, "", "", "", f"Error parsing JSON: {e}"])
        return 0

    filings = collect_filings(submissions)
    if not filings:
        st.info(f"No filings found for {ticker_upper}.")
        log_rows.insert(0, [ticker_upper, "", "", "", "No filings found"])
        return 0

    try:
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    except Exception as e:
        st.error("Invalid start date format. Use YYYY-MM-DD.")
        log_rows.insert(0, [ticker_upper, "", "", "", "Invalid start date"])
        return 0

    files_downloaded = 0
    for filing in filings:
        filing_date_str = filing.get("filingDate", "")
        try:
            filing_date_obj = datetime.datetime.strptime(filing_date_str, "%Y-%m-%d")
        except Exception as e:
            st.error(f"Error parsing filing date {filing_date_str}: {e}")
            log_rows.insert(0, [ticker_upper, filing_date_str, filing.get("form", ""), "", f"Error parsing filing date: {e}"])
            continue

        # Only process filings on or after the start_date.
        if filing_date_obj < start_date_obj:
            continue

        current_form = filing.get("form", "").upper()
        if current_form not in [f.upper() for f in forms]:
            continue

        accession = filing.get("accessionNumber", "")
        acc_no_clean = accession.replace("-", "")
        primary_doc = filing.get("primaryDocument", "")
        cik_non_padded = str(int(cik))
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_non_padded}/{acc_no_clean}/{primary_doc}"

        # Build the file storage path.
        ticker_folder = os.path.join(download_dir, ticker_upper)
        form_folder = os.path.join(ticker_folder, current_form)
        os.makedirs(form_folder, exist_ok=True)
        filename = f"{filing_date_str}_{os.path.basename(primary_doc)}"
        file_path = os.path.join(form_folder, filename)

        # Check if file already exists.
        if os.path.exists(file_path):
            st.info(f"File already exists: {file_path}. Skipping.")
            file_size = os.path.getsize(file_path)
            log_rows.insert(0, [ticker_upper, filing_date_str, current_form, file_size, "Skipped"])
            continue

        st.info(f"Downloading {current_form} filed on {filing_date_str} for {ticker_upper}...")
        try:
            filing_response = requests.get(url, headers=headers)
            filing_response.raise_for_status()
        except Exception as e:
            st.error(f"Error downloading filing from {url}: {e}")
            log_rows.insert(0, [ticker_upper, filing_date_str, current_form, "", f"Download error: {e}"])
            continue

        try:
            with open(file_path, "wb") as f:
                f.write(filing_response.content)
            file_size = os.path.getsize(file_path)
            st.success(f"Saved to {file_path} (size: {file_size} bytes)")
            log_rows.insert(0, [ticker_upper, filing_date_str, current_form, file_size, "Downloaded"])
            files_downloaded += 1
        except Exception as e:
            st.error(f"Error saving file {file_path}: {e}")
            log_rows.insert(0, [ticker_upper, filing_date_str, current_form, "", f"Save error: {e}"])
        time.sleep(1)  # Pause to be courteous to SEC servers.
    
    return files_downloaded


def download_xbrl_data_for_ticker(ticker, download_dir, log_rows):
    mapping = get_ticker_mapping()
    ticker_upper = ticker.upper()
    if ticker_upper not in mapping:
        st.warning(f"Ticker {ticker_upper} not found in SEC ticker mapping for XBRL download.")
        log_rows.insert(0, [ticker_upper, "", "XBRL", "", "Ticker not found"])
        return

    cik = mapping[ticker_upper]
    xbrl_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": USER_AGENT}

    # Create directory for XBRL data.
    ticker_folder = os.path.join(download_dir, ticker_upper)
    xbrl_folder = os.path.join(ticker_folder, "XBRL")
    os.makedirs(xbrl_folder, exist_ok=True)
    file_path = os.path.join(xbrl_folder, "companyfacts.json")

    # Check if XBRL file already exists.
    if os.path.exists(file_path):
        st.info(f"XBRL data already exists for {ticker_upper} at {file_path}. Skipping download.")
        file_size = os.path.getsize(file_path)
        log_rows.insert(0, [ticker_upper, "", "XBRL", file_size, "Skipped"])
        return

    st.info(f"Downloading XBRL data for {ticker_upper}...")
    try:
        response = requests.get(xbrl_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Error downloading XBRL data for {ticker_upper}: {e}")
        log_rows.insert(0, [ticker_upper, "", "XBRL", "", f"XBRL download error: {e}"])
        return

    try:
        with open(file_path, "wb") as f:
            f.write(response.content)
        file_size = os.path.getsize(file_path)
        st.success(f"Saved XBRL data for {ticker_upper} to {file_path} (size: {file_size} bytes)")
        log_rows.insert(0, [ticker_upper, "", "XBRL", file_size, "Downloaded"])
    except Exception as e:
        st.error(f"Error saving XBRL data for {ticker_upper}: {e}")
        log_rows.insert(0, [ticker_upper, "", "XBRL", "", f"XBRL save error: {e}"])


def parse_companyfacts(xbrl_data, ticker):
    """
    Extracts fact records from the XBRL JSON data.
    Returns a list of rows, where each row is [Ticker, Particular, Time, Value].
    """
    rows = []
    facts = xbrl_data.get("facts", {})
    # Loop through each taxonomy (e.g., "us-gaap", "dei", etc.)
    for taxonomy, elements in facts.items():
        for element, element_data in elements.items():
            # Each element is expected to have a "units" dictionary.
            units = element_data.get("units", {})
            all_records = []
            for unit, records in units.items():
                all_records.extend(records)
            if not all_records:
                continue

            # Check if any record has an "fp" (fiscal period) that is not "FY" (annual)
            has_granular = any(("fp" in rec and rec["fp"] != "FY") for rec in all_records)
            if has_granular:
                # Keep only granular (e.g., quarterly) records
                filtered_records = [rec for rec in all_records if ("fp" in rec and rec["fp"] != "FY")]
            else:
                filtered_records = all_records

            for rec in filtered_records:
                # Choose the most granular time stamp: "instant" if available, else "end".
                time_stamp = rec.get("instant", rec.get("end", ""))
                if not time_stamp:
                    continue
                value = rec.get("val", "")
                rows.append([ticker, element, time_stamp, value])
    return rows


def convert_xbrl_to_csv(ticker, download_dir, log_rows):
    """
    Automatically converts the downloaded XBRL JSON file for the given ticker
    to a CSV file (using parse_companyfacts) and saves it under [download_dir]/[TICKER]/XBRL.
    """
    ticker_upper = ticker.upper()
    xbrl_folder = os.path.join(download_dir, ticker_upper, "XBRL")
    json_file_path = os.path.join(xbrl_folder, "companyfacts.json")
    if not os.path.exists(json_file_path):
        st.warning(f"XBRL JSON file not found for {ticker_upper}. Cannot convert to CSV.")
        log_rows.insert(0, [ticker_upper, "", "XBRL Conversion", "", "XBRL JSON file not found"])
        return
    try:
        with open(json_file_path, "r") as f:
            xbrl_data = json.load(f)
        rows = parse_companyfacts(xbrl_data, ticker_upper)
        if not rows:
            st.warning(f"No fact records found for {ticker_upper} during conversion.")
            log_rows.insert(0, [ticker_upper, "", "XBRL Conversion", "", "No fact records found"])
            return
        csv_file_path = os.path.join(xbrl_folder, "companyfacts.csv")
        with open(csv_file_path, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Ticker", "Particular", "Time", "Value"])
            writer.writerows(rows)
        st.success(f"Converted XBRL JSON to CSV for {ticker_upper} at {csv_file_path}.")
        log_rows.insert(0, [ticker_upper, "", "XBRL Conversion", os.path.getsize(csv_file_path), "Converted"])
    except Exception as e:
        st.error(f"Error converting XBRL JSON to CSV for {ticker_upper}: {e}")
        log_rows.insert(0, [ticker_upper, "", "XBRL Conversion", "", f"Conversion error: {e}"])


# -------------------------------
# Streamlit App Interface
# -------------------------------
st.title("SEC Filings & XBRL Converter")

# Use a single tab for downloading and converting data.
tabs = st.tabs(["Download & Convert Data"])
with tabs[0]:
    st.header("Download SEC Filings and XBRL Data")
    
    # Display helper text for each input field.
    st.markdown("**Ticker symbols:** Enter the stock symbols for companies (e.g., AAPL, MSFT). Use commas to separate multiple tickers.")
    st.markdown("**Filing forms:** Choose the type of filings to download (e.g., 10-K for annual reports, 10-Q for quarterly reports).")
    st.markdown("**Start Date:** Only filings on or after this date will be downloaded.")
    
    tickers_input = st.text_input("Enter ticker symbols (comma-separated)", value="AAPL, MSFT")
    st.caption("Example: AAPL, MSFT")
    
    forms_selected = st.multiselect("Select filing forms", options=["10-K", "10-Q"], default=["10-K", "10-Q"])
    st.caption("Select '10-K' for annual and '10-Q' for quarterly filings.")
    
    start_date_obj = st.date_input("Start Date", value=datetime.date(2018, 1, 1))
    st.caption("Filings before this date will be ignored.")
    
    # Automatically set the download directory to the user's default Downloads folder.
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    st.info(f"Files will be saved to your Downloads folder: {download_dir}")
    
    if st.button("Download Data"):
        # Ensure download directory exists.
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
        tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]
        log_rows = []  # For collecting log rows.
        overall_downloaded = 0

        for ticker in tickers:
            status_container = st.empty()  # Container for dynamic status updates.
            status_container.subheader(f"Processing ticker: {ticker.upper()}")
            log_rows.insert(0, [ticker.upper(), "", "Subheader", "", f"Downloading {ticker.upper()}"])
            downloaded = download_filings_for_ticker(
                ticker,
                forms_selected,
                start_date_obj.strftime("%Y-%m-%d"),
                download_dir,
                log_rows
            )

            status_container.write(f"✅ Total filing files downloaded for {ticker.upper()}: {downloaded}")
            overall_downloaded += downloaded

            # Download the XBRL data and automatically convert it to CSV.
            if downloaded == 0:
                st.warning(f"No filings found for {ticker.upper()}. Skipping XBRL download and conversion.")
            else:
                download_xbrl_data_for_ticker(ticker, download_dir, log_rows)
                convert_xbrl_to_csv(ticker, download_dir, log_rows)

        st.success(f"Overall, {overall_downloaded} filing files were downloaded.")

        # Prepare an in-memory CSV log that the user can download.
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Ticker", "Filing Date", "Filing Type", "File Size (bytes)", "Status/Errors"])
        for row in log_rows:
            writer.writerow(row)

        st.download_button(
            label="Download Log CSV",
            data=csv_buffer.getvalue(),
            file_name="download_log.csv",
            mime="text/csv"
        )
