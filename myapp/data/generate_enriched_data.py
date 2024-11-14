import pandas as pd
import os
import random

# Set up paths
base_dir = os.path.dirname(os.path.abspath(__file__))
data_csv_path = os.path.join(base_dir, 'Data2.csv')
enriched_csv_path = os.path.join(base_dir, 'Enriched_Data2.csv')

# Load and rename columns for consistency
df = pd.read_csv(data_csv_path, encoding='utf-8-sig')
df.columns = df.columns.str.strip()
df.rename(columns={
    'prav. Materialkosten': 'prav_Materialkosten',
    'prav. Personalkosten': 'prav_Personalkosten',
    'korr. Materialkosten': 'korr_Materialkosten',
    'korr. Personalkosten': 'korr_Personalkosten'
}, inplace=True)

# Define suppliers
suppliers = ["Bode", "Kangni", "Ultimate"]

# Create enriched data
enriched_data = pd.DataFrame()

for project in df['Project'].unique():
    project_data = df[df['Project'] == project].copy()

    # Only apply supplier variations if the project is "HFX"
    if project == "HFX":
        for i, supplier in enumerate(suppliers):
            supplier_data = project_data.copy()
            supplier_data['Project'] = f"{project} ({supplier})"
            
            # No modification for the first supplier
            if i > 0:
                for column in ['prav_Materialkosten', 'prav_Personalkosten', 'korr_Materialkosten', 'korr_Personalkosten']:
                    supplier_data[column] *= 1 + random.uniform(0.05, 0.10)
            
            enriched_data = pd.concat([enriched_data, supplier_data])
    else:
        # Add other projects without modification
        enriched_data = pd.concat([enriched_data, project_data])

# Save the enriched data
enriched_data.to_csv(enriched_csv_path, index=False, encoding='utf-8-sig')
