# this is needed for conversions that need IERS data
import pyodide_http
pyodide_http.patch_all()

from astropy import cosmology
from astropy.cosmology.tests.helper import get_redshift_methods

def get_all_subclasses(cls):
    # https://stackoverflow.com/questions/3862310/how-to-find-all-the-subclasses-of-a-class-given-its-name
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass.__qualname__)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses

def populate_cosmology_class_dropdown(inelem, outelem):
    class_names = get_all_subclasses(cosmology.Cosmology)
    class_names.remove('Cosmology')
    class_names.remove('FLRW')
    class_names.sort()

    select_options = [f'<option value="{nm}">{nm}</option>' for nm in frame_names]
    
    for e in (inelem, outelem):
        e.innerHTML = select_options


def populate_parameters_table(inelem, outelem):
    # From the cosmology

    select_options = cosmo_cls.__parameters__

    for e in (inelem, outelem):
        e.innerHTML = select_options


def populate_method_and_function_dropdown(inelem, outelem):
    """"""

    get_redshift_methods(cosmology, include_private=False, include_z2=True)


hin = Element("incoo")
hout = Element("outputcoo")
hinf = Element("inputframe")
houtf = Element("outputframe")
hbutton = Element("convertbutton")

populate_cosmology_class_dropdown(hinf.element, houtf.element)
hbutton.element.disabled = False

def convert():
    incoo = coordinates.SkyCoord(hin.element.value, 
                                 frame=hinf.element.value)
    toframe = houtf.element.value
    try:
        outcoo = incoo.transform_to(toframe)
    except Exception as e:
        hout.write(f"Failed to convert due to exception: {e}")
    else:
        hout.write(str(outcoo))