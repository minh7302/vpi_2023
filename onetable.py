import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.subplots as sp
import pandas as pd
import requests
import pyautogui
width, height = pyautogui.size()

app = dash.Dash()
well_id = requests.get("http://127.0.0.1:8000/api/cal_curve_value/well_id/unique")
well_id = well_id.json()

app.layout = html.Div([
    dcc.Dropdown(id='well_id', options=[{'label': i, 'value': i} for i in well_id], value=well_id[0]),

    dcc.Checklist(
        id='my-checkboxes',
        ),

    html.Div(id = 'graph')
])

# Đọc dữ liệu từ API và trả về dạng dataframe
def read_data(well_id):
    df = requests.get("http://127.0.0.1:8000/api/get_data/cal_curve_value/well_id/" + well_id)
    df = df.json()
    df = pd.DataFrame(df)
    df = df.pivot(index='md', columns='curve_id', values='cal_value')
    return df

@app.callback(
    Output('graph', 'children'),
    [Input('well_id', 'value'),
     Input('my-checkboxes', 'value')]
)
def update_graph(well_id, value):
    df = read_data(well_id)
    num_columns = int(width/400)
    
    # nếu value là None thì in ra please select a curve
    if value is None:
        fig = go.Figure()
        fig.update_layout(title='Please select a curve')
        return dcc.Graph(figure=fig)
    else:
        if 'all' in value:
            value = df.columns.tolist()
        
        n_rows = int(len(value) / num_columns) + 1
        fig = sp.make_subplots(rows=n_rows, cols=num_columns, shared_yaxes='all', horizontal_spacing=0.1)
        row = 1
        col = 1
        for i in value:
            if col > num_columns:
                col = 1
                row += 1
            fig.add_trace(go.Scatter(x=df[i], y=df.index, name=f'{i}', mode='lines'),
                                row=row, col=col)
            fig.update_xaxes(title = f'{i}', row=row, col=col, autorange=True)
            col += 1
        fig.update_yaxes(autorange="reversed", showticklabels=True)
        fig.update_layout(height=n_rows*400 + 10)
        return dcc.Graph(figure=fig)


# tạo 1 callback có giá trị trả về là 1 list các options

@app.callback(
    Output('my-checkboxes', 'options'),
    [Input('well_id', 'value')]
)
def update_checklist_options(well_id):
    df = requests.get("http://127.0.0.1:8000/api/get_data/cal_curve_value/well_id/" + well_id)
    df = df.json()
    df = pd.DataFrame(df)
    curve_id = df['curve_id'].unique()
    
    # Thêm option all
    options = [{'label': 'ALL', 'value': 'all'}]
    options += [{'label': i, 'value': i} for i in curve_id]
    
    return options

@app.callback(
    Output('my-checkboxes', 'value'),
    [Input('my-checkboxes', 'options'),
     Input('my-checkboxes', 'value')],
    [State('my-checkboxes', 'value')]
)
def update_checklist_value(options, value, prev_value):
    if 'all' in prev_value: # if all was selected, return all
        if value[-1] == 'all':
            return ['all']
        else: # if all was selected, but then unselected, return all but the unselected value
            return [v for v in value if v != 'all']
    else:
        if 'all' in value:  # if all was selected, return all
            return ['all']
        elif set(value) == set([o['value'] for o in options]) - {'all'}:
            return ['all']
        else:
            return value
    
if __name__ == '__main__':
    app.run_server()
