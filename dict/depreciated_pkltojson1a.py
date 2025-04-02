import pickle, json

with open('./svg_dict.pkl', 'rb') as f:
    svg_dict = pickle.load(f)
with open('./comp_dict.pkl', 'rb') as f:
    comp_dict = pickle.load(f)
with open('./def_dict.pkl', 'rb') as f:
    def_dict = pickle.load(f)

with open('./svg_dict.json', 'w') as f:
    json.dump(svg_dict, f)
with open('./comp_dict.json', 'w') as f:
    json.dump(comp_dict, f)
with open('./def_dict.json', 'w') as f:
    json.dump(def_dict, f)
