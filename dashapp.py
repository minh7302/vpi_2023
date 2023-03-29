import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.subplots as sp
import pandas as pd
import requests
import pyautogui
from scipy import stats
import numpy as np
from flask import Flask
from flask_cors import CORS

server = Flask(__name__)
CORS(server)
width, height = pyautogui.size()

# Khởi tạo ứng dụng Dash
app = dash.Dash(__name__, server=server)

well_id = requests.get("http://127.0.0.1:8000/api/cal_curve_value/well_id/unique")
well_id = well_id.json()

# Layout cho trang thứ nhất
layout1 = html.Div([
    dcc.Input(id='well_id', value=well_id[0]),

    dcc.Checklist(
        id='my-checkboxes',
        ),

    html.Div(id = 'graph')
])

# Layout cho trang thứ hai
layout2 = html.Div([
    dcc.Dropdown(id='well_id1', options=[{'label': i, 'value': i} for i in well_id], value=well_id[0], multi=True),

    dcc.RadioItems(
        id='my-radioitems',
        options=[],
        value=''
        ),

    html.Div(id='graph1')
])


# ------------------------------------------------------------------Layout 1------------------------------------------------------------------#
# Callback cho trang thứ nhất
@app.callback(
    Output('graph', 'children'),
    [Input('well_id', 'value'),
     Input('my-checkboxes', 'value')]
)
def update_graph(well_id, value):
    columns = requests.get("http://127.0.0.1:8000/api/unique_curve_ids/" + well_id)
    columns = columns.json()
    num_columns = int(width/400)
    
    # nếu value là một mảng rỗng
    if len(value) == 0:
        fig = go.Figure()
        fig.update_layout(title='Please select a curve')
        return dcc.Graph(figure=fig)
    else:
        if 'all' in value:
            value = columns
        
        n_rows = int(len(value) / num_columns) + 1
        fig = sp.make_subplots(rows=n_rows, cols=num_columns, shared_yaxes='all', horizontal_spacing=0.1)
        row = 1
        col = 1
        for i in value:
            data = requests.get("http://127.0.0.1:8000/api/get_data/cal_curve_value/well_id/" + well_id + "/" + i)
            data = data.json()
            # chuyển sang thành 2 list với x = md, y = cal_value
            x = [i['cal_value'] for i in data]
            y = [i['md'] for i in data]
            if col > num_columns:
                col = 1
                row += 1
            fig.add_trace(go.Scatter(x=x, y=y, name=f'{i}', mode='lines'),
                                row=row, col=col)
            fig.update_xaxes(title = f'{i}', row=row, col=col, autorange=True)
            col += 1
        fig.update_yaxes(autorange="reversed", showticklabels=True)
        fig.update_layout(height=n_rows*400 + 10)
        return dcc.Graph(figure=fig)


# tạo 1 callback có giá trị trả về là 1 list các options
@app.callback(
    Output('my-checkboxes', 'options'),
    [Input('well_id', 'value')],
)
def update_checklist_options(well_id):
    curve_id = requests.get("http://127.0.0.1:8000/api/unique_curve_ids/" + well_id)
    curve_id = curve_id.json()
    
    # Thêm option all
    options = [{'label': 'ALL', 'value': 'all'}]
    options += [{'label': i, 'value': i} for i in curve_id]
    
    return options

@app.callback(
    Output('my-checkboxes', 'value'),
    [Input('my-checkboxes', 'options'),
     Input('my-checkboxes', 'value')],
    [State('my-checkboxes', 'value')],
)
def update_checklist_value(options, value, prev_value):
    if value is not None:
        value = [v for v in value if v in [o['value'] for o in options]]
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
    return []



# -----------------------------------------------------------Layout 2------------------------------------------------------------#
@app.callback(
    Output('my-radioitems', 'options'),
    [Input('well_id1', 'value')]
)
def update_radioitems_options(well_id):
    # nếu well_id là 1 giá trị thì đọc dữ liệu từ API và lấy các giá trị unique của curve_id
    if isinstance(well_id, str):
        curve_id = requests.get("http://127.0.0.1:8000/api/unique_curve_ids/" + well_id)
        curve_id = curve_id.json()
    # nếu well_id là 1 list thì đọc dữ liệu từ API và lấy các giá trị unique của curve_id
    elif isinstance(well_id, list):
        # df_list là tên tất các các giá trị unique của curve_id trong well_id
        df_list = [requests.get("http://127.0.0.1:8000/api/unique_curve_ids/" + wid).json() for wid in well_id]
        if not df_list:
            return []
        # lấy tên các cột chung của tất cả các dataframe
        common_columns = set(df_list[0])
        for df in df_list[1:]:
            common_columns = common_columns.intersection(df)
        # chuyển common_columns thành list nếu nó không rỗng
        if common_columns:
            curve_id = list(common_columns)
        else:
            return []
    # nếu well_id là None thì trả về 1 list rỗng
    else:
        return []
    return [{'label': i, 'value': i} for i in curve_id]

# tạo ra updata_radioitems_value chỉ cho chọn duy nhất 1 giá trị
@app.callback(
    Output('my-radioitems', 'value'),
    [Input('my-radioitems', 'options')]
)
def update_radioitems_value(options):
    if options:
        return options[0]['value']
    else:
        return None

@app.callback(
    Output('graph1', 'children'),
    [Input('well_id1', 'value'), Input('my-radioitems', 'value')]
)
def update_graph(well_id, curve_id):
    fig = go.Figure()

    if not well_id:
        fig.update_layout(title='Please select well')
        return dcc.Graph(figure=fig)
    elif not curve_id:
        fig.update_layout(title='No curve selected')
        return dcc.Graph(figure=fig)
    else:

        if isinstance(well_id, str):
            curve = requests.get("http://127.0.0.1:8000/api/unique_curve_ids/" + well_id)
            curve = curve.json()
            if curve_id not in curve:
                fig.update_layout(title=f'Curve "{curve_id}" not found in data for well "{well_id}"')
                return fig
            
            data = requests.get("http://127.0.0.1:8000/api/get_data/cal_curve_value/well_id/" + well_id + "/" + curve_id)
            data = data.json()
            # chuyển sang thành 2 list với x = md, y = cal_value
            x = [i['cal_value'] for i in data]
            x = [i for i in x if isinstance(i, (int, float))]
            kde = stats.gaussian_kde(x)
            x_range = np.linspace(min(x), max(x), 100)
            y_range = kde(x_range)

            fig.add_trace(
                    go.Scatter(x=x_range, 
                    y=y_range, 
                    mode='lines',
                    line=dict(width=1.5),
                    name='Normal',
                )
            )

        elif isinstance(well_id, list):
            for i in well_id:
                curve = requests.get("http://127.0.0.1:8000/api/unique_curve_ids/" + i)
                curve = curve.json()
                if curve_id not in curve:
                    fig.update_layout(title=f'Curve "{curve_id}" not found in data for well "{i}"')
                    return fig
                data = requests.get("http://127.0.0.1:8000/api/get_data/cal_curve_value/well_id/" + i + "/" + curve_id)
                data = data.json()

                x = [i['cal_value'] for i in data]
                x = [i for i in x if isinstance(i, (int, float))]

                kde = stats.gaussian_kde(x)
                x_range = np.linspace(min(x), max(x), 100)
                y_range = kde(x_range)

                fig.add_trace(
                        go.Scatter(x=x_range, 
                        y=y_range, 
                        mode='lines',
                        line=dict(width=1.5),
                        name='{0}'.format(i),
                    )
                )
    
    return dcc.Graph(figure=fig),



#-------------------------------------------------------- Tạo tab --------------------------------------------------------#
# Thêm các tab vào ứng dụng Dash
app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab1', children=[
        dcc.Tab(label='Log', value='tab1', children=[]),
        dcc.Tab(label='Histogram', value='tab2', children=[])
    ]),
    html.Div(id='tab-output')
])

# Callback để hiển thị nội dung của tab được chọn
@app.callback(Output('tab-output', 'children'),
            Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab1':
        return layout1
    elif tab == 'tab2':
        return layout2

# Chạy ứng dụng Dash
if __name__ == '__main__':
    app.run_server()
