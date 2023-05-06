import sys
import gradio as gr
import json
import threading
import subprocess
from pathlib import Path
import time

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
from gradio_app.interacton_with_swarm import *

SWARM_IS_RUNNING = False

def display_logs():
    return read_swarm_logs()

def display_output():
    return read_swarm_output()

def run_the_swarm():
    # Launch the app in the background
    run_swarm()

def swarm_interface(swarm_role, swarm_global_goal, swarm_goals, n_managers, n_analysts, n_googlers):
    global PROC
    # please, don't judge me for this hardcoding. it's 3am and it's the first time i use gradio =)))
    # Call the necessary set_ functions with the user inputs
    set_swarm_role(swarm_role)
    set_swarm_global_goal(swarm_global_goal)
    set_swarm_goals(swarm_goals)
    agents_config = [
        {"type": "manager", "n": n_managers},
        {"type": "analyst", "n": n_analysts},
        {"type": "googler", "n": n_googlers}
    ]
    set_swarm_agents_config(agents_config)

    t = threading.Thread(target=run_the_swarm)
    t.start()
    print("Swarm is running")
    SWARM_IS_RUNNING = True

def create_gradio_interface():
    title = """
    <h1 align="center">🐝🐝 Swarm Intelligence 🐝🐝</h1>
    <div align="center">
    <a style="display:inline-block" href='https://github.com/nicelir1996/GPT-Swarm'><img src='https://img.shields.io/github/stars/nicelir1996/GPT-Swarm?style=social' /></a>
    <a href="https://huggingface.co/spaces/swarm-agents/swarm-agents?duplicate=true"><img src="https://bit.ly/3gLdBN6" alt="Duplicate Space"></a>
    </div>
    """

    #display message for themes feature
    theme_addon_msg = """
    The swarm of agents combines a huge number of parallel agents divided into roles, including (for now) managers, analytics, and googlers. 
    The agents all interact with each other through the shared memory and the task queue.
    """

    #Modifying existing Gradio Theme
    theme = gr.themes.Soft(primary_hue="zinc", secondary_hue="green", neutral_hue="green",
                        text_size=gr.themes.sizes.text_lg)       
    
    with gr.Blocks() as demo:
        # Create a container on the left for the inputs
        gr.HTML(title)
        gr.HTML(theme_addon_msg)

        # layout
        with gr.Row():
            with gr.Column(variant="panel", scale=0.4):
                submit = gr.Button(value="Start the Swarm 🚀")
                with gr.Accordion(label="Swarm goals (can leave empty for default)", open=False):
                    # Create a textbox for swarm role
                    swarm_role = gr.Textbox(placeholder=get_swarm_role(), label="Swarm role")
                    # Create a textbox for swarm global goal
                    swarm_global_goal = gr.Textbox(placeholder=get_swarm_global_goal(), label="Swarm global goal")
                    # Create a list for swarm goals
                    swarm_goals = gr.List(headers=None, col_count=(1, "fixed"), max_cols=1)
                with gr.Accordion(label="Agents Setup:", open=False):
                    # Create a textbox for number of manager agents
                    n_managers = gr.Textbox(placeholder=get_swarm_agents_config()[0]["n"], label="Number of manager agents")
                    # Create a textbox for number of analyst agents
                    n_analysts = gr.Textbox(placeholder=get_swarm_agents_config()[1]["n"], label="Number of analyst agents")
                    # Create a textbox for number of googler agents
                    n_googlers = gr.Textbox(placeholder=get_swarm_agents_config()[2]["n"], label="Number of googler agents")
                    # create a submit button

            # Create a container on the right for the outputs
            with gr.Column(variant="panel", scale=0.6):
                    # Create a textbox for output
                    output_textbox = gr.Textbox(label="Output", lines=20)
                    # Create a textbox for logs
                    logs_textbox = gr.Textbox(label="Logs", lines=8)
                    update_view_button = gr.Button(value="Update Results Display 🔄")
                    gr.HTML("""<center><p>(If someone knows how to update dynamically, please save us, that's emberrasing 😳)</p></center>""")

        #Event handling
        def update_view_callback():
            return display_logs(), display_output()
        
        def submit_callback(swarm_role, swarm_global_goal, swarm_goals, n_managers, n_analysts, n_googlers):
            if not SWARM_IS_RUNNING:
                swarm_interface(swarm_role, swarm_global_goal, swarm_goals, n_managers, n_analysts, n_googlers)
            return display_logs(), display_output()
        
        submit.click(submit_callback, inputs=[swarm_role, swarm_global_goal, swarm_goals, n_managers, n_analysts, n_googlers], outputs=[logs_textbox, output_textbox])
        update_view_button.click(update_view_callback, outputs=[logs_textbox, output_textbox])

    return demo