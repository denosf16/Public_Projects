# **MLB Game Data Fetcher**

## **Overview**
This Python command-line tool fetches MLB game and linescore data from the **MLB StatsAPI**, parses it, and saves it into **CSV files** that match a predefined relational database schema.

## **Usage**
### **Command-Line Execution**
To run the script for a single date:
```bash
python fetch_mlb_dataV2.py --start_date YYYY-MM-DD --csv
```
Example:
```bash
python fetch_mlb_dataV2.py --start_date 2023-07-28 --csv
```
This fetches all **MLB games** played on **July 28, 2023**, and saves the data as CSV files.

### **Fetching an Entire Season**
To fetch **all games from Opening Day to the end of the season**, specify both `--start_date` and `--end_date`:
```bash
python fetch_mlb_dataV2.py --start_date 2023-03-30 --end_date 2023-10-01 --csv
```
This retrieves all games from **March 30, 2023, to October 1, 2023**, and saves the results in CSV format.

## **Output Files**
The script generates the following CSV files in the designated export folder:
- `Teams.csv` – Contains team information.
- `Venues.csv` – Stores venue details.
- `Games.csv` – Includes game-level data (scores, teams, dates, venue).
- `Linescore.csv` – Captures inning-by-inning scoring and game events.

## **Database Integration**
Each CSV file aligns with a **relational database schema**, where:
- `Games` references `Teams` and `Venues`.
- `Linescore` references `Games`.
- Primary keys and foreign keys ensure referential integrity.

## **Edge Cases & Error Handling**
- **Missing Data**: Defaults to placeholder values (`"Unknown"` for text fields, `NULL` for numbers) if API responses lack information.
- **No Games Found**: Logs a warning instead of failing.
- **API Downtime**: Retries the request before skipping the date.

## **Example Logs**
The script logs key events for tracking progress and debugging:
```plaintext
[2023-07-28 12:34:56] INFO: Fetched 15 games for 2023-07-28
[2023-07-28 12:35:02] WARNING: Skipping Game ID 123456 - No valid scores.
[2023-07-28 12:35:15] SUMMARY: CSV files saved in C:/Users/denos/OneDrive/Projects/BlueJays/data_exports/20230728_20230728
```

## **Installation & Requirements**
### **Required Python Packages**
Install dependencies using:
```bash
pip install -r requirements.txt
```
### **Database Connection (Optional)**
To log messages to a SQL Server database, update the **DB connection string** in the script:
```python
DB_SERVER = "YOUR_SERVER_NAME"
DB_NAME = "MLB_StatsAPI"
DB_CONN_STRING = f"DRIVER={{SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};Trusted_Connection=yes;"
```


