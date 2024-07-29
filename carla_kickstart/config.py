import uuid

RENDER_SCALE_FACTOR = 0.7

def get_default_sim_id() -> str:
    try:
        with open("sim_id", "r") as f:
            return f.readline()
    except:
        sim_id = str(uuid.uuid4())
        with open("sim_id", "w") as f:
            f.write(sim_id)
        return sim_id

class Config:

    sim_id = get_default_sim_id()
    target_fps = 30

    render_resolution = (1280*RENDER_SCALE_FACTOR, 720*RENDER_SCALE_FACTOR)
    output_resolution = (1280, 720)
    window_size = (1280 + 320, 720)


config = Config()
available_car_models = ['vehicle.mercedes.coupe_2020', 'vehicle.ford.crown', 'vehicle.mercedes.sprinter', 'vehicle.mini.cooper_s_2021', 'vehicle.nissan.patrol_2021', 'vehicle.volkswagen.t2_2021']