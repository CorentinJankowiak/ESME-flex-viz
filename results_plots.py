#%%
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np


class rebuilt_es():
    def __init__(self, filepath):
        """
        This class is used to load results from excel formats, and minic the
        behaviour of the esmeflex.core.EnergySystem class.
        """

        self.filepath = filepath
        self.flows_by_w__name = {}
        self.df_patterns = pd.read_excel(
            self.filepath,
            sheet_name = 'df_patterns',
            index_col = 0
        )

        for node in ['elec_gb','h2_gb']:
            self.flows_by_w__name[node] = pd.read_excel(
                self.filepath,
                sheet_name = "flows_by_w__name_" + node,
                index_col = 0
            ).reset_index().fillna(method='ffill', axis=0).set_index(['p','start'])

        self.df_storage_lvl = pd.read_excel(
            self.filepath,
            sheet_name = 'storage_lvl',
            index_col = [0,1]
        ).reset_index().fillna(method='ffill', axis=0).set_index(['p','w'])
    
    def granularise(self, df, granularity):
        df = df.reset_index()
        df['start'] = np.floor(df['start'].values/granularity)*granularity
        df = df.groupby(['p','start']).mean()
        return df

    def build_grouped_df(self, node, granularity, df_grouping):
        
        df = self.flows_by_w__name[node].copy()

        df_gran = self.granularise(df = df, granularity = granularity)

        tech_grouping  = "grouping4"

        grp = df_grouping.set_index("actors")[tech_grouping].to_dict()

        df_gran = df_gran.rename(columns = grp)
        return df_gran.groupby(by=df_gran.columns, axis=1).sum()
    
    def build_full_profile(self, df):
        #stack up all data to recreate the entire profile
        x = pd.DataFrame()
        for order in self.df_patterns['order']:
            p = self.df_patterns.loc[self.df_patterns.order == order, 'name'].values[0]
            reps = self.df_patterns.loc[self.df_patterns.order == order, 'reps'].values[0]
            y = df.loc[(p,),:].copy()
            y = y.reset_index()

            if x.empty:
                y['p'] = p
            else:
                if p in list(x['p']):
                    y['p'] = p + "_2"
                else:
                    y['p'] = p

            z = pd.DataFrame()
            for r in range(reps):   
                y2 = y.copy()
                y2['start'] = y['start'] + len(y['start'])*r
                z = pd.concat([z, y2])
            
            
            x = pd.concat([x, z])

        x = x.set_index(['p','start'])

        return x

def isolate_by_sign(df, sign):
    if sign == 'pos': # return only positive values
        return df.map(lambda v : v if v>=0 else 0)
    elif sign == 'neg': # return only positive values
        return df.map(lambda v : v if v<=0 else 0)
    else:
        print("sign must be either 'pos' or 'neg'.")

def create_col_list(df):
    col_list_default = list(df.columns)
    col_list = []
    for i in ["emand", "nterconnector", "ic_", "uclear", "HINKLEY", "SIZEWELL", 'EV', "Thermal", "ccgt", "CCGT",'iomass','DRAX', "H2", "h2", "ydrogen",  'enewable', 'Wind','PV', 'V2G','storage','Backstop']:
        col_list += list(df.columns[df.columns.str.contains(i)])

    col_list += [x for x in col_list_default if x not in col_list]

    # col_list = list(set(col_list))
    col_list = list(dict.fromkeys(col_list))

    return col_list

def get_color_dict(df, df_grouping):
    coloring = 'coloring4'
    tech_grouping  = "grouping4"

    d = df_grouping[[
        coloring,
        tech_grouping
    ]].drop_duplicates().set_index(tech_grouping).join(
        pd.DataFrame(index = df.columns), how = 'inner'
    )[coloring].to_dict()

    return d

def plot_full_period(es, granularity, df_grouping):
    
    fig = make_subplots(rows = 2, cols=1, shared_xaxes=True)

    for node in ['elec_gb','h2_gb']:
        row = 1 if node=='elec_gb' else 2

        # group and de-granularise before stacking
        df = es.build_grouped_df(node = node, granularity = granularity, df_grouping = df_grouping)

        colors = get_color_dict(df, df_grouping)

        # build full profiled
        df_full = es.build_full_profile(df)

        # add all data to figure
        for sign in ['pos','neg']:
            df = isolate_by_sign(df_full, sign=sign)
            col_list = create_col_list(df)
            for c in col_list:
                if c in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=[df.reset_index()['p'], df.reset_index()['start']],
                            y=df[c],
                            mode='lines',
                            name = c,
                            fill='tonexty',
                            fillcolor = colors[c],
                            line=dict(width=0),
                            stackgroup= sign,
                            connectgaps=True,
                            line_shape='hv'
                        ),
                        row = row, col = 1
                    )
    return fig


def plot_year(year, es, granularity, df_grouping):
    p_list = list(es.df_patterns.loc[es.df_patterns.year == year, 'name'].unique())
    p_count = len(p_list)

    fig = make_subplots(rows = 2, cols=p_count, shared_xaxes=True, shared_yaxes=True)

    for node in ['elec_gb','h2_gb']:
        row = 1 if node=='elec_gb' else 2
        df_grouped = es.build_grouped_df(node = node, granularity = granularity, df_grouping = df_grouping)
        colors = get_color_dict(df_grouped, df_grouping)

        p_idx = 1
        for p in p_list:
            print(p)
            df_season = df_grouped.loc[p]

            for sign in ['pos','neg']:
                df = isolate_by_sign(df_season, sign=sign)
                col_list = create_col_list(df)
                for c in col_list:
                    if c in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df.reset_index()['start'],
                                y=df[c],
                                mode='lines',
                                name = c,
                                fill='tonexty',
                                fillcolor = colors[c],
                                line=dict(width=0),
                                stackgroup= sign,
                                connectgaps=True,
                                line_shape='hv'
                            ),
                            row = row, col = p_idx
                        )
            p_idx+=1
    
    fig.update_layout(showlegend=False)

    return fig

def plot_selectable_year(es, granularity, df_grouping):
    fig = make_subplots(
        cols = 3,
        rows = 3,
        shared_xaxes=True,
        row_heights = [.4, .2, .4],
        horizontal_spacing = 0.05, 
        vertical_spacing=0.05,
        specs = [
            [{'secondary_y': False}, {'secondary_y': False}, {'secondary_y': False}],
            [{'secondary_y': True}, {'secondary_y': True}, {'secondary_y': True}],
            [{'secondary_y': False}, {'secondary_y': False}, {'secondary_y': False}]
]

)

    years = es.df_patterns['year'].unique()

    year_visible = []
    show_lgd_1 = True
    show_lgd_2 = True
    
    for year in years:
        p_list = es.df_patterns.loc[es.df_patterns['year']==year,'name'].unique()
        cols_plotted = []
        for p in p_list:
            print(p)
            if "ummer" in p:
                fig_col=1
            elif "inter" in p:
                fig_col=2
            else:
                fig_col=3

            for node in ['elec_gb','h2_gb']:
                row = 1 if node=='elec_gb' else 3

                df_grouped = es.build_grouped_df(node = node, granularity = granularity, df_grouping = df_grouping)
                colors = get_color_dict(df_grouped, df_grouping)

                df_season = df_grouped.loc[p]

                for sign in ['pos','neg']:
                    df = isolate_by_sign(df_season, sign=sign)
                    col_list = create_col_list(df)

                    for c in col_list:

                        if c in df.columns:
                            if c in cols_plotted:
                                show_lgd = False
                            else:
                                show_lgd = True
                            
                            year_visible.append(year)
                            fig.add_trace(
                                go.Scatter(
                                    x=df.reset_index()['start'],
                                    y=df[c]/1000,
                                    mode='lines',
                                    name = c,
                                    fill='tonexty',
                                    fillcolor = colors[c],
                                    line=dict(width=0),
                                    stackgroup= sign,
                                    connectgaps=True,
                                    line_shape='hv',
                                    showlegend= show_lgd,
                                    legendgroup='group1'
                                ),
                                
                                row = row, col = fig_col
                            )

                            cols_plotted.append(c)
                            cols_plotted = list(set(cols_plotted))

                            

            # adding SOCs
            df_soc = es.df_storage_lvl.loc[p].copy()
            df_soc = df_soc.reset_index(drop = True)
            df_soc = df_soc.iloc[0:168,:]

            for c in df_soc.columns:

                if c in cols_plotted:
                    show_lgd = False
                else:
                    show_lgd = True

                year_visible.append(year)
            
                fig.add_trace(
                    go.Scatter(
                        x=[i for i in range(0, 168)],
                        y=df_soc[c]/1000,
                        mode='lines',
                        name = c,
                        line=dict(width=1),
                        # line_shape='hv',
                        legendgroup='group1',
                        showlegend= show_lgd,
                    ),  
                    
                    secondary_y= True if "h2" in c else False,
                    row = 2, col = fig_col
                )

                cols_plotted.append(c)
                cols_plotted = list(set(cols_plotted))

    fig.update_layout(
        height = 500,
        title='Displaying values per year',
        yaxis_title='Value',
        updatemenus=[
            {
                'buttons': [
                    {'label': str(year), 'method': 'update', 'args': [{'visible': [i == year for i in year_visible]}]}
                    for year in years
                ],
                'direction': 'down',
                'showactive': True,
                'x': 0.17,
                'xanchor': 'left',
                'y': 1.15,
                'yanchor': 'top'
            }
        ],
        legend=dict(
            itemsizing='trace', 
            itemclick=False,  # Disable click interactions
            itemdoubleclick=False  # Disable double-click interactions
            )
        )
    
    return fig







# # Save the graph as an HTML file
# # fig.write_html("interactive_graph.html")

# filepath = r"results/" + "System_Transformation_10.0years_start2005_no_ic_relaxed_" + ".xlsx"
# es = rebuilt_es(filepath)

# node = 'elec_gb'
# granularity = 168
# df_grouping = pd.read_csv("data/tech_maps.csv")
# #%%

# fig_2 = plot_selectable_year(es, 1, df_grouping)

# #%%
# fig_1 = plot_full_period(es, granularity, df_grouping)

#%%
# plot_year(2005, es, 1, df_grouping) 



# %%
