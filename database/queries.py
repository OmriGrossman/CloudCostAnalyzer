from sqlalchemy import inspect, text
from database.connection import get_db_engine, get_db_session
import pandas as pd
from collections import defaultdict

engine = get_db_engine()


def find_duplicate_columns(tables):
    """
    Identify duplicate columns within and across the provided tables.

    Args:
        tables (list): List of table names to inspect.

    Returns:
        dict: Mapping of table names to duplicate column information.
    """
    inspector = inspect(engine)
    duplicate_columns = {}

    for table in tables:
        # Get column names for the current table
        columns = [col['name'] for col in inspector.get_columns(table)]

        # Check for duplicates within the same table
        duplicates_within = [col for col in columns if columns.count(col) > 1]

        # Add results to the dictionary
        duplicate_columns[table] = {
            "within": duplicates_within,
            "across": []
        }

    # Check for duplicates across tables
    all_columns = {table: [col['name'] for col in inspector.get_columns(table)] for table in tables}
    for i, table1 in enumerate(tables):
        for table2 in tables[i + 1:]:
            common = set(all_columns[table1]).intersection(all_columns[table2])
            if common:  # Only add if there are common columns
                duplicate_columns[table1]["across"].append({table2: list(common)})

    return duplicate_columns


def find_shared_columns(tables, min_occurrence=3):
    """
    Finds columns that appear in at least `min_occurrence` tables from the list.

    Args:
        tables (list): List of table names to inspect.
        min_occurrence (int): Minimum number of tables a column must appear in to be considered 'shared'.

    Returns:
        list: A list of dictionaries, each containing a column name, its count, and the tables it appears in.
    """
    session = get_db_session()
    inspector = inspect(session.bind)

    column_map = {}

    for table in tables:
        columns = [col["name"] for col in inspector.get_columns(table)]
        for col in columns:
            key = col.lower()  # use lowercase for consistency
            if key not in column_map:
                column_map[key] = {"count": 0, "tables": set()}
            column_map[key]["count"] += 1
            column_map[key]["tables"].add(table)

    # Filter columns by minimum occurrence
    shared = []
    for col, meta in column_map.items():
        if meta["count"] >= min_occurrence:
            shared.append({
                "column": col,
                "count": meta["count"],
                "tables": sorted(meta["tables"])
            })

    return sorted(shared, key=lambda x: -x["count"])


def extract_columns(table):
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table)]
    return columns


def export_table_to_excel(table_name, file_name=None, limit=10):
    """
    Exports a table's data to an Excel file, with an optional row limit.

    Args:
        table_name (str): The name of the table to export.
        file_name (str, optional): The name of the Excel file to create.
                                   Defaults to f"{table_name}_data.xlsx".
        limit (int, optional): The maximum number of rows to export. If None, all rows are exported.
    """
    if file_name is None:
        file_name = f"{table_name}_data.xlsx"

    try:
        # Construct the SQL query with an optional LIMIT clause
        sql_query = f"SELECT * FROM \"{table_name}\""
        if limit is not None and isinstance(limit, int) and limit > 0:
            sql_query += f" LIMIT {limit}"

        # Use pandas to read the results of the SQL query into a DataFrame
        df = pd.read_sql_query(text(sql_query), con=engine)

        # Export the DataFrame to an Excel file
        df.to_excel(file_name, index=False)  # index=False prevents writing DataFrame index as a column

        row_count = len(df)
        print(f"Successfully exported {row_count} rows from '{table_name}' to '{file_name}'")

    except Exception as e:
        print(f"An error occurred while exporting {table_name} to Excel: {e}")


# Enhanced analysis functions for the assignment
def comprehensive_table_analysis(tables):
    """
    Comprehensive analysis of database tables to answer all assignment questions.

    Args:
        tables (list): List of table names to analyze

    Returns:
        dict: Complete analysis results
    """
    inspector = inspect(engine)
    session = get_db_session()

    analysis_results = {
        'duplicate_info': {},
        'essential_columns': {},
        'table_specific_columns': {},
        'redundant_columns': {},
        'column_details': {}
    }

    # Get detailed column information for all tables
    all_table_columns = {}
    for table in tables:
        columns_info = inspector.get_columns(table)
        all_table_columns[table] = columns_info
        analysis_results['column_details'][table] = columns_info

    # Question 1: Duplicate Information Analysis
    # Pass the session to the enhanced function for data sampling
    analysis_results['duplicate_info'] = find_duplicate_columns_enhanced(tables, all_table_columns, session)

    # Question 3: Most Important Table-Specific Columns
    analysis_results['table_specific_columns'] = identify_table_specific_columns(tables, all_table_columns, session)

    # Question 4: Redundant Columns
    analysis_results['redundant_columns'] = identify_redundant_columns(tables, all_table_columns, session)

    session.close()
    return analysis_results


def fetch_distinct_column_values(session, table_name, column_name, limit=100):
    """Fetches a sample of distinct non-null values from a column."""
    try:
        query = text(
            f'SELECT DISTINCT "{column_name}" FROM "{table_name}" WHERE "{column_name}" IS NOT NULL LIMIT {limit}'
        )
        result = session.execute(query).fetchall()
        # Convert to a set for faster comparison
        return {str(row[0]) for row in result}
    except Exception as e:
        print(f"Error fetching distinct values for {table_name}.{column_name}: {e}")
        return set()


def find_duplicate_columns_enhanced(tables, all_table_columns, session, sample_limit=500):
    """
    Enhanced duplicate column detection with semantic analysis based on data content.
    """
    duplicates = {}
    column_data_samples = defaultdict(dict)  # Stores {table: {column_name: set_of_sample_values}}

    # First, collect column data samples for all columns in all tables
    for table in tables:
        columns = [col['name'] for col in all_table_columns[table]]
        for col_name in columns:
            column_data_samples[table][col_name] = fetch_distinct_column_values(session, table, col_name, sample_limit)

    for table in tables:
        columns = [col['name'] for col in all_table_columns[table]]

        # Within table duplicates (exact name matches, as before)
        within_duplicates = [col for col in set(columns) if columns.count(col) > 1]

        duplicates[table] = {
            "within_name_match": within_duplicates,
            "across_name_match": [],  # Rename from "across" for clarity
            "semantic_data_match": []  # New category for data-based duplicates
        }

    # Across table duplicates (name match, as before)
    all_column_names = {table: [col['name'] for col in all_table_columns[table]] for table in tables}
    for i, table1 in enumerate(tables):
        for table2 in tables[i + 1:]:
            common_names = set(all_column_names[table1]).intersection(all_column_names[table2])
            if common_names:
                duplicates[table1]["across_name_match"].append({table2: list(common_names)})
                # Also add to table2 for a complete view if needed, or handle symmetrically later
                if table2 not in duplicates:
                    duplicates[table2] = {"within_name_match": [], "across_name_match": [], "semantic_data_match": []}
                duplicates[table2]["across_name_match"].append({table1: list(common_names)})

    # Semantic Data Duplicates (new logic)
    # This checks for columns in different tables (or even the same table, though less common for semantic)
    # that have similar distinct data values, even if their names differ.
    processed_pairs = set() # To avoid redundant comparisons (A vs B is same as B vs A)

    for i, table1_name in enumerate(tables):
        for col1_name, col1_sample in column_data_samples[table1_name].items():
            if not col1_sample: # Skip if no data
                continue

            for j, table2_name in enumerate(tables):
                # Ensure we don't compare a table with itself for cross-table semantic duplicates
                # And avoid re-processing pairs (e.g., (A,B) and then (B,A))
                if (table1_name == table2_name) or ((table1_name, table2_name) in processed_pairs) or ((table2_name, table1_name) in processed_pairs):
                    continue

                for col2_name, col2_sample in column_data_samples[table2_name].items():
                    if not col2_sample: # Skip if no data
                        continue

                    # Heuristic for semantic duplication: significant overlap in distinct values
                    # You might need to adjust this heuristic based on data characteristics.
                    # For example, Jaccard similarity: |A intersect B| / |A union B|
                    intersection = col1_sample.intersection(col2_sample)
                    union = col1_sample.union(col2_sample)

                    if len(union) > 0: # Avoid division by zero
                        jaccard_similarity = len(intersection) / len(union)
                        # Define a threshold for considering them semantically duplicate
                        if jaccard_similarity > 0.8: # Adjust this threshold (e.g., 0.8 means 80% overlap)
                            duplicates[table1_name]["semantic_data_match"].append({
                                'column1': col1_name,
                                'table2': table2_name,
                                'column2': col2_name,
                                'similarity': f"{jaccard_similarity:.2f}",
                                'reason': f"High data overlap ({jaccard_similarity:.2f}) suggests semantic duplication."
                            })
                processed_pairs.add((table1_name, table2_name))

    # Clean up the output format for semantic_data_match
    for table_name in duplicates:
        # Remove reverse entries if they exist, or structure as pairs
        unique_semantic_matches = []
        seen_combinations = set()
        for match in duplicates[table_name]["semantic_data_match"]:
            col1 = match['column1']
            table2 = match['table2']
            col2 = match['column2']
            # Create a canonical representation for the pair to avoid duplicates
            if (table_name, col1, table2, col2) not in seen_combinations and \
               (table2, col2, table_name, col1) not in seen_combinations:
                unique_semantic_matches.append(match)
                seen_combinations.add((table_name, col1, table2, col2))
                seen_combinations.add((table2, col2, table_name, col1)) # Mark reverse as seen too
        duplicates[table_name]["semantic_data_match"] = unique_semantic_matches

    return duplicates


def identify_table_specific_columns(tables, all_table_columns, session):
    """Identify most important columns for each specific service type"""
    service_specific = {}

    service_priorities = {
        'aws-ec2-proc': ['instance_type', 'vcpu', 'memory', 'price', 'region'],
        'aws-s3-proc': ['storage_class', 'price', 'durability', 'availability'],
        'aws-rds-full': ['engine', 'instance_class', 'storage_type', 'price', 'multi_az'],
        'aws-lambda-full': ['memory', 'price', 'duration', 'concurrent_executions']
    }

    for table in tables:
        service_specific[table] = {
            'most_critical': [],
            'configuration_specific': []
        }

        available_columns = [col['name'].lower() for col in all_table_columns[table]]

        if table in service_priorities:
            for priority_col in service_priorities[table]:
                matching_cols = [col for col in available_columns if priority_col.lower() in col]
                if matching_cols:
                    service_specific[table]['most_critical'].extend(matching_cols)

        # Identify configuration-specific columns
        config_patterns = ['type', 'class', 'size', 'tier', 'mode', 'engine', 'version']
        for col_name in available_columns:
            if any(pattern in col_name for pattern in config_patterns):
                if col_name not in service_specific[table]['most_critical']:
                    service_specific[table]['configuration_specific'].append(col_name)

    return service_specific


def identify_redundant_columns(tables, all_table_columns, session):
    """Identify potentially redundant columns including empty/near-empty ones."""
    redundant = {}

    for table in tables:
        redundant[table] = {
            'likely_redundant': [],
            'potential_redundant': []
        }

        columns = [col['name'] for col in all_table_columns[table]]

        # --- Existing keyword-based redundancy check ---
        redundant_patterns = [
            'id', 'uuid', 'arn', 'url', 'link', 'description', 'note',
            'created', 'modified', 'updated', 'timestamp'
        ]

        for col_name in columns:
            col_lower = col_name.lower()

            if any(pattern in col_lower for pattern in redundant_patterns):
                if 'id' in col_lower or 'arn' in col_lower:
                    redundant[table]['potential_redundant'].append({
                        'column': col_name,
                        'reason': 'Identifier column - may not be needed for price comparison'
                    })
                else:
                    redundant[table]['likely_redundant'].append({
                        'column': col_name,
                        'reason': 'Metadata column (keyword match) - likely not essential for service selection'
                    })

        # --- New: Check for empty/near-empty columns ---
        # Define a threshold for considering a column "empty"
        # For example, if more than 95% of its values are NULL
        EMPTY_COLUMN_THRESHOLD = 0.95

        for col_name in columns:
            # Query to count NULLs and total rows for the column
            try:
                # Get total row count for the table
                row_count_query = text(f"SELECT COUNT(*) FROM \"{table}\"")
                total_rows = session.execute(row_count_query).scalar()

                if total_rows == 0: # Handle empty tables
                    continue

                # Count non-NULL values for the column
                non_null_count_query = text(f"SELECT COUNT(\"{col_name}\") FROM \"{table}\"")
                non_null_count = session.execute(non_null_count_query).scalar()

                # Calculate null percentage
                null_percentage = (total_rows - non_null_count) / total_rows

                if null_percentage >= EMPTY_COLUMN_THRESHOLD:
                    redundant[table]['likely_redundant'].append({
                        'column': col_name,
                        'reason': f'Empty/Near-empty column ({null_percentage:.2%} nulls) - contains mostly null values'
                    })
            except Exception as e:
                # Handle cases where column might not exist or other query errors
                print(f"Warning: Could not check emptiness for column '{col_name}' in table '{table}'. Error: {e}")
                continue

    return redundant


def print_analysis_report(analysis_results):
    """Print a comprehensive analysis report"""
    print("=" * 80)
    print("COMPREHENSIVE DATABASE ANALYSIS REPORT")
    print("=" * 80)

    # Question 1: Duplicates
    print("\n1. DUPLICATE INFORMATION ANALYSIS")
    print("-" * 40)
    for table, duplicates in analysis_results['duplicate_info'].items():
        print(f"\nTable: {table}")
        if duplicates['within_name_match']:
            print(f"  Within-table duplicates (name match): {duplicates['within_name_match']}")
        if duplicates['across_name_match']:
            print(f"  Cross-table duplicates (name match): {duplicates['across_name_match']}")
        if duplicates['semantic_data_match']:
            print(f"  Semantic Data Duplicates:")
            for match in duplicates['semantic_data_match']:
                print(f"    - '{match['column1']}' (in {table}) and '{match['column2']}' (in {match['table2']}) "
                      f"have high data overlap ({match['similarity']}). Reason: {match['reason']}")
        if not duplicates['within_name_match'] and not duplicates['across_name_match'] and not duplicates['semantic_data_match']:
            print("  No significant duplicates found (by name or data sample).")

    # Question 2: Essential Columns (Shared Across Tables)
    print("\n2. SHARED ESSENTIAL COLUMNS ACROSS SERVICES")
    print("-" * 50)

    shared_columns = find_shared_columns(
        tables=["aws-ec2-proc", "aws-s3-proc", "aws-rds-full", "aws-lambda-full"],
        min_occurrence=4
    )

    if shared_columns:
        print(f"\nColumns appearing in at least 3 out of 4 tables:\n")
        for col in shared_columns:
            print(f"  - {col['column']}  |  Appears in {col['count']} tables: {', '.join(col['tables'])}")
    else:
        print("  No shared columns found across 3 or more tables.")

    # Question 3: Table-specific columns
    print("\n\n3. MOST IMPORTANT TABLE-SPECIFIC COLUMNS")
    print("-" * 40)
    for table, specifics in analysis_results['table_specific_columns'].items():
        print(f"\nTable: {table}")
        if specifics['most_critical']:
            print(f"  Most critical: {', '.join(specifics['most_critical'])}")
        if specifics['configuration_specific']:
            print(f"  Configuration-specific: {', '.join(specifics['configuration_specific'])}")

    # Question 4: Redundant columns
    print("\n\n4. REDUNDANT COLUMNS")
    print("-" * 40)
    for table, redundant in analysis_results['redundant_columns'].items():
        print(f"\nTable: {table}")
        if redundant['likely_redundant']:
            print("  Likely redundant:")
            for col in redundant['likely_redundant']:
                print(f"    - {col['column']}: {col['reason']}")
        if redundant['potential_redundant']:
            print("  Potentially redundant:")
            for col in redundant['potential_redundant']:
                print(f"    - {col['column']}: {col['reason']}")


# Usage function for main.py
def run_comprehensive_analysis():
    """Main function to run the comprehensive analysis"""
    tables = ["aws-ec2-proc", "aws-s3-proc", "aws-rds-full", "aws-lambda-full"]

    print("Starting comprehensive database analysis...")
    results = comprehensive_table_analysis(tables)

    print_analysis_report(results)

    return results
