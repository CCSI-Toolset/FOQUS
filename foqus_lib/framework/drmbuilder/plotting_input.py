# plotting_input.py
class PlottingInput(object):
    """
        The user input data for plotting DRM results including UQ results
    """
    def __init__(self):
        self.input_index_list = list()
        self.output_index_list = list()
        self.bplot_error = True
        self.bplot_step_change = True
        self.bplot_correlation = True

    def to_dictionary(self):
        dict_data = dict()
        dict_data['input_index_list'] = self.input_index_list
        dict_data['output_index_list'] = self.output_index_list
        dict_data['bplot_error'] = self.bplot_error
        dict_data['bplot_step_change'] = self.bplot_step_change
        dict_data['bplot_correlation'] = self.bplot_correlation
        return dict_data

    def from_dictionary(self, dict_data):
        self.input_index_list = dict_data['input_index_list']
        self.output_index_list = dict_data['output_index_list']
        self.bplot_error = dict_data['bplot_error']
        self.bplot_step_change = dict_data['bplot_step_change']
        self.bplot_correlation = dict_data['bplot_correlation']