import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import numpy as np
import plotly.graph_objs as go
import plotly.subplots as sp
import pandas as pd
import requests
import pyautogui
from scipy import stats

width, height = pyautogui.size()

app = dash.Dash()
well_id = requests.get("http://127.0.0.1:8000/api/cal_curve_value/well_id/unique")
well_id = well_id.json()

app.layout = html.Div([
    dcc.Dropdown(id='well_id', options=[{'label': i, 'value': i} for i in well_id], value=well_id[0], multi=True),

    dcc.RadioItems(
        id='my-radioitems',
        options=[],
        value=''
        ),

    html.Div(id='graph')
])

# Đọc dữ liệu từ API và trả về dạng dataframe
def read_data(well_id):
    df = requests.get("http://127.0.0.1:8000/api/get_data/cal_curve_value/well_id/" + well_id)
    df = df.json()
    df = pd.DataFrame(df)
    df = df.pivot(index='md', columns='curve_id', values='cal_value')
    return df

@app.callback(
    Output('my-radioitems', 'options'),
    [Input('well_id', 'value')]
)
def update_radioitems_options(well_id):
    # nếu well_id là 1 giá trị thì đọc dữ liệu từ API và lấy các giá trị unique của curve_id
    if isinstance(well_id, str):
        df = read_data(well_id)
        curve_id = df.columns.tolist()
    # nếu well_id là 1 list thì đọc dữ liệu từ API và lấy các giá trị unique của curve_id
    elif isinstance(well_id, list):
        df_list = [read_data(wid) for wid in well_id]
        if not df_list:
            return []
        # lấy tên các cột chung của tất cả các dataframe
        common_columns = set(df_list[0].columns.tolist())
        for df in df_list[1:]:
            common_columns = common_columns.intersection(df.columns.tolist())
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
    Output('graph', 'children'),
    [Input('well_id', 'value'), Input('my-radioitems', 'value')]
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
                df = read_data(well_id)
                if curve_id not in df.columns:
                    fig.update_layout(title=f'Curve "{curve_id}" not found in data for well "{well_id}"')
                    return fig
                df = df[[curve_id]]
                df = df.reset_index()

                x = df[curve_id]
                x = x[np.isfinite(x)] # Loại bỏ các giá trị không phải số
                kde = stats.gaussian_kde(x)
                x_range = np.linspace(x.min(), x.max(), 100)
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
                df = read_data(i)
                if curve_id not in df.columns:
                    fig.update_layout(title=f'Curve "{curve_id}" not found in data for well "{i}"')
                    return fig
                df = df[[curve_id]]
                df = df.reset_index()

                x = df[curve_id]
                x = x[np.isfinite(x)] # Loại bỏ các giá trị không phải số
                kde = stats.gaussian_kde(x)
                x_range = np.linspace(x.min(), x.max(), 100)
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

if __name__ == '__main__':
    app.run_server(debug=True)
