#%%
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from pathlib import Path
import os
#os.chdir("..")
#root_dir = os.getcwd()
#print(root_dir)
from results_plots import *
#os.chdir("results")

# %%

class App():
    def __init__(self):
        st.set_page_config(layout="wide")
        st.title("ESME-flex results visualiser")

        self.initial_dir = os.getcwd()
        os.chdir("..")
        self.root_dir = os.getcwd()
        os.chdir("results")
        self.res_dir = os.getcwd()
        self.list_files = os.listdir(self.res_dir)
        os.chdir(self.initial_dir)
    
    def launch(self):

        self.select_file_cont = st.container()
    
        with self.select_file_cont:
            self.filepath = st.selectbox(
            "Select a results file among the available options",
            self.list_files,
            )
            st.button(label = "Load data", on_click=self.load_res)
        
        self.full_profile_container = st.container(border = True)
        # self.initiate_button_full()

        self.seasonal_profiles_container = st.container(border = True)
        # self.initiate_button_season()

    # def initiate_button_full(self):
        with self.full_profile_container:
            self.granularity  = st.number_input(label = "Enter time granularity [hour]: ", value = 168, min_value=0, max_value=168)
            st.button(label = 'Update full graph', on_click = self.update_full_profile)       
        
    # def initiate_button_season(self):
        # with self.seasonal_profiles_container:
            # year  = st.number_input(label = "Enter year: ", value = 2005, min_value=2005, max_value=2014, step=1)
            # st.button(label = 'Update seasonal graph', on_click = self.update_season_profile, args=(year,))
    
    def update_full_profile(self):
        if (not hasattr(self, 'es')) or (not hasattr(self, 'df_grouping')):
            self.load_res()

        self.fig_full = plot_full_period(self.es, self.granularity, self.df_grouping)

        with self.full_profile_container:
            st.plotly_chart(self.fig_full)
        
        self.fig_season = plot_selectable_year(self.es, 1, self.df_grouping)

        with self.seasonal_profiles_container:
            st.plotly_chart(self.fig_season)

    def update_season_profile(self, year):
        if (not hasattr(self, 'es')) or (not hasattr(self, 'df_grouping')):
            self.load_res()

        self.fig_season = plot_year(year, self.es, 1, self.df_grouping)

        with self.seasonal_profiles_container:
            st.plotly_chart(self.fig_season)

    def load_res(self):
        self.es = rebuilt_es(Path(self.res_dir, self.filepath))
        self.df_grouping = pd.read_csv(Path(self.root_dir,"data/tech_maps.csv"))


if __name__ == "__main__":
    my_app = App()
    my_app.launch()


# %%
