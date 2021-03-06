import supervisely as sly
import ui.ui as ui

import sly_globals as g


def main():
    data = {}
    state = {}
    data["teamId"] = g.team_id

    g.my_app.compile_template(g.root_source_path)

    ui.init(data, state)

    g.my_app.run(data=data, state=state)

if __name__ == "__main__":
    sly.main_wrapper("main", main)