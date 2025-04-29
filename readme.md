# Multi-DB SQL Runner

## Overview
The Multi-DB SQL Runner is a Python-based desktop application designed to execute SQL scripts across multiple databases on a SQL Server instance simultaneously. Built with tkinter for the GUI and pyodbc for database connectivity, it provides a user-friendly interface for database administrators, developers, and data analysts to manage and query multiple databases efficiently. The application supports light and dark themes, asynchronous database operations, and result exporting to CSV, making it a versatile tool for database management tasks.

This application is particularly useful in scenarios where repetitive SQL operations need to be performed across multiple databases, such as data migrations, batch updates, or generating aggregated reports. It includes features like database selection, script editing with line numbers, execution progress tracking, and detailed logging.

## Features

- **Multi-Database Execution**: Run SQL scripts on multiple user-selected databases in a single SQL Server instance.
- **Asynchronous Operations**: Load databases and execute scripts asynchronously to ensure a responsive UI.
- **Theme Support**: Switch between light and dark themes for better usability in different environments.
- **Script Editor**: Edit SQL scripts with line numbers and load scripts from .sql files.
- **Progress Monitoring**: Track execution progress with a progress bar and detailed status logs.
- **Result Exporting**: Export query results to CSV files for further analysis.
- **Error Handling**: Comprehensive error logging for connection issues, query failures, and execution errors.
- **Searchable Database List**: Filter databases by name for quick selection.
- **Cross-Platform**: Compatible with Windows, macOS, and Linux (with appropriate ODBC drivers).

## Real-World Applications

The Multi-DB SQL Runner is designed for various real-world use cases, including:

### Data Migration:
- **Scenario**: A company is consolidating multiple regional databases into a single database or upgrading to a new SQL Server version.
- **Use Case**: Use the application to execute schema creation scripts, data transfer queries, or data cleanup scripts across all regional databases simultaneously, ensuring consistency and saving time compared to manual execution.
- **Example**: Run ALTER TABLE statements to add new columns or INSERT INTO ... SELECT queries to migrate data.

### Batch Updates:
- **Scenario**: A retail chain needs to update pricing or inventory data across databases for each store.
- **Use Case**: Load an UPDATE script to modify records in specific tables (e.g., UPDATE Products SET Price = Price * 1.1) and execute it across all store databases, with progress tracking and error logging.
- **Example**: Apply a discount to products in all databases during a sale period.

### Reporting and Analytics:
- **Scenario**: A financial institution needs to generate monthly reports from multiple client databases.
- **Use Case**: Run SELECT queries to aggregate data (e.g., SELECT SUM(TransactionAmount) FROM Transactions WHERE Date >= '2025-01-01') across databases, then export results to CSV for analysis in tools like Excel or Power BI.
- **Example**: Generate a consolidated report of transaction totals across all client databases.

### Database Maintenance:
- **Scenario**: A database administrator needs to perform maintenance tasks like index rebuilding or statistics updates.
- **Use Case**: Execute maintenance scripts (e.g., UPDATE STATISTICS or DBCC CHECKDB) across all databases to ensure optimal performance, with detailed logs to verify completion.
- **Example**: Rebuild indexes on all databases during a maintenance window.

### Testing and Development:
- **Scenario**: A development team needs to apply schema changes to multiple test databases during a sprint.
- **Use Case**: Use the script editor to write or load DDL scripts (e.g., CREATE TABLE or ALTER PROCEDURE) and apply them to all test databases, ensuring consistency across environments.
- **Example**: Deploy a new table structure to all test databases for a feature release.

### Compliance and Auditing:
- **Scenario**: A healthcare provider must audit data access logs across patient databases to comply with regulations.
- **Use Case**: Run audit queries (e.g., SELECT * FROM AuditLog WHERE AccessTime >= '2025-04-01') across all databases and export results for compliance reporting.
- **Example**: Generate a report of all user access events for a regulatory audit.

## Prerequisites

To run the Multi-DB SQL Runner, ensure the following are installed:

1. **Python 3.8+**: The application is built with Python and requires a compatible version.
2. **Required Python Packages**: `pip install pyodbc`
   - pyodbc: For SQL Server connectivity.

3. **SQL Server ODBC Driver**:
   - Windows: Install ODBC Driver 17 for SQL Server or a compatible version.
   - macOS/Linux: Install Microsoft ODBC Driver for SQL Server (follow platform-specific instructions).
   - Verify installed drivers with:
     ```python
     import pyodbc
     print(pyodbc.drivers())
     ```

4. **SQL Server Instance**: Access to a SQL Server instance with user credentials or Windows authentication.
   - Ensure the user has VIEW ANY DATABASE permission to list databases:
     ```sql
     GRANT VIEW ANY DATABASE TO [username];
     ```

5. **tkinter**: Included with standard Python installations. On Linux, install python3-tk:
   ```
   sudo apt-get install python3-tk
   ```

## Installation

1. **Clone or Download the Repository**:
   ```
   git clone <repository-url>
   cd multi-db-sql-runner
   ```
   Alternatively, download and extract the source code.

2. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```
   Create a requirements.txt with:
   ```
   pyodbc
   ```

3. **Set Up ODBC Driver**:
   - Windows: Download and install the ODBC driver from Microsoft's official site.
   - macOS/Linux: Follow instructions at Microsoft ODBC Driver for SQL Server.

4. **Verify SQL Server Access**:
   - Test connectivity using a tool like SQL Server Management Studio (SSMS) with the same credentials.
   - Run:
     ```sql
     SELECT name FROM sys.databases WHERE database_id > 4;
     ```
     to confirm user databases are accessible.

## Usage

1. **Launch the Application**:
   ```
   python main.py
   ```
   Replace main.py with the name of the main script file.

2. **Login**:
   - Enter SQL Server credentials in the login dialog:
     - Server: SQL Server instance name (e.g., localhost, SERVERNAME\INSTANCE).
     - Username and Password: SQL Server authentication credentials.
     - Driver: ODBC driver name (e.g., ODBC Driver 17 for SQL Server).
   - For Windows authentication, modify the code to set use_windows_auth=True in SQLServerConnectionFactory.

3. **Select Databases**:
   - In the Databases tab, view and select databases to query.
   - Use the search bar to filter databases by name.
   - Click Select All or Deselect All for bulk selection.

4. **Write or Load SQL Script**:
   - In the SQL Script tab, write SQL queries or scripts in the editor.
   - Use Upload SQL File to load a .sql file.
   - The editor supports line numbers for easier script navigation.

5. **Execute Script**:
   - Click Execute Script to run the script on selected databases.
   - Monitor progress in the Output tab via the progress bar and status log.
   - Stop execution with Stop Execution if needed.

6. **View and Export Results**:
   - Query results (for SELECT statements) appear in a table in the Output tab.
   - Click Export Results to save results as a CSV file.

7. **Switch Themes**:
   - Toggle between light and dark themes using the theme button in the status bar.

## Project Structure
```
multi-db-sql-runner/
├── main.py               # Main application script
├── thread_login.py       # Login dialog implementation
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── assets/              # (Optional) Icons or other resources
```

## Code Architecture

- **Theme System**:
  - Theme, LightTheme, DarkTheme, ThemeManager: Manage UI themes with observer pattern.

- **Database System**:
  - ConnectionFactory, SQLServerConnectionFactory: Handle SQL Server connections.
  - DatabaseManager: Manage database operations and async loading.

- **Script Execution**:
  - ScriptExecutor: Execute SQL scripts across multiple databases with progress tracking.

- **UI Implementation**:
  - SQLAppUI: Main UI with tabs for databases, scripts, and output.
  - TextLineNumbers: Custom widget for script editor line numbers.
  - Interfaces (LoggingInterface, ProgressInterface, ResultsInterface, ThemeObserver) for extensibility.

- **Application**:
  - SQLApp: Orchestrates the application, integrating UI and database components.

## Debugging Tips

If the database list doesn't load:

1. **Check Console Output**:
   - Look for connection errors or empty database lists in logs from list_databases.

2. **Verify Credentials**:
   - Ensure server name, username, password, and driver are correct in the login dialog.

3. **Test Connection**:
   - Use SSMS to connect to the server and run:
     ```sql
     SELECT name FROM sys.databases WHERE database_id > 4;
     ```

4. **Check ODBC Driver**:
   - Confirm the driver is installed and matches the one specified.

5. **Enable Windows Authentication**:
   - If applicable, set use_windows_auth=True in SQLServerConnectionFactory.

## Limitations

- **SQL Server Only**: Currently supports Microsoft SQL Server via pyodbc. Other DBMS (e.g., MySQL, PostgreSQL) require additional connection factories.
- **Single Server**: Limited to one SQL Server instance at a time.
- **No Query Validation**: Users must ensure SQL scripts are valid to avoid errors.
- **Performance**: Executing scripts on many databases may be slow, depending on server performance and network latency.

## Future Enhancements

- **Multi-DBMS Support**: Add connection factories for MySQL, PostgreSQL, etc.
- **Script Validation**: Implement SQL syntax checking before execution.
- **Batch Processing Options**: Allow parallel execution for faster processing on large database sets.
- **Query History**: Save and reload previously executed scripts.
- **Advanced Filtering**: Add regex or advanced search for database selection.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch (git checkout -b feature-name).
3. Commit changes (git commit -m "Add feature").
4. Push to the branch (git push origin feature-name).
5. Open a pull request.

Please include tests and documentation for new features.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For questions or support, contact the project maintainer at [nitinvasishtha16@example.com] or open an issue on the repository.

Happy Querying! 🚀