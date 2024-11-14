# myapp/views.py

import os
import pandas as pd
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import csv
import random

# Importiere die project_images Zuordnung
from .project_images import project_images  # Stelle sicher, dass project_images.py im selben Verzeichnis liegt oder passe den Pfad an

# Authentifizierungs-Views

def login_view(request):
    error_message = None  # Initialize error message as None

    if request.method == "POST":
        password = request.POST.get("password")
        correct_password = "123"  # Replace with your actual password

        if password == correct_password:
            request.session['authenticated'] = True
            return redirect('dashboard')

        # Set error message if password is incorrect
        error_message = "Incorrect password. Please try again."

    return render(request, "login.html", {"error_message": error_message})


def logout(request):
    auth_logout(request)
    return redirect('login')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def check_authentication(request):
    return request.session.get('authenticated', False)


def protected_view(view_func):
    def wrapper(request, *args, **kwargs):
        if not check_authentication(request):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Dashboard-View

@protected_view
def dashboard(request):
    # Load project summaries or a list of project names
    project_names = [project['Project'] for project in PROJECT_SUMMARIES]
    project_names.append("Neues Projekt anlegen")  # Add this to create the button at the end

    context = {
        'projects': project_names
    }

    return render(request, 'lcc-dashboard.html', context)

# Helper-Funktion zum Laden der Projektzusammenfassungen

def load_project_summaries():
    # Path to the CSV file
    csv_file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'Data2.csv')

    try:
        # Load CSV for aggregated data
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()

        # Rename columns for consistency
        df.rename(columns={
            'prav. Materialkosten': 'prav_Materialkosten',
            'prav. Personalkosten': 'prav_Personalkosten',
            'korr. Materialkosten': 'korr_Materialkosten',
            'korr. Personalkosten': 'korr_Personalkosten'
        }, inplace=True)

        # Calculate preventive and corrective costs for each project
        df['Gesamtkosten'] = (
            df['prav_Materialkosten'].fillna(0) +
            df['prav_Personalkosten'].fillna(0) +
            df['korr_Materialkosten'].fillna(0) +
            df['korr_Personalkosten'].fillna(0)
        )

        project_summaries = df.groupby('Project').agg({
            'prav_Materialkosten': 'sum',
            'prav_Personalkosten': 'sum',
            'korr_Materialkosten': 'sum',
            'korr_Personalkosten': 'sum',
            'Gesamtkosten': 'sum'
        }).reset_index()

        # Convert to a list of dictionaries for easier access in templates
        return project_summaries.to_dict(orient='records')

    except Exception as e:
        print(f"Error loading project summaries: {e}")
        return []

PROJECT_SUMMARIES = load_project_summaries()

# Project Details-View

@protected_view
def project_details(request, project_name):
    csv_file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'Data2.csv')

    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()

        df.rename(columns={
            'prav. Materialkosten': 'prav_Materialkosten',
            'prav. Personalkosten': 'prav_Personalkosten',
            'korr. Materialkosten': 'korr_Materialkosten',
            'korr. Personalkosten': 'korr_Personalkosten'
        }, inplace=True)

        project_data = df[df['Project'].str.strip() == project_name].copy()

        if project_data.empty:
            return HttpResponse(f"The project '{project_name}' was not found.", status=404)

        project_data['Gesamtkosten'] = (
            project_data['prav_Materialkosten'].fillna(0) +
            project_data['prav_Personalkosten'].fillna(0) +
            project_data['korr_Materialkosten'].fillna(0) +
            project_data['korr_Personalkosten'].fillna(0)
        )

        total_cost_sum = project_data['Gesamtkosten'].sum()
        preventive_cost_sum = project_data[['prav_Materialkosten', 'prav_Personalkosten']].sum().sum()
        corrective_cost_sum = project_data[['korr_Materialkosten', 'korr_Personalkosten']].sum().sum()

        personal_sum = project_data[['prav_Personalkosten', 'korr_Personalkosten']].sum().sum()
        material_sum = project_data[['korr_Materialkosten', 'prav_Materialkosten']].sum().sum()

        structured_data = {}
        for _, row in project_data.iterrows():
            din1 = row['DIN_Ebene1']
            din2 = row['DIN_Ebene2']
            din3 = row['DIN_Ebene3']

            # Ebene 1 hinzufügen
            if din1 not in structured_data:
                structured_data[din1] = {
                    'description': row['DIN_Ebene1_Beschreibung'],
                    'total_cost': 0,
                    'total_prav_material': 0,
                    'total_prav_personal': 0,
                    'total_korr_material': 0,
                    'total_korr_personal': 0,
                    'children': {}
                }

            structured_data[din1]['total_cost'] += row['Gesamtkosten']
            structured_data[din1]['total_prav_material'] += row['prav_Materialkosten']
            structured_data[din1]['total_prav_personal'] += row['prav_Personalkosten']
            structured_data[din1]['total_korr_material'] += row['korr_Materialkosten']
            structured_data[din1]['total_korr_personal'] += row['korr_Personalkosten']

            # Ebene 2 hinzufügen
            if pd.notna(din2):
                if din2 not in structured_data[din1]['children']:
                    structured_data[din1]['children'][din2] = {
                        'description': row['DIN_Ebene2_Beschreibung'],
                        'total_cost': 0,
                        'total_prav_material': 0,
                        'total_prav_personal': 0,
                        'total_korr_material': 0,
                        'total_korr_personal': 0,
                        'children': {}
                    }

                structured_data[din1]['children'][din2]['total_cost'] += row['Gesamtkosten']
                structured_data[din1]['children'][din2]['total_prav_material'] += row['prav_Materialkosten']
                structured_data[din1]['children'][din2]['total_prav_personal'] += row['prav_Personalkosten']
                structured_data[din1]['children'][din2]['total_korr_material'] += row['korr_Materialkosten']
                structured_data[din1]['children'][din2]['total_korr_personal'] += row['korr_Personalkosten']

                # Ebene 3 hinzufügen
                if pd.notna(din3):
                    structured_data[din1]['children'][din2]['children'][din3] = {
                        'description': row['DIN_E3_Beschreibung'],
                        'prav_Materialkosten': row['prav_Materialkosten'],
                        'prav_Personalkosten': row['prav_Personalkosten'],
                        'korr_Materialkosten': row['korr_Materialkosten'],
                        'korr_Personalkosten': row['korr_Personalkosten'],
                        'Gesamtkosten': row['Gesamtkosten']
                    }

        detailed_data = project_data.to_dict(orient='records')

        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL

        context = {
            'project_name': project_name,
            'project_data': detailed_data,
            'structured_data': structured_data,
            'total_cost_sum': total_cost_sum,
            'preventive_cost_sum': preventive_cost_sum,
            'corrective_cost_sum': corrective_cost_sum,
            'material_sum': material_sum,
            'personal_sum': personal_sum,
            'image_url': image_url,  # Füge image_url zum Kontext hinzu
        }

    except Exception as e:
        return HttpResponse(f"Error loading data: {e}", status=500)

    return render(request, 'lcc-projects.html', context)

# Benchmarking-View

@protected_view
def benchmarking(request, project_name, filter_din=None):
    # Use enriched CSV for benchmarking only
    csv_file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'Enriched_Data2.csv')

    try:
        # Load the enriched data
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        df.rename(columns={
            'prav. Materialkosten': 'prav_Materialkosten',
            'prav. Personalkosten': 'prav_Personalkosten',
            'korr. Materialkosten': 'korr_Materialkosten',
            'korr. Personalkosten': 'korr_Personalkosten',
            'DIN_Ebene1_Beschreibung': 'DIN_Ebene1_Beschreibung'
        }, inplace=True)

        # Apply DIN filter if provided
        din_values = df['DIN_Ebene1_Beschreibung'].dropna().unique()
        if filter_din:
            df = df[df['DIN_Ebene1_Beschreibung'] == filter_din]

        # Aggregate cost data
        cost_data = df.groupby('Project').agg({
            'prav_Materialkosten': 'sum',
            'prav_Personalkosten': 'sum',
            'korr_Materialkosten': 'sum',
            'korr_Personalkosten': 'sum'
        }).reset_index()

        # Sort projects, placing "HFX" projects at the beginning
        cost_data['is_hfx'] = cost_data['Project'].str.startswith('HFX')
        cost_data = cost_data.sort_values(by='is_hfx', ascending=False).drop(columns=['is_hfx'])

        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL

        context = {
            'project_name': project_name,
            'cost_data': cost_data.to_dict(orient='records'),
            'din_values': din_values,
            'selected_din': filter_din,
            'image_url': image_url,  # Füge image_url zum Kontext hinzu
        }

    except Exception as e:
        print(f"Error loading benchmarking data: {e}")
        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL
        context = {
            'project_name': project_name,
            'cost_data': [],
            'din_values': [],
            'selected_din': None,
            'image_url': image_url,  # Füge image_url zum Kontext hinzu
        }

    return render(request, 'lcc-benchmarking.html', context)

# Export CSV-View

@protected_view
def export_csv(request, project_name, filter_din="all"):
    # Set the filename based on the selected Baugruppe (DIN filter)
    selected_filter = "alle" if filter_din.lower() == "all" else filter_din
    filename = f"Benchmarking_Baugruppen_{selected_filter}_LCC_data.csv"

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Define the path to the CSV file
    csv_file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'Enriched_Data2.csv')

    try:
        # Load the CSV file
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()

        # Rename columns for consistency
        df.rename(columns={
            'prav. Materialkosten': 'prav_Materialkosten',
            'prav. Personalkosten': 'prav_Personalkosten',
            'korr. Materialkosten': 'korr_Materialkosten',
            'korr. Personalkosten': 'korr_Personalkosten'
        }, inplace=True)

        # Apply filtering if filter_din is not "all"
        if filter_din.lower() != "all":
            df = df[df['DIN_Ebene1_Beschreibung'].str.strip() == filter_din]

            # Check if there’s data after filtering
            if df.empty:
                return HttpResponse("No data available for the selected filter.", content_type="text/plain")

        # Write the CSV headers, including "Project" as the first column
        writer = csv.writer(response)
        writer.writerow([
            'Project', 'DIN Ebene 1', 'DIN Ebene 1 Beschreibung', 'DIN Ebene 2', 'DIN Ebene 2 Beschreibung',
            'DIN Ebene 3', 'DIN E3 Beschreibung', 'Präv. Materialkosten',
            'Präv. Personalkosten', 'Korr. Materialkosten', 'Korr. Personalkosten', 'Gesamtkosten'
        ])

        # Write each row, including the "Project" column as the first entry
        for _, row in df.iterrows():
            writer.writerow([
                row.get('Project', ''),
                row.get('DIN_Ebene1', ''),
                row.get('DIN_Ebene1_Beschreibung', ''),
                row.get('DIN_Ebene2', ''),
                row.get('DIN_Ebene2_Beschreibung', ''),
                row.get('DIN_Ebene3', ''),
                row.get('DIN_E3_Beschreibung', ''),
                row.get('prav_Materialkosten', 0),
                row.get('prav_Personalkosten', 0),
                row.get('korr_Materialkosten', 0),
                row.get('korr_Personalkosten', 0),
                row.get('Gesamtkosten', 0)
            ])

    except Exception as e:
        return HttpResponse(f"Error exporting data: {e}", status=500)

    return response

# Workflow-View

@protected_view
def workflow(request, project_name):
    # Path to the correct CSV file (baugruppen_suppliers.csv)
    csv_file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'baugruppen_suppliers.csv')

    try:
        # Load the CSV file
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()  # Clean up any leading/trailing whitespace in column names

        # Verify column names based on the CSV structure you provided
        if 'Baugruppe' in df.columns and 'Beschreibung' in df.columns and 'Supplier' in df.columns:
            # Combine "Baugruppe" and "Beschreibung" into a single "Baugruppe" field
            df['Baugruppe'] = df['Baugruppe'] + " -- " + df['Beschreibung']

            # Add random quantities for "Menge"
            df['Menge'] = [random.randint(1, 10) for _ in range(len(df))]

            # Prepare the data for the template, ensuring 'Supplier' column is included
            workflow_data = df[['Baugruppe', 'Supplier', 'Menge']].to_dict(orient='records')
        else:
            print("Error: Expected columns not found in CSV")
            workflow_data = []

        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL

        # Pass data to the template
        context = {
            'project_name': project_name,
            'workflow_data': workflow_data,
            'image_url': image_url,  # Füge image_url zum Kontext hinzu
        }

    except Exception as e:
        print(f"Error loading workflow data: {e}")
        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL
        context = {
            'project_name': project_name,
            'workflow_data': [],
            'image_url': image_url,  # Füge image_url zum Kontext hinzu
        }

    return render(request, 'lcc-workflow.html', context)

# Projekterstellungs-View

@protected_view
def projekterstellung(request):
    if request.method == "POST":
        # Process form submission
        project_name = request.POST.get("project_name")
        project_description = request.POST.get("project_description")
        # Hier kannst du den neuen Projekt-Eintrag in die CSV oder Datenbank hinzufügen
        return redirect('dashboard')

    csv_file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'Data2.csv')
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()

        hierarchy = {}
        for _, row in df.iterrows():
            ebene1 = row['DIN_Ebene1']
            ebene2 = row.get('DIN_Ebene2', None)
            ebene3 = row.get('DIN_Ebene3', None)

            if ebene1 not in hierarchy:
                hierarchy[ebene1] = {}

            if pd.notna(ebene2):
                if ebene2 not in hierarchy[ebene1]:
                    hierarchy[ebene1][ebene2] = []

                if pd.notna(ebene3):
                    hierarchy[ebene1][ebene2].append(ebene3)

    except Exception as e:
        print(f"Error loading hierarchy data: {e}")
        hierarchy = {}

    context = {'hierarchy': hierarchy}
    return render(request, 'projekterstellung.html', context)

# Display Tätigkeiten Data-View

@protected_view
def display_taetigkeiten_data(request, project_name):
    # Set up paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_csv_path = os.path.join(base_dir, 'data', 'Enriched_Tätigkeiten_Data.csv')
    
    try:
        # Load the CSV data and replace spaces in column names with underscores
        df = pd.read_csv(data_csv_path, encoding='utf-8-sig')
        df.columns = df.columns.str.replace(' ', '_')

        # Filter the data for the selected project
        project_data = df[df['Project'] == project_name]

        # Group by 'DIN_Ebene1' and aggregate by summing the numeric columns
        grouped_data = project_data.groupby(['DIN_Ebene1', 'DIN_Ebene1_Beschreibung'], as_index=False).sum(numeric_only=True)

        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL

        # Pass the grouped data to the template
        context = {
            'project_name': project_name,
            'project_data': grouped_data.to_dict(orient='records'),
            'image_url': image_url,  # Füge image_url zum Kontext hinzu
        }

    except Exception as e:
        print(f"Error loading benchmarking data: {e}")
        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL
        context = {
            'project_name': project_name,
            'project_data': [],
            'image_url': image_url,  # Füge image_url zum Kontext hinzu
        }

    return render(request, 'lcc-taetigkeiten.html', context)

@protected_view
def display_taetigkeiten2_data(request, project_name):
    # Set up paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_csv_path = os.path.join(base_dir, 'data', 'Enriched_Tätigkeiten_Data.csv')  
    data2_csv_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'Data2.csv')  # Pfad zu Data2.csv
    
    try:
        # Lade Data2.csv für die Summenberechnung
        df_data2 = pd.read_csv(data2_csv_path, encoding='utf-8-sig')
        df_data2.columns = df_data2.columns.str.strip()
        df_data2.rename(columns={
            'prav. Materialkosten': 'prav_Materialkosten',
            'prav. Personalkosten': 'prav_Personalkosten',
            'korr. Materialkosten': 'korr_Materialkosten',
            'korr. Personalkosten': 'korr_Personalkosten'
        }, inplace=True)
        
        # Filtere Data2.csv für das ausgewählte Projekt
        project_data2 = df_data2[df_data2['Project'].str.strip() == project_name].copy()
        
        if project_data2.empty:
            return HttpResponse(f"Das Projekt '{project_name}' wurde in Data2.csv nicht gefunden oder enthält keine Daten.", status=404)
        
        # Berechne die Summen aus Data2.csv
        total_cost_sum = project_data2['prav_Materialkosten'].fillna(0).sum() + \
                         project_data2['prav_Personalkosten'].fillna(0).sum() + \
                         project_data2['korr_Materialkosten'].fillna(0).sum() + \
                         project_data2['korr_Personalkosten'].fillna(0).sum()
        preventive_cost_sum = project_data2['prav_Materialkosten'].fillna(0).sum() + \
                              project_data2['prav_Personalkosten'].fillna(0).sum()
        corrective_cost_sum = project_data2['korr_Materialkosten'].fillna(0).sum() + \
                              project_data2['korr_Personalkosten'].fillna(0).sum()
        personal_sum = project_data2['prav_Personalkosten'].fillna(0).sum() + \
                       project_data2['korr_Personalkosten'].fillna(0).sum()
        material_sum = project_data2['prav_Materialkosten'].fillna(0).sum() + \
                       project_data2['korr_Materialkosten'].fillna(0).sum()
        
        # Lade Enriched_Tätigkeiten_Data.csv für die detaillierte Tabelle
        df_taetigkeiten = pd.read_csv(data_csv_path, encoding='utf-8-sig')
        df_taetigkeiten.columns = df_taetigkeiten.columns.str.replace(' ', '_')
        
        # Überprüfe, ob alle erforderlichen Spalten vorhanden sind
        required_columns = [
            'Project', 'DIN_Ebene1', 'DIN_Ebene1_Beschreibung', 
            'Inspektion', 'Wartung', 'Zustandsermittlung',
            'Revision', 'Tausch', 'Betriebsprüfung', 'Betriebsservice',
            'Vorbereitung', 'Nachbereitung', 'Reparatur_am_Objekt', 'Gesamtkosten'
        ]
        missing_columns = [col for col in required_columns if col not in df_taetigkeiten.columns]
        if missing_columns:
            raise ValueError(f"Fehlende Spalten in Enriched_Tätigkeiten_Data.csv: {', '.join(missing_columns)}")
        
        # Filtere Enriched_Tätigkeiten_Data.csv für das ausgewählte Projekt
        project_taetigkeiten = df_taetigkeiten[df_taetigkeiten['Project'] == project_name].copy()
        
        if project_taetigkeiten.empty:
            return HttpResponse(f"Das Projekt '{project_name}' wurde in Enriched_Tätigkeiten_Data.csv nicht gefunden oder enthält keine Daten.", status=404)
        
        # Gruppiere die Daten für die Tabelle
        grouped_data = project_taetigkeiten.groupby(['DIN_Ebene1', 'DIN_Ebene1_Beschreibung'], as_index=False).sum(numeric_only=True)
        project_data_dict = grouped_data.to_dict(orient='records')
        
        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL

        # Kontext vorbereiten
        context = {
            'project_name': project_name,
            'project_data': project_data_dict,
            'image_url': image_url,
            'total_cost_sum': total_cost_sum,
            'preventive_cost_sum': preventive_cost_sum,
            'corrective_cost_sum': corrective_cost_sum,
            'material_sum': material_sum,
            'personal_sum': personal_sum,
        }

    except Exception as e:
        print(f"Error loading taetigkeiten2 data: {e}")
        # Bestimme das entsprechende Bild basierend auf project_name
        image_url = project_images.get(project_name, "https://via.placeholder.com/150")  # Standardbild-URL
        context = {
            'project_name': project_name,
            'project_data': [],
            'image_url': image_url,
            'total_cost_sum': 0,
            'preventive_cost_sum': 0,
            'corrective_cost_sum': 0,
            'material_sum': 0,
            'personal_sum': 0,
        }

    return render(request, 'lcc-taetigkeiten2.html', context)
