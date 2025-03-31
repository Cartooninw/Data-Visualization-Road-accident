from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd
import plotly.graph_objects as go
# Read in the data
df = pd.read_csv("accident2019_2025.csv", parse_dates=["incident_datetime"])

# --- Precompute summary statistics (overall, unfiltered) ---
total_accidents = len(df)
average_accidents_per_year = df.groupby(df['incident_datetime'].dt.year).size().mean().round(2)
max_accidents_in_a_year = df.groupby(df['incident_datetime'].dt.year).size().max()
min_accidents_in_a_year = df.groupby(df['incident_datetime'].dt.year).size().min()
std_accidents_per_year = df.groupby(df['incident_datetime'].dt.year).size().std().round(2)

# --- Define the app ---
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# --- Layout components ---

# 1. Summary statistics cards (top)
summary_cards = dbc.Row([
    dbc.Col(dbc.Card([
        dbc.CardHeader("Total Accidents"),
        dbc.CardBody(html.H4(f"{total_accidents}", className="card-title"))
    ], className="mb-2"), lg=2),
    dbc.Col(dbc.Card([
        dbc.CardHeader("Avg Accidents/Year"),
        dbc.CardBody(html.H4(f"{average_accidents_per_year}", className="card-title"))
    ], className="mb-2"), lg=2),
    dbc.Col(dbc.Card([
        dbc.CardHeader("Max Accidents in a Year"),
        dbc.CardBody(html.H4(f"{max_accidents_in_a_year}", className="card-title"))
    ], className="mb-2"), lg=2),
    dbc.Col(dbc.Card([
        dbc.CardHeader("Min Accidents in a Year"),
        dbc.CardBody(html.H4(f"{min_accidents_in_a_year}", className="card-title"))
    ], className="mb-2"), lg=2),
    dbc.Col(dbc.Card([
        dbc.CardHeader("Std Dev Accidents/Year"),
        dbc.CardBody(html.H4(f"{std_accidents_per_year}", className="card-title"))
    ], className="mb-2"), lg=2),
], className="mb-3")

# 2. Date range picker
date_picker = dcc.DatePickerRange(
    id='date-range',
    min_date_allowed=df['incident_datetime'].min(),
    max_date_allowed=df['incident_datetime'].max(),
    start_date=df['incident_datetime'].min(),
    end_date=df['incident_datetime'].max(),
    display_format='YYYY-MM-DD'
)

# 3. Individual chart containers (we'll have 10)
# We'll place them in a Grid-like layout: maybe two columns, five rows.
charts_layout = []
for i in range(1, 11):
    charts_layout.append(
        dbc.Col(dcc.Graph(id=f"chart-{i}"), lg=6, className="mb-3")
    )

# Put charts_layout into rows of two charts each
chart_rows = []
for i in range(0, len(charts_layout), 2):
    chart_rows.append(dbc.Row(charts_layout[i:i+2]))

app.layout = dbc.Container([
    html.H1("Accident Dashboard (2019–2025)", className="mt-3 mb-3"),
    summary_cards,
    html.Div([
        html.Label("Select Date Range:"),
        date_picker
    ], className="mb-4"),
    dbc.Container(chart_rows, fluid=True)
], fluid=True)

# --- Callbacks for dynamic updates ---

# def filter_data_by_date(df, start_date, end_date):
#     """Helper to filter the dataframe by selected date range."""
#     mask = (df['incident_datetime'] >= start_date) & (df['incident_datetime'] <= end_date)
#     return df[mask]

@app.callback(
    [Output(f"chart-{i}", "figure") for i in range(1, 11)],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_charts(start_date, end_date):
    # dff = filter_data_by_date(df, start_date, end_date)
    
    # Example 1: Line chart of accidents over time
    # dff_year_line = df["incident_datetime"].dt.strftime("%B").reset_index()
    # dff_year_line = df.groupby(dff_year_line)["number_of_fatalities"].sum()
    # dff_year_line.columns = (["number_of_fatalities","incident_datetime"])
    df['incident_datetime'] = pd.to_datetime(df['incident_datetime'])

    # 2. Create a Month column with full month names
    df['Month'] = df['incident_datetime'].dt.month_name()

    # 3. Group by Month and sum the number_of_fatalities
    df_monthly = df.groupby(['Month','vehicle_type'], as_index=False)['number_of_fatalities'].sum()
    # df_monthly = df.groupby('Month', as_index=False)['number_of_injuries'].sum()
    # 4. Ensure months are in chronological order (Jan, Feb, Mar, ...)
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Convert the Month column to a categorical type with the specified order
    df_monthly['Month'] = pd.Categorical(df_monthly['Month'], 
                                        categories=month_order, 
                                        ordered=True)
    # Sort by this categorical order
    df_monthly.sort_values('Month', inplace=True)

    fig1 = px.line(
        df_monthly, 
        x="Month", 
        y="number_of_fatalities",
        color="vehicle_type",
        labels={"number_of_fatalities": "Number of Fatalities"},
        title="Fatalities By Month  (Line Chart)"
    )
    
    # Example 2: Bar chart of accident counts by year
    dff_year = df.groupby(df['incident_datetime'].dt.strftime("%B")).size().reset_index(name='count')
    dff_year.columns = ["Month", "count"]  # Rename for clarity

# 2. Define the desired month order
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # 3. Convert the Month column to a categorical type with the specified order
    dff_year["Month"] = pd.Categorical(dff_year["Month"], 
                                    categories=month_order, 
                                    ordered=True)

    # 4. Sort by the categorical month column
    dff_year.sort_values("Month", inplace=True)
    fig2 = px.bar(
        dff_year, 
        x="Month", 
        y="count",  
        title="Accidents by Month (Bar Chart)"
    )
    
    # Example 3: Scatter plot (e.g., severity vs. some other measure)
    main_vehicle_types = ["4-wheel pickup truck", "private/passenger car", "motorcycle"]

    df["vehicle_type_simplified"] = df["vehicle_type"].apply(
    lambda vt: vt if vt in main_vehicle_types else "Other"
)

# 3. Optionally, define a custom color map for these categories
    color_map = {
        "4-wheel pickup truck": "blue",
        "private/passenger car": "red",
        "motorcycle": "green",
        "Other": "gray"
    }
    fig3 = px.scatter_mapbox(
        df, 
        lat="latitude",  # Replace with an actual column from your CSV
        lon="longitude",    # Replace with an actual column
        color="vehicle_type_simplified",  # Color by number of injuries
        hover_data=["province_th"],  # Additional info on hover
        zoom=5,
        center={"lat": 15, "lon": 100},  # Center of Thailand
        mapbox_style="open-street-map",
        title="Geographical Scatter Plot",
        color_discrete_map=color_map  
    )
    
    # Example 4: Pie chart by accident category
    # (Assuming there's a column, e.g., 'accident_type')
    dff_type = df['accident_type'].value_counts().reset_index()
    dff_type.columns = ['accident_type', 'number_of_injuries']
    fig4 = px.pie(
        dff_type,
        names="accident_type",
        values="number_of_injuries",  
        title="Accidents by Type (Pie Chart)"
    )

    # Example 5: Histogram of some numeric column (e.g., 'speed')
    df_monthly_stacked = df.groupby(['Month', 'vehicle_type'], as_index=False)['number_of_injuries'].sum().sort_values(by="number_of_injuries",ascending=True)
    df_monthly_stacked['Month'] = pd.Categorical(df_monthly_stacked['Month'],
                                        categories=month_order, 
                                        ordered=True)
    df_monthly_stacked.sort_values('Month', inplace=True)
    # Sorting the stacked ascending
    # vehicle_type_totals = (
    # df_monthly
    # .groupby('vehicle_type')['number_of_injuries'].sum()
    # .sort_values(ascending=True)  # ascending order
    # )


    # vehicle_type_order = vehicle_type_totals.index.tolist()
    fig5 = px.bar(
        df_monthly_stacked, 
        x="Month", 
        y="number_of_injuries",  
        color="vehicle_type",
        # category_orders={"vehicle_type": vehicle_type_order},  
        labels={
            "Month": "Month",
            "number_of_injuries": "Number of Injuries",
            "vehicle_type": "Vehicle Type"
        },
        barmode="stack",
        title="StackBar Chart of Accidents by Month and Vehicle Type"
    )
    

    #snakey diagram
    #There are a ton of case, so this would sort only top 5 for each category
    df_vehicle_ranked = df.groupby('vehicle_type').size().reset_index(name='count')
    df_vehicle_ranked.columns = ['vehicle_type', 'count']
    df_vehicle_ranked.sort_values('count', ascending=False, inplace=True)
    df_vehicle_ranked = df_vehicle_ranked.head(5)
    df_vehicle_ranked = df_vehicle_ranked[df_vehicle_ranked['vehicle_type'] != 'other']

    df_cause_ranked = df.groupby('presumed_cause').size().reset_index(name='count')
    df_cause_ranked.columns = ['presumed_cause', 'count']
    df_cause_ranked.sort_values('count', ascending=False, inplace=True)
    df_cause_ranked = df_cause_ranked.head(5)
    df_cause_ranked = df_cause_ranked[df_cause_ranked['presumed_cause'] != 'other']


    df_accident_ranked = df.groupby('accident_type').size().reset_index(name='count')
    df_accident_ranked.columns = ['accident_type', 'count']
    df_accident_ranked.sort_values('count', ascending=False, inplace=True)
    df_accident_ranked = df_accident_ranked.head(5)
    df_accident_ranked = df_accident_ranked[df_accident_ranked['accident_type'] != 'other']

    df_road_ranked = df.groupby('road_description').size().reset_index(name='count')
    df_road_ranked.columns = ['road_description', 'count']
    df_road_ranked.sort_values('count', ascending=False, inplace=True)
    df_road_ranked = df_road_ranked.head(5)
    df_road_ranked = df_road_ranked[df_road_ranked['road_description'] != 'other']
    # print(df_vehicle_ranked)
    # print(df_cause_ranked)
    # print(df_accident_ranked)
    # print(df_road_ranked)

    df_top_5 = df[df['vehicle_type'].isin(df_vehicle_ranked['vehicle_type']) 
                  &
                    df['presumed_cause'].isin(df_cause_ranked['presumed_cause']) 
                    &
                    df['accident_type'].isin(df_accident_ranked['accident_type']) 
                    &
                    df['road_description'].isin(df_road_ranked['road_description'])]
    # print(df_top_5)
    #Prepare data for Sankey diagram
    df1 = df_top_5.groupby(['vehicle_type', 'presumed_cause'], observed=True).size().reset_index(name='Count1')
    df2 = df_top_5.groupby(['presumed_cause', 'accident_type'], observed=True).size().reset_index(name='Count2')
    df3 = df_top_5.groupby(['accident_type', 'road_description'], observed=True).size().reset_index(name='Count3')
    # print(df2)
    element_count = {"Value":list(df1['Count1']) + list(df2['Count2']) + list(df3['Count3'])}
    df2.to_csv("df2.csv", index=False)
    #Get unique elements for the Sankey diagram
    unique_elements = list(df_top_5["vehicle_type"].unique()) + list(df_top_5["presumed_cause"].unique()) + list(df_top_5["accident_type"].unique()) + list(df_top_5["road_description"].unique())

    label_index = {}

    for index, label in enumerate(unique_elements):
        label_index[label] = index

    element_count['Source'] = list(df1['vehicle_type'].map(label_index)) + list(df2['presumed_cause'].map(label_index)) + list(df3['accident_type'].map(label_index)) 
    element_count['Target'] = list(df1['presumed_cause'].map(label_index)) + list(df2['accident_type'].map(label_index)) + list(df3['road_description'].map(label_index))
    print(len(element_count['Source']))
    print(len(element_count['Target']))
    # print(len(element_count["Source"]) , len(element_count["Target"]), len(element_count["Value"]))
    fig6 = go.Figure(data=[
        go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=unique_elements,
                color="blue"
            ),
            link=dict(
                source=element_count["Source"],
                target=element_count["Target"],
                value=element_count["Value"]
            )
        )
    ])

    fig6.update_layout(title_text="Sankey Diagram of Accident Data Vehicle type/Presumed cause/accident type/Road Type", font_size=10)
    
    # Example 7: Area chart (similar to line but filled)
    # dff_year = df.groupby(df['incident_datetime'].dt.year).size().reset_index(name='frequency')

# Optionally, rename the grouping column for clarity
    # dff_year.rename(columns={'incident_datetime': 'Year'}, inplace=True)

    # Create the area chart using the 'Year' column for the x-axis and 'frequency' for the y-axis
    fig7 = px.parallel_coordinates(
        df,
        color="number_of_vehicles_involved",
        dimensions=["number_of_injuries", "number_of_fatalities"],
        labels={
            "number_of_injuries": "Number of Injuries",
            "number_of_fatalities": "Number of Fatalities",
            "number_of_vehicles_involved": "Number of Vehicles Involved"
        },
        color_continuous_scale=px.colors.sequential.Viridis,
        color_continuous_midpoint=df["number_of_injuries"].mean(),

        title="parallel coordinates plot of accidents",
    )
    # fig7 = px.area(
    #     dff_year,
    #     x="Year",       # Now using the renamed column
    #     y="frequency",
    #     title="Accidents by Year (Area Chart)"
    # )
    # fig7 = px.area(
    #     dff_year,
    #     x="incident_datetime",
    #     y="count",
    #     title="Accidents by Year (Area Chart)"
    # )
    
    # Example 8: A donut chart (just a pie chart with a hole) for another categorization
    # Let's pretend there's a 'severity' column with categories like "Minor", "Major", etc.
    dff_sev = df['vehicle_type'].value_counts().reset_index(name='vehicle_count')
    dff_sev.columns = ['vehicle_type', 'vehicle_count']
    fig8 = px.pie(
        dff_sev,
        names="vehicle_type",
        values="vehicle_count",
        hole=0.4,  # Creates the donut hole
        title="Accidents by vehicle type (Donut Chart)"
    )
    
    # Example 9: Bar chart with a categorical breakdown (stacked or grouped)
    # Let's assume there's a 'weather' column
    dff_weather = df.groupby(['weather_condition', 'Month']).size().reset_index(name='count')
    dff_weather['Month'] = pd.Categorical(dff_weather['Month'],
                                        categories=month_order, 
                                        ordered=True)
    dff_weather.sort_values('Month', inplace=True)
    fig9 = px.bar(
        dff_weather,
        x="Month",
        y="count",
        color="weather_condition",
        barmode="group",
        title="Accidents by month and Weather"
    )
    
    # Example 10: Scatter matrix to explore relationships among numeric columns
    # Pick a few numeric columns relevant to your data
    numeric_cols = ["number_of_injuries", "number_of_fatalities"]  # Adjust as needed
    try:
        fig10 = px.scatter_matrix(
            df[numeric_cols],
            title="Scatter Matrix of Numeric Columns"
        )
    except Exception:
        # If there's an error (e.g. not enough columns or no data in date range),
        # create an empty figure with a title.
        fig10 = px.scatter(title="Not enough data for Scatter Matrix")

    return [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10]

# --- Run the app ---
if __name__ == "__main__":
    app.run(debug=False)
