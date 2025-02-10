import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

# Page configuration with a modern theme
st.set_page_config(
    page_title="US Population Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stDataFrame {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Enable dark theme for Altair
#alt.themes.enable("dark")

# Updated
alt.theme.enable('quartz')

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('us-population-2020-2024-reshaped.csv')

df_reshaped = load_data()

# Sidebar with enhanced styling
with st.sidebar:
    st.title('📊 Population Analytics')
    st.markdown('---')
    
    year_list = list(df_reshaped.year.unique())[::-1]
    
    selected_year = st.selectbox('📅 Select Year', year_list, index=len(year_list)-1)
    df_selected_year = df_reshaped[df_reshaped.year == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="population", ascending=False)

    st.markdown('---')
    st.markdown('### 🎨 Visualization Settings')
    color_theme_list = [
        'viridis', 'plasma', 'inferno', 'magma', 
        'Spectral', 'RdYlBu', 'RdBu', 'PuOr', 
        'BrBG', 'PRGn'
    ]
    selected_color_theme = st.selectbox('Color Theme', color_theme_list)

# Custom functions with enhanced visuals
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O', 
                axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, 
                             titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', 
                axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, 
                             titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q',
                       legend=None,
                       scale=alt.Scale(scheme=input_color_theme)),
        tooltip=[
            alt.Tooltip(f'{input_x}:O', title='State'),
            alt.Tooltip(f'{input_y}:O', title='Year'),
            alt.Tooltip(f'max({input_color}):Q', title='Population', format=',')
        ]
    ).properties(
        width=900
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )
    return heatmap

def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(
        input_df, 
        locations=input_id, 
        color=input_column,
        locationmode="USA-states",
        color_continuous_scale=input_color_theme,
        range_color=(0, max(df_selected_year.population)),
        scope="usa",
        labels={'population':'Population'}
    )
    choropleth.update_layout(
        template='plotly',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350,
        geo=dict(
            showlakes=True,
            lakecolor='lightblue',  # Changed lake color for better visibility on white
            bgcolor='white',  # Added explicit white background
            landcolor='white',  # Added explicit white land color
            subunitcolor='gray',  # Changed state border color for better visibility
            subunitwidth=1  # Added explicit border width
        )
    )
    return choropleth

def make_donut(input_response, input_text, input_color):
    color_schemes = {
        'blue': ['#4361EE', '#3F37C9'],
        'green': ['#4CAF50', '#388E3C'],
        'orange': ['#FF9800', '#F57C00'],
        'red': ['#F44336', '#D32F2F']
    }
    chart_color = color_schemes.get(input_color, ['#29b5e8', '#155F7A'])
    
    source = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100-input_response, input_response]
    })
    
    plot = alt.Chart(source).mark_arc(
        innerRadius=45, 
        cornerRadius=25,
        stroke="#fff",
        strokeWidth=1
    ).encode(
        theta="% value",
        color=alt.Color(
            "Topic:N",
            scale=alt.Scale(domain=[input_text, ''], range=chart_color),
            legend=None
        ),
        tooltip=["Topic", "% value"]
    ).properties(width=130, height=130)
    
    text = plot.mark_text(
        align='center',
        color="#ffffff",
        font="Inter",
        fontSize=32,
        fontWeight=700
    ).encode(text=alt.value(f'{input_response}%'))
    
    return plot + text

def calculate_population_difference(input_df, input_year):
    selected_year_data = input_df[input_df['year'] == input_year].reset_index()
    previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
    selected_year_data['population_difference'] = selected_year_data.population.sub(
        previous_year_data.population, fill_value=0
    )
    return pd.concat([
        selected_year_data.states, 
        selected_year_data.id, 
        selected_year_data.population, 
        selected_year_data.population_difference
    ], axis=1).sort_values(by="population_difference", ascending=False)

def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000}M'
        return f'{round(num / 1000000, 1)}M'
    return f'{num // 1000}K'

# Layout
col = st.columns((1.5, 4.5, 2), gap='medium')

# Column 1: Migration Stats
with col[0]:
    st.markdown('### 📈 Population Changes')
    
    df_population_difference_sorted = calculate_population_difference(df_reshaped, selected_year)
    
    if selected_year > 2010:
        first_state = df_population_difference_sorted.iloc[0]
        last_state = df_population_difference_sorted.iloc[-1]
        
        st.metric(
            label=f"📈 {first_state.states}",
            value=format_number(first_state.population),
            delta=format_number(first_state.population_difference)
        )
        
        st.metric(
            label=f"📉 {last_state.states}",
            value=format_number(last_state.population),
            delta=format_number(last_state.population_difference)
        )
    else:
        st.metric(label="-", value="-")
        st.metric(label="-", value="-")
    
    st.markdown('### 🔄 Migration Patterns')
    
    if selected_year > 2010:
        df_inbound = df_population_difference_sorted[
            df_population_difference_sorted.population_difference > 50000
        ]
        df_outbound = df_population_difference_sorted[
            df_population_difference_sorted.population_difference < -50000
        ]
        
        states_count = df_population_difference_sorted.states.nunique()
        inbound_pct = round((len(df_inbound)/states_count)*100)
        outbound_pct = round((len(df_outbound)/states_count)*100)
    else:
        inbound_pct = outbound_pct = 0
    
    cols = st.columns(2)
    with cols[0]:
        st.markdown("#### Inbound")
        st.altair_chart(make_donut(inbound_pct, 'Inbound', 'green'))
    with cols[1]:
        st.markdown("#### Outbound")
        st.altair_chart(make_donut(outbound_pct, 'Outbound', 'red'))

# Column 2: Maps and Heatmap
with col[1]:
    st.markdown('### 🗺️ Geographic Distribution')
    
    choropleth = make_choropleth(
        df_selected_year, 'states_code', 'population', selected_color_theme
    )
    st.plotly_chart(choropleth, use_container_width=True)
    
    st.markdown('### 📊 Population Trends')
    heatmap = make_heatmap(
        df_reshaped, 'year', 'states', 'population', selected_color_theme
    )
    st.altair_chart(heatmap, use_container_width=True)

# Column 3: Rankings and Info
with col[2]:
    st.markdown('### 🏆 State Rankings')
    
    st.dataframe(
        df_selected_year_sorted,
        column_order=("states", "population"),
        hide_index=True,
        column_config={
            "states": st.column_config.TextColumn("States"),
            "population": st.column_config.ProgressColumn(
                "Population",
                format="%f",
                min_value=0,
                max_value=max(df_selected_year_sorted.population),
            )
        }
    )
    
    with st.expander('ℹ️ About', expanded=True):
        st.markdown("""
        #### Data Source
        - U.S. Census Bureau population estimates (2020-2024)
        
        #### Metrics Explained
        - **Population Changes**: Shows states with highest inbound/outbound migration
        - **Migration Patterns**: % of states with migration >50,000 people
        - **Geographic Distribution**: Population density across states
        - **Population Trends**: Year-over-year population changes
        """)