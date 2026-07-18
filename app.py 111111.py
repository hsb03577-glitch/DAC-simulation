import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import numpy as np

app = dash.Dash(__name__)
server = app.server

# 이동 중인 입자들 (최대 500개)
moving_x = np.random.uniform(-1, 5, 500)
moving_y = np.random.uniform(-1, 1, 500)
moving_z = np.random.uniform(-1, 1, 500)

# 필터에 포집된 입자들
captured_x, captured_y, captured_z = [], [], []
history_count = [0] * 50

app.layout = html.Div([
    html.H1("DAC 실시간 물리 시뮬레이터"),
    html.Div([
        html.Button('시작 / 멈춤', id='btn-play-pause', n_clicks=0, style={'fontSize': '16px', 'backgroundColor': '#28a745', 'color': 'white'}),
        html.Button('초기화', id='btn-reset', n_clicks=0, style={'fontSize': '16px', 'backgroundColor': '#dc3545', 'color': 'white', 'marginLeft': '10px'}),
        html.Label(" 농도 (ppm):"), dcc.Slider(id='co2-slider', min=400, max=2000, value=600),
        html.Label(" 온도 (°C):"), dcc.Slider(id='temp-slider', min=0, max=50, value=25),
        html.Label(" 압력 (atm):"), dcc.Slider(id='press-slider', min=0.5, max=2.0, step=0.1, value=1.0),
        html.Label(" 입자 속도:"), dcc.Slider(id='speed-slider', min=0.05, max=0.5, step=0.05, value=0.15),
    ], style={'width': '30%', 'padding': '10px'}),
    
    html.Div([
        dcc.Graph(id='main-graph', style={'width': '60%', 'display': 'inline-block'}),
        dcc.Graph(id='history-graph', style={'width': '40%', 'display': 'inline-block'})
    ]),
    dcc.Interval(id='interval-component', interval=100, n_intervals=0, disabled=True)
])

@app.callback(
    [Output('main-graph', 'figure'), Output('history-graph', 'figure')],
    [Input('interval-component', 'n_intervals'), Input('btn-reset', 'n_clicks')],
    [State('co2-slider', 'value'), State('temp-slider', 'value'), 
     State('press-slider', 'value'), State('speed-slider', 'value')]
)
def update_simulation(n, reset_clicks, co2, temp, press, speed):
    global moving_x, moving_y, moving_z, captured_x, captured_y, captured_z, history_count
    
    ctx = dash.callback_context
    if ctx.triggered and 'btn-reset' in ctx.triggered[0]['prop_id']:
        captured_x, captured_y, captured_z = [], [], []
        moving_x = np.random.uniform(-1, 5, 500)
        history_count = [0] * 50
    
    num_particles = int((co2 / 600) * 100)
    prob = (0.15 * (1.0 - temp/50.0) * (1.0 - (press-0.5)/1.5)) + 0.02
    
    for i in range(num_particles):
        moving_x[i] += speed * np.random.uniform(0.5, 1.5)
        
        if 5 <= moving_x[i] < 5 + speed and np.random.rand() < prob:
            captured_x.append(5)
            captured_y.append(moving_y[i])
            captured_z.append(moving_z[i])
            moving_x[i] = -0.5
        elif moving_x[i] > 6:
            moving_x[i] = -0.5
            
    # 통계 기록
    history_count.append(len(captured_x))
    if len(history_count) > 50: history_count.pop(0)
    
    # 그래프 시각화
    fig = go.Figure()
    fig.add_trace(go.Mesh3d(x=[5,5,5,5], y=[-1.5,1.5,1.5,-1.5], z=[-1.5,-1.5,1.5,1.5], opacity=0.1, color='gray'))
    fig.add_trace(go.Scatter3d(x=moving_x[:num_particles], y=moving_y[:num_particles], z=moving_z[:num_particles], mode='markers', marker=dict(size=2, color='orange')))
    fig.add_trace(go.Scatter3d(x=captured_x, y=captured_y, z=captured_z, mode='markers', marker=dict(size=2, color='green')))
    
    fig.update_layout(scene=dict(xaxis=dict(range=[-1, 7], autorange=False), yaxis=dict(range=[-2, 2], autorange=False), zaxis=dict(range=[-2, 2], autorange=False), camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))), uirevision='constant', margin=dict(l=0, r=0, b=0, t=0), showlegend=False)
    
    # 상승 구간 빨간색 강조
    line_colors = ['red' if history_count[i] > history_count[i-1] else 'green' for i in range(1, len(history_count))]
    fig_hist = go.Figure()
    for i in range(len(line_colors)):
        fig_hist.add_trace(go.Scatter(x=[i, i+1], y=[history_count[i], history_count[i+1]], mode='lines', line=dict(color=line_colors[i])))
        
    fig_hist.update_layout(title="누적 포집 개수", xaxis_title="시간", yaxis_title="개수", margin=dict(t=40), showlegend=False)
    
    return fig, fig_hist

@app.callback(Output('interval-component', 'disabled'), Input('btn-play-pause', 'n_clicks'), State('interval-component', 'disabled'))
def toggle(n, d): return not d

if __name__ == '__main__':
    app.run(debug=True)
