import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load the data
data_path = '/Users/brett/Desktop/Universiteit Hasselt/Semester 2/Visualisation in Data Science/Project/orders.csv'
data = pd.read_csv(data_path)

# Convert 'OrderDate' and 'DeliveryDate' to datetime and extract Year-Month
data['OrderDate'] = pd.to_datetime(data['OrderDate'])
data['DeliveryDate'] = pd.to_datetime(data['DeliveryDate'])
data['Delivery Duration Days'] = (data['DeliveryDate'] - data['OrderDate']).dt.days
data['DeliveryTime'] = data['Delivery Duration Days']  # Assuming DeliveryTime is same as Delivery Duration Days
data['OrderYM'] = data['OrderDate'].dt.to_period('M').dt.strftime('%Y-%m')

# Group data by 'Territory' and 'Duration Category' to count occurrences in each category
bins = [-1, 3, 7, 14, 30, float('inf')]
labels = ['0-3 days', '4-7 days', '8-14 days', '15-30 days', '30+ days']
data['Duration Category'] = pd.cut(data['Delivery Duration Days'], bins=bins, labels=labels)
territory_duration_counts = data.groupby(['Territory', 'Duration Category']).size().reset_index(name='Counts')

# Initialize the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='order-delivery-time-scatter'),
    dcc.Dropdown(
        id='duration-dropdown',
        options=[{'label': label, 'value': label} for label in labels],
        value='0-3 days'
    ),
    dcc.Graph(id='histogram-graph'),
    html.Hr(),
    dcc.Dropdown(id='territory-dropdown'),
    dash_table.DataTable(
        id='product-details-table',
        columns=[{'name': 'Product', 'id': 'Products'}, {'name': 'Quantity', 'id': 'Quantities'}],
        style_table={'height': '300px', 'overflowY': 'auto'}
    ),
    dcc.Graph(id='product-pie-chart')
])

@app.callback(
    Output('order-delivery-time-scatter', 'figure'),
    [Input('duration-dropdown', 'value')]  # This input is not used, kept for simplicity
)
def create_scatter_plot(_):
    fig = px.scatter(data, x='OrderYM', y='DeliveryTime', title='Delivery Time vs. Order Year-Month')
    fig.update_layout(xaxis_tickangle=-90, xaxis_title='Order Year-Month', yaxis_title='Delivery Time')
    return fig

@app.callback(
    Output('histogram-graph', 'figure'),
    [Input('duration-dropdown', 'value')]
)
def update_histogram(selected_duration):
    filtered_data = territory_duration_counts[territory_duration_counts['Duration Category'] == selected_duration]
    fig = px.bar(filtered_data.sort_values('Counts', ascending=False),
                 y='Territory', x='Counts', text='Counts', orientation='h',
                 title=f'Counts of Delivery Durations: {selected_duration}')
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(yaxis_title='Territory', xaxis_title='Count of Deliveries',
                      yaxis={'categoryorder':'total descending', 'autorange': "reversed"},
                      uniformtext_minsize=8, uniformtext_mode='hide', height=max(400, 20 * len(filtered_data)))
    return fig

@app.callback(
    Output('territory-dropdown', 'options'),
    [Input('duration-dropdown', 'value')]
)
def update_territory_options(selected_duration):
    filtered_data = territory_duration_counts[territory_duration_counts['Duration Category'] == selected_duration]
    territories = [{'label': row['Territory'], 'value': row['Territory']} for index, row in filtered_data.sort_values('Counts', ascending=False).iterrows()]
    return territories

@app.callback(
    [Output('product-details-table', 'data'), Output('product-pie-chart', 'figure')],
    [Input('territory-dropdown', 'value'), Input('duration-dropdown', 'value')]
)
def update_table_and_chart(selected_territory, selected_duration):
    if selected_territory:
        territory_data = data[(data['Territory'] == selected_territory) & (data['Duration Category'] == selected_duration)]
        table_data = territory_data[['Products', 'Quantities']].to_dict('records')
        
        product_counts = territory_data.groupby('Products').size().reset_index(name='Counts').sort_values('Counts', ascending=False).head(10)
        if not product_counts.empty:
            fig = px.pie(product_counts, values='Counts', names='Products', title='Top 10 Most Counted Products')
            return table_data, fig
        else:
            return table_data, go.Figure()
    return [], go.Figure() 

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
