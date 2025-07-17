from database.queries import (find_duplicate_columns_enhanced, extract_columns,
                              export_table_to_excel, comprehensive_table_analysis,
                              run_comprehensive_analysis)
from database.connection import get_db_session
from sqlalchemy import text
from api.openrouter import evaluate_all_architectures
import pandas as pd


def run_table_analysis():
    """Run the comprehensive cloud cost and structure analysis"""
    print("Running comprehensive database analysis...")

    # Perform full database analysis and export options
    results = run_comprehensive_analysis()

    # Optional: Export sample data for manual inspection
    export_sample_data = input("\nWould you like to export sample data to Excel? (y/n): ")
    if export_sample_data.lower() == 'y':
        tables = ["aws-ec2-proc", "aws-s3-proc", "aws-rds-full", "aws-lambda-full"]
        for table in tables:
            export_table_to_excel(table, limit=100)  # Export first 100 rows

    return results


def explore_specific_table(table_name):
    """Helper function to explore a specific table in detail"""
    print(f"\n=== EXPLORING TABLE: {table_name} ===")

    # Show basic info
    print(f"Row count: {count_table_rows(table_name)}")

    # Show column structure
    columns = extract_columns(table_name)
    print(f"Columns ({len(columns)}): {', '.join(columns)}")

    # Show sample data
    fetch_table_data(table_name, limit=3)

    # Show some specific column samples
    important_patterns = ['price', 'cost', 'type', 'region', 'memory', 'cpu']
    for pattern in important_patterns:
        matching_cols = [col for col in columns if pattern.lower() in col.lower()]
        for col in matching_cols[:2]:  # Max 2 columns per pattern
            fetch_column_data(table_name, col, limit=5)


def fetch_column_data(table_name, column_name, limit=10):
    """Fetch and print data from a specified column"""
    session = get_db_session()
    try:
        query = text(
            f'SELECT DISTINCT "{column_name}" FROM "{table_name}" WHERE "{column_name}" IS NOT NULL LIMIT {limit}')
        result = session.execute(query)

        print(f"\n--- Sample '{column_name}' values from {table_name} ---")
        for row in result:
            print(f"  {row[0]}")
    except Exception as e:
        print(f"Error fetching '{column_name}' from {table_name}: {e}")
    finally:
        session.close()


def fetch_table_data(table_name, limit=5):
    """Fetch limited rows from a table"""
    session = get_db_session()
    try:
        query = text(f'SELECT * FROM "{table_name}" LIMIT {limit}')
        result = session.execute(query)

        column_names = result.keys()
        print(f"\n--- Sample data from {table_name} ---")
        print(f"Columns: {', '.join(column_names)}")
        print("-" * 50)

        for i, row in enumerate(result, 1):
            print(f"Row {i}:")
            for col_name, value in zip(column_names, row):
                # Truncate long values for readability
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
                print(f"  {col_name}: {display_value}")
            print()
    except Exception as e:
        print(f"Error fetching data from {table_name}: {e}")
    finally:
        session.close()


def count_table_rows(table_name):
    """Count rows in a table"""
    session = get_db_session()
    try:
        query = text(f'SELECT COUNT(*) FROM "{table_name}"')
        row_count = session.execute(query).scalar_one()
        return row_count
    except Exception as e:
        print(f"Error counting rows in {table_name}: {e}")
        return -1
    finally:
        session.close()


def interactive_exploration():
    """Interactive mode for exploring specific aspects"""
    tables = ["aws-ec2-proc", "aws-s3-proc", "aws-rds-full", "aws-lambda-full"]

    while True:
        print("\n" + "=" * 50)
        print("INTERACTIVE EXPLORATION")
        print("=" * 50)
        print("1. Run full analysis")
        print("2. Explore specific table")
        print("3. Export table to Excel")
        print("4. Check table row counts")
        print("5. Exit")

        choice = input("\nEnter your choice (1-5): ")

        if choice == '1':
            run_table_analysis()
        elif choice == '2':
            print("\nAvailable tables:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
            try:
                table_idx = int(input("Select table number: ")) - 1
                if 0 <= table_idx < len(tables):
                    explore_specific_table(tables[table_idx])
                else:
                    print("Invalid table number")
            except ValueError:
                print("Please enter a valid number")
        elif choice == '3':
            print("\nAvailable tables:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
            try:
                table_idx = int(input("Select table number: ")) - 1
                if 0 <= table_idx < len(tables):
                    limit = input("Enter row limit (default 100): ")
                    limit = int(limit) if limit.isdigit() else 100
                    export_table_to_excel(tables[table_idx], limit=limit)
                else:
                    print("Invalid table number")
            except ValueError:
                print("Please enter a valid number")
        elif choice == '4':
            for table in tables:
                count = count_table_rows(table)
                print(f"{table}: {count:,} rows")
        elif choice == '5':
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    print("Choose mode:")
    print("1. Run database analysis (Part 1)")
    print("2. Run architecture ranking (Part 2)")
    print("3. Interactive exploration (optional)")

    choice = input("Enter your choice (1/2/3): ").strip()

    if choice == "1":
        run_table_analysis()  # runs run_comprehensive_analysis + optional Excel export prompt

    elif choice == "2":
        results = evaluate_all_architectures("architectures.json")
        ranked = sorted(results, key=lambda x: (x["overall"] is not None, x["overall"]), reverse=True)

        print("\nRanked Architectures:")
        for i, arch in enumerate(ranked, start=1):
            name = arch.get("Architecture", "Unnamed Architecture")
            overall = arch.get("overall")
            score_display = f"{overall:.2f}" if isinstance(overall, (int, float)) else "N/A"
            print(f"{i}. {name} — Overall Score: {score_display}")

        # Optionally export to CSV
        # pd.DataFrame(ranked).to_csv("architecture_rankings.csv", index=False)

    elif choice == "3":
        interactive_exploration()

    else:
        print("Invalid option.")

