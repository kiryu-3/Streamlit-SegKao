class ShapeManager:
    def __init__(self, map_manager):
        self.map_manager = map_manager

    def handle_draw_data(self, draw_data):
        self.map_manager.add_draw_data(draw_data)

    def select_shape(self, shape_id):
        self.map_manager.select_shape(shape_id)

    def delete_shape(self, shape_id):
        self.map_manager.delete_shape(shape_id)
