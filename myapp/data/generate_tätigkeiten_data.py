import pandas as pd
import os
import random

# Set up paths
base_dir = os.path.dirname(os.path.abspath(__file__))
data_csv_path = os.path.join(base_dir, 'Data2.csv')
output_csv_path = os.path.join(base_dir, 'Enriched_Tätigkeiten_Data.csv')

# Load the data with adjusted column names
df = pd.read_csv(data_csv_path, encoding='utf-8-sig')
df.columns = df.columns.str.strip()  # Remove any extra whitespace

# Select only relevant columns, including the 'Project' column to keep it in the final output
project_data = df[['Project', 'DIN_Ebene1', 'DIN_Ebene1_Beschreibung', 'Gesamtkosten']].copy()

# Define tasks to split "Gesamtkosten" across
tasks = [
    'Inspektion', 'Wartung', 'Zustandsermittlung', 'Revision', 'Tausch',
    'Betriebsprüfung', 'Betriebsservice', 'Vorbereitung', 'Nachbereitung', 'Reparatur am Objekt'
]

# Apply random distribution to "Gesamtkosten" across tasks
for index, row in project_data.iterrows():
    remaining_cost = row['Gesamtkosten']
    distributed_costs = []
    
    # Distribute costs randomly, ensuring a minimum of 5% and a maximum of 15% for each task
    for i in range(len(tasks) - 1):
        max_allocation = min(0.15 * row['Gesamtkosten'], remaining_cost)
        min_allocation = 0.05 * row['Gesamtkosten']
        allocated_cost = random.uniform(min_allocation, max_allocation)
        distributed_costs.append(allocated_cost)
        remaining_cost -= allocated_cost
    
    # Assign remaining cost to the last task to ensure total matches
    distributed_costs.append(remaining_cost)
    
    # Assign these values back to the DataFrame
    for i, task in enumerate(tasks):
        project_data.at[index, task] = distributed_costs[i]

# Save the enriched DataFrame to a new CSV, including 'Project' to use for filtering
project_data.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
