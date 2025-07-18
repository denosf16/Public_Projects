
# AU_Soccer Data Processing Project

## Overview

The **AU_Soccer Data Processing Project** automates the extraction, cleaning, validation, and uploading of soccer data from the ASA (American Soccer Analysis) API to a Microsoft SQL Server database. The project processes data on soccer players, games, teams, and other related metrics to ensure the data is in a clean and usable format, ready for further analysis or reporting.

The project also includes robust logging and error handling to track the entire workflow, making it easy to monitor the success and failure of each operation.

## Key Features

- **API Data Fetching**: Fetch data from various ASA API endpoints, including data on players, games, teams, and more.
- **Data Cleaning and Validation**: Handles missing values, removes duplicates, validates foreign keys, and ensures data consistency.
- **SQL Server Integration**: Data is uploaded directly to a Microsoft SQL Server database, where tables are created dynamically.
- **Logging**: All operations are logged into a `ChangeLogs` table in SQL Server to track data fetching, cleaning, and uploading processes.
- **Indexing**: Efficient indexing of database columns for faster query performance.

## Installation

### Prerequisites

Before running the project, you’ll need:

1. **Python 3.x**: The project uses Python 3.x for data fetching, cleaning, and SQL interaction.
2. **Required Python Libraries**:
   - `requests`: For interacting with the ASA API.
   - `pandas`: For data manipulation and cleaning.
   - `pyodbc`: For connecting to Microsoft SQL Server.
   - `python-docx`: For generating a Word document summarizing the workflow.

To install the required libraries, run the following command:

```bash
pip install requests pandas pyodbc python-docx

3. SQL Server:
A running instance of Microsoft SQL Server (e.g., SQLEXPRESS).
A database called SoccerProjects.
Project Structure
AU_Soccer.ipynb: The main Jupyter notebook containing the entire workflow for fetching, cleaning, and uploading data.
data_processing_summary.docx: A Word document automatically generated that contains a detailed summary of the entire data processing workflow, including steps for fetching, cleaning, and uploading data.
README.md: This file.

Workflow
1. Data Fetching
The first part of the workflow fetches data from various ASA API endpoints, including:

Players' statistics (goals, assists, xG, etc.)
Teams' statistics (xG, pass accuracy, etc.)
Game data (scores, team matchups, etc.)
This data is fetched and then normalized into a structured format for processing.

2. Data Cleaning and Validation
Once the data is fetched, the following cleaning steps are applied:

Missing Values: Fill missing values in key columns like birth_date and position with default values (e.g., "1900-01-01" for birth dates and "UNKNOWN" for missing positions).
Duplicates: Drop rows containing duplicate records or unhashable types (e.g., lists or dictionaries).
Data Type Validation: Ensure that all columns have the correct data types, such as converting dates into datetime format and numerical values into float or int.
Foreign Key Validation: Check that IDs in one dataset (e.g., player_id, team_id) correspond to valid records in another dataset.

3. Data Upload to SQL Server
The cleaned data is then uploaded to SQL Server in batches. The following steps are involved:

Table Creation: SQL tables are created dynamically based on the structure of the DataFrames.
Data Insertion: The data is inserted into the respective SQL tables in batches to handle large datasets efficiently.
Indexing: Clustered and non-clustered indexes are created on key columns like player_id, team_id, and date_time_utc to speed up query performance.
4. Logging
Throughout the workflow, logs are maintained in the ChangeLogs table within SQL Server, capturing every action taken (data fetched, cleaned, and uploaded). This provides a full audit trail for the entire data processing pipeline.

5. Document Generation
After the data is processed, a detailed summary document (data_processing_summary.docx) is generated, capturing:

The key steps of the data fetching process.
The cleaning and validation operations applied.
The upload process to SQL Server.
Logs of all actions taken during the workflow.
Usage
Running the Workflow
Prepare the environment:

Ensure that Python and SQL Server are properly set up as per the installation section.
Make sure the SoccerProjects database exists in SQL Server.
Run the Jupyter Notebook:

Open the AU_Soccer.ipynb Jupyter notebook.
Execute the notebook cells sequentially. The notebook will fetch data from the ASA API, clean and validate the data, and upload it to SQL Server.
The process is logged, and a summary document (data_processing_summary.docx) will be saved to your local path.
Check the Results:

After running the notebook, you can check the SQL Server database (SoccerProjects) for the uploaded data.
Review the ChangeLogs table for a log of all operations performed.
Download the Summary Document:

The document data_processing_summary.docx will be saved to C:/Users/denos/OneDrive/Projects/AU_Soccer/.
Example Output
Players Data:

A preview of the players_df DataFrame, containing player details such as player_id, player_name, birth_date, etc.
XGoals Data:

A preview of the xgoals_df DataFrame, containing statistics such as shots, goals, xgoals, key_passes, etc.
Logs:

Each operation, such as data fetching, cleaning, and uploading, is logged to the ChangeLogs table.
Contact
For any issues or further questions, please reach out to Sam Denomme.
